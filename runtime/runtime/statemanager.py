from collections import UserDict
import enum

import abc
import asyncio
import os
import threading
import uuid
import pickle

from cobs import cobs
from runtime.buffer import SharedMemoryBuffer, BinaryRingBuffer
from runtime.util import read_conf_file


class SharedStore(UserDict, abc.ABC):
    """
    Base class for a shared key-value store.

    The underlying implementation uses UNIX sockets configured in a primary-
    replica arrangement to facilitate interprocess communication. The primary
    process should run a ``SharedStoreServer`` that holds an authoritative copy
    of the data. ``SharedStoreClient``s can broadcast mutations to (set or
    delete keys) or request missing keys from the server::

                   +--------+
             +---->| Server |<----+
             |     +--------+     |
             V                    V
        +----------+         +----------+
        | Client 1 |   ...   | Client N |
        +----------+         +----------+

    A background thread watches for changes from the other end of each
    connection. Due to the unpredictability of thread scheduling, accesses to
    the store may arrive in any order. For example, a replica may use a key
    after it was deleted by another replica, but before the update propogated
    through the server.

    Updates (including keys and values) are serialized using the ``pickle``
    module, then encoded using COBS to delimit packets with null bytes. This
    store should not be used for high-throughput applications; consider using
    shared memory instead. Shared store objects support the context management
    protocol for automatic resource cleanup.

    Attributes:
        addr: The UNIX socket address this object should serve or connect to.
        data: The initial data used to populate this store.
        name: The background thread name.
    """
    class Command(enum.Flag):
        """
        Command types. Every message starts with a command type and the key
        operated on. Messages follow one of these formats:
            * `(GET, <key>)`: Requests a key from the server. The server should
              send back at most one `SET`, and exactly one `ACK`.
            * `(ACK, <key>, <found>)`: Acknowledgement from server to client.
            * `(ACK,)`: The server is ready to broadcast messages.
            * `(SET, <key>, <value>)`: Key set by sender. Duplex.
            * `(DEL, <key>)`: Key deleted by sender. Duplex.
        """
        GET = enum.auto()
        ACK = enum.auto()
        SET = enum.auto()
        DEL = enum.auto()
        MUTATE = SET | DEL
    delimeter = b'\x00'
    cleanup_timeout = 10

    def __init__(self, addr: str, data: dict = None, name: str = None):
        self.addr, self.name = addr, name
        self.loop_ready, self.watchers = threading.Event(), {}
        self.loop = asyncio.new_event_loop()
        super().__init__(data or {})

    def __del__(self):
        self.loop.close()

    def start(self):
        self.thread = threading.Thread(name=self.name, daemon=True,
                                       target=self.bootstrap_thread)
        self.thread.start()

    @abc.abstractmethod
    async def main(self):
        """ The main task. """

    def bootstrap_thread(self):
        """
        Bootstrap the background thread by adding the main task to a new event loop.

        Create a new event loop. When the root task is cancelled by calling
        ``stop``, all tasks are cancelled but allowed to finish by cleaning up
        open resources. Tasks should not block ``asyncio.CancelledError``.
        """
        try:
            asyncio.set_event_loop(self.loop)
            self.main_task = self.loop.create_task(self.main())
            self.loop_ready.set()
            self.loop.run_until_complete(self.main_task)
        except (asyncio.CancelledError, asyncio.IncompleteReadError):
            pass
        finally:
            tasks = asyncio.all_tasks(self.loop)
            for task in tasks:
                if not task.cancelled():
                    self.loop.call_soon_threadsafe(task.cancel)
            tasks = asyncio.gather(*tasks, return_exceptions=True)
            tasks = asyncio.wait_for(tasks, self.cleanup_timeout)
            self.loop.run_until_complete(tasks)
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.stop()
            self.loop_ready.clear()

    def stop(self):
        if hasattr(self, 'main_task') and not self.main_task.cancelled():
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.main_task.cancel)
        if hasattr(self, 'thread'):
            self.thread.join()

    def is_running(self):
        return self.loop_ready.set() and self.loop.is_running()

    async def cobs_write(self, writer, data):
        packet = cobs.encode(pickle.dumps(data))
        writer.write(packet)
        writer.write(self.delimeter)
        await writer.drain()

    async def cobs_read(self, reader):
        packet = await reader.readuntil(self.delimeter)
        return pickle.loads(cobs.decode(packet[:-len(self.delimeter)]))

    async def recv_update(self, reader):
        command, key, *value = data = await self.cobs_read(reader)
        if command is SharedStore.Command.SET:
            SharedStore.__setitem__(self, key, value[0])
        elif command is SharedStore.Command.DEL:
            SharedStore.__delitem__(self, key)
        return data

    def watch(self, key, coro):
        """ Register a coroutine that should be called whenever a key mutates. """
        self.watchers[key] = coro

    def unwatch(self, key):
        """ Unregister a watcher coroutine. """
        if key in self.watchers:
            del self.watchers[key]

    def _trigger_watch(self, key):
        watch_coro = self.watchers.get(key)
        if watch_coro:
            self.loop_ready.wait()
            if self.loop.is_running():
                asyncio.run_coroutine_threadsafe(watch_coro(self, key), self.loop)

    def __setitem__(self, key, value):
        self._trigger_watch(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self._trigger_watch(key)
        super().__delitem__(key)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


class SharedStoreServer(SharedStore):
    """
    A shared key-value store server.

    Attributes:
        buf_lock (asyncio.Lock): Synchronizes access to the update buffer
            table. Note that the individual buffers themselves are allowed to
            mutate without the lock.
        update_buffers (dict): Map from randomly generated client IDs to
            buffers holding messages to be written to replicas.
    """
    def __init__(self, *args, buf_max_size=1024, **kwargs):
        self.server_ready = threading.Event()
        self.buf_lock, self.buf_max_size = asyncio.Lock(), buf_max_size
        self.update_buffers = {}
        super().__init__(*args, **kwargs)

    def start(self):
        super().start()
        self.server_ready.wait()

    async def main(self):
        self.server = await asyncio.start_unix_server(self.handle, self.addr)
        async with self.server:
            self.server_ready.set()
            await self.server.serve_forever()

    def stop(self):
        self.server_ready.wait()
        if self.server.is_serving():
            try:
                self.server.close()
            except TypeError:
                pass
        self.server_ready.clear()
        super().stop()
        os.unlink(self.addr)

    async def read(self, reader: asyncio.StreamReader, client_id: str):
        buf = self.update_buffers[client_id]
        while True:
            try:
                command, store_key, *_ = data = await self.recv_update(reader)
                if command is SharedStore.Command.GET:
                    found = store_key in self
                    if found:
                        value = super().__getitem__(store_key)
                        await buf.put((SharedStore.Command.SET, store_key, value))
                    await buf.put((SharedStore.Command.ACK, store_key, found))
                elif command & SharedStore.Command.MUTATE:
                    async with self.buf_lock:
                        for buf_client_id, buf in self.update_buffers.items():
                            if buf_client_id != client_id:
                                await buf.put(data)
            except pickle.PickleError:
                continue

    async def write(self, writer: asyncio.StreamWriter, client_id: str):
        buf = self.update_buffers[client_id]
        while True:
            try:
                await self.cobs_write(writer, await buf.get())
            except pickle.PickleError:
                continue

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            client_id = str(uuid.uuid4())
            async with self.buf_lock:
                self.update_buffers[client_id] = asyncio.Queue(maxsize=self.buf_max_size)
            await self.cobs_write(writer, (SharedStore.Command.ACK,))

            tasks = {self.read(reader, client_id), self.write(writer, client_id)}
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            for task in pending:
                task.cancel()
        finally:
            writer.close()
            async with self.buf_lock:
                if client_id in self.update_buffers:
                    del self.update_buffers[client_id]

    async def send_set(self, key, value):
        async with self.buf_lock:
            for buf in self.update_buffers.values():
                await buf.put((SharedStore.Command.SET, key, value))

    async def send_del(self, key):
        async with self.buf_lock:
            for buf in self.update_buffers.values():
                await buf.put((SharedStore.Command.DEL, key))

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.loop_ready.wait()
        asyncio.run_coroutine_threadsafe(self.send_set(key, value), self.loop)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.loop_ready.wait()
        asyncio.run_coroutine_threadsafe(self.send_del(key), self.loop)


class SharedStoreClient(SharedStore):
    """
    A shared key-value store client.
    """
    def __init__(self, *args, **kwargs):
        self.writer_ready = threading.Event()
        self.req_lock, self.res_recv = threading.Lock(), threading.Event()
        self.res_recv.set()
        super().__init__(*args, **kwargs)

    def start(self):
        super().start()
        self.writer_ready.wait()

    async def wait_for_ack(self, reader):
        while True:
            command, *_ = data = await self.cobs_read(reader)
            if command is SharedStore.Command.ACK:
                return data

    async def main(self):
        try:
            reader, self.writer = await asyncio.open_unix_connection(self.addr)
            await self.wait_for_ack(reader)
            self.writer_ready.set()
            while True:
                try:
                    command, *_ = await self.recv_update(reader)
                    if command is SharedStore.Command.ACK and not self.res_recv.is_set():
                        self.res_recv.set()
                except pickle.PickleError:
                    continue
        finally:
            if hasattr(self, 'writer'):
                self.writer.close()
                self.writer_ready.clear()

    def __getitem__(self, key):
        if key not in self:
            self.writer_ready.wait()
            with self.req_lock:
                self.res_recv.clear()
                task = self.cobs_write(self.writer, (SharedStore.Command.GET, key))
                asyncio.run_coroutine_threadsafe(task, self.loop)
                self.res_recv.wait()
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.writer_ready.wait()
        self.loop_ready.wait()
        task = self.cobs_write(self.writer, (SharedStore.Command.SET, key, value))
        asyncio.run_coroutine_threadsafe(task, self.loop)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.writer_ready.wait()
        self.loop_ready.wait()
        task = self.cobs_write(self.writer, (SharedStore.Command.DEL, key))
        asyncio.run_coroutine_threadsafe(task, self.loop)


class StateManager:
    DEVICES_KEY = ''

    def __init__(self, addr, schema):
        if not os.path.exists(addr):
            self.store = SharedStoreServer(addr)
        else:
            self.store = SharedSToreClient(addr)
        for protocol, devices in schema.items():
            for device_name, device in devices.items():
                pass

    @classmethod
    def load_from_schema(cls, filename: str):
        schema = read_conf_file(filename)
        return StateManager()

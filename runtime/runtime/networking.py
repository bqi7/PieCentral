import asyncio
import signal
import socket
from typing import Tuple
import msgpack
import aio_msgpack_rpc as rpc

import runtime.journal
from runtime.store import StoreService
from runtime.util import RuntimeBaseException

LOGGER = runtime.journal.make_logger(__name__)

Addr = Tuple[str, int]


class StreamingProtocol(asyncio.DatagramProtocol):
    stat_log_period = 30

    def connection_made(self, transport):
        self.transport = transport
        LOGGER.debug('Streaming server connection made.')
        self.bad_msg_count, self.msg_count = 0, 0
        self.stat_log_task = asyncio.ensure_future(self.log_statistics())

    def connection_lost(self, exc):
        LOGGER.debug('Streaming server connection lost.')
        self.stat_log_task.cancel()

    def datagram_received(self, data, addr):
        try:
            command = msgpack.unpackb(data)
        except msgpack.exceptions.ExtraData:
            self.bad_msg_count += 1
        finally:
            self.msg_count += 1

        # TODO

        response = {}
        self.transport.sendto(msgpack.packb(response), addr)

    def error_received(self, exc):
        LOGGER.error(str(exc))

    async def log_statistics(self):
        try:
            while True:
                LOGGER.debug('Streaming server statistics.',
                             bad_msg_count=self.bad_msg_count, msg_count=self.msg_count)
                await asyncio.sleep(self.stat_log_period)
        except asyncio.CancelledError:
            pass

    @classmethod
    async def make_streaming_server(cls, local_addr: Addr, remote_addr: Addr = None):
        return await asyncio.get_event_loop().create_datagram_endpoint(
            cls,
            local_addr=local_addr,
            remote_addr=remote_addr,
            family=socket.AF_INET,
            reuse_address=True,
            reuse_port=True,
        )


async def make_rpc_server(service, host=None, port=None, path=None, **options):
    if host and port:
        return await asyncio.start_server(rpc.Server(service), host=host, port=port, **options)
    elif path:
        return await asyncio.start_unix_server(rpc.Server(service), path=path, **options)
    else:
        raise RuntimeBaseException('Must run service with TCP or UNIX sockets.')


async def make_rpc_client():
    pass


async def make_circuitbreaker():
    if host and port:
        pass


async def start(options):
    try:
        host, rpc_port, stream_recv_port = options['host'], options['tcp'], options['udp_recv']
        rpc_server = await make_rpc_server(StoreService(options), host=host, port=rpc_port)
        async with rpc_server:
            LOGGER.info('Starting RPC server.', host=host, port=rpc_port)
            await asyncio.gather(
                rpc_server.serve_forever(),
                StreamingProtocol.make_streaming_server((host, stream_recv_port)),
            )
    except asyncio.CancelledError:
        pass
    finally:
        await rpc_server.wait_closed()
        LOGGER.info('Stopped RPC server gracefully.')

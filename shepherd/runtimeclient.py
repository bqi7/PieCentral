import asyncio
import aio_msgpack_rpc as rpc
from functools import lru_cache
import click


class RuntimeClient:
    """
    A Python interface for communicating with Runtime.
    This client uses `aio_msgpack_rpc` to perform asynchronous remote procedure
    calls (RPC). The underlying messages are packaged using `msgpack`, a
    JSON-like binary serialization format, so all parameters and return values
    need to be serializable with `msgpack`.
    At a low level, the client interacts with the server with either
    notifications (one-way, non-blocking) or calls (request-response, blocking).
    By default, the client uses calls, but notifications can be used with the
    `block=False` keyword.
    Example::
        >>> async def main():
        ...     client = RuntimeClient('192.168.128.200', 1234)
        ...     async with client:
        ...         await client.set_field_param('team', 'blue')
        ...         print('Team:', await client.get_field_param('team'))
        >>> asyncio.run(main())
        Team: blue
    References::
        .. _aio-msgpack-rpc PyPI Page
            https://pypi.org/project/aio-msgpack-rpc/
    """
    def __init__(self, host: str, port: int = 6200):
        self.host, self.port = host, port
        # Every client gets its own method wrapper cache.
        self._get_method_wrapper = lru_cache(maxsize=1024)(self._get_method_wrapper)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb):
        await self.disconnect()

    async def connect(self):
        self.client = rpc.Client(*await asyncio.open_connection(self.host, self.port))

    async def disconnect(self):
        if hasattr(self, 'client'):
            self.client.close()
            delattr(self, 'client')

    def _get_client(self):
        try:
            return self.client
        except AttributeError as exc:
            raise ValueError('Must connect to runtime before issuing commands.') from exc

    def _get_method_wrapper(self, name):
        async def method_wrapper(*args, block=True, **kwargs):
            client = self._get_client()
            if block:
                return await client.call(name, *args, **kwargs)
            else:
                client.notify(name, *args, **kwargs)
        method_wrapper.__name__ = name
        return method_wrapper

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return self._get_method_wrapper(name)

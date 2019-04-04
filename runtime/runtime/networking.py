import asyncio
import signal
import socket
import time
import aio_msgpack_rpc as rpc

import runtime.journal

LOGGER = runtime.journal.make_logger(__name__)


class StreamingProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def datagram_received(self, data, addr):
        pass

    def error_received(self, exc):
        pass

    async def send_datagrams(self):
        pass


async def run_rpc_server(service: type, host=None, port=None, path=None, **options):
    if host and port:
        server = await asyncio.start_server(rpc.Server(service), host=host, port=port, **options)
    elif path:
        server = await asyncio.start_unix_server(rpc.Server(service), path=path, **options)
    else:
        raise RuntimeBaseException('Must run service')
    async with server:
        await server.serve_forever()


async def make_rpc_client():
    pass


async def make_circuitbreaker():
    if host and port:
        pass


if __name__ == '__main__':
    from runtime.store import StoreService
    asyncio.run(run_rpc_server(StoreService({
        'dev_names': 'test-dev-names.yaml',
    }), '127.0.0.1', 6200))
# async def main():
#     await asyncio.open_connection(host='8.8.8.8', port=1234)
#     # await asyncio.open_unix_connection('/tmp/tmp.sock')
# asyncio.run(main())


# async def create_server(host: str, port: int, protocol: asyncio.BaseProtocol):
#     loop = asyncio.get_event_loop()
#     return await loop.create_server(protocol, host, port, family=socket.AF_INET,
#                                     reuse_address=True, reuse_port=True)
#
#
# async def run(host: str, tcp_port: int, udp_send_port: int, udp_recv_port: int):
#     while True:
#         pass
#     loop = asyncio.get_event_loop()
#     try:
#         streaming_server = await create_server(host, tcp_port, DawnStreamingProtocol) # UDP two-way connection to dawn
#         command_server = await create_server(host, udp_recv_port, CommandProtocol) # TCP connection to dawn (will need another one for TCP to Shepherd)
#
#         async with streaming_server, command_server:
#             await asyncio.gather(streaming_server.serve_forever(),
#                                           command_server.serve_forever())
#     except asyncio.CancelledError:
#          LOGGER.info('Event loop cancelled.')
#     finally:
#         await asyncio.gather(streaming_server.wait_closed(),
#                                      command_server.wait_closed())
#         LOGGER.info('Closed streaming and command servers.')

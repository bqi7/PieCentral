import asyncio
import signal
import socket
import time

from runtime.logging import make_logger

LOGGER = make_logger(__name__)


class DawnStreamingProtocol(asyncio.DatagramProtocol):
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


class CommandProtocol(asyncio.Protocol):
    pass


class NetworkingMonitor:
    pass


class NetworkingManager:
    def __init__(self):
        pass

    def __call__(self):
        pass


async def create_server(host: str, port: int, protocol: asyncio.BaseProtocol):
    loop = asyncio.get_event_loop()
    return await loop.create_server(protocol, host, port, family=socket.AF_INET,
                                    reuse_address=True, reuse_port=True)


async def run(host: str, tcp_port: int, udp_send_port: int, udp_recv_port: int):
    while True:
        pass
    # loop = asyncio.get_event_loop()
    # try:
    #     streaming_server = await create_server(host, tcp_port, DawnStreamingProtocol)
    #     command_server = await create_server(host, udp_recv_port, CommandProtocol)
    #     async with streaming_server, command_server:
    #         await asyncio.gather(streaming_server.serve_forever(),
    #                              command_server.serve_forever())
    # except asyncio.CancelledError:
    #     LOGGER.info('Event loop cancelled.')
    # finally:
    #     await asyncio.gather(streaming_server.wait_closed(),
    #                          command_server.wait_closed())
    #     LOGGER.info('Closed streaming and command servers.')


def stop(_signum, _stack_frame):
    pass


def start(host, tcp_port, udp_send_port, udp_recv_port):
    signal.signal(signal.SIGTERM, stop)
    LOGGER.debug('Attached SIGTERM handler.')
    asyncio.run(run(host, tcp_port, udp_send_port, udp_recv_port))

import asyncio
import signal
import socket

from runtime.logging import make_logger

LOGGER = make_logger(__name__)


class DawnStreamingProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print('OK!')

    def connection_lost(self, exc):
        pass

    def datagram_received(self, data, addr):
        pass

    def error_received(self, exc):
        pass

    async def send_datagrams(self):
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


async def run(host: str, streaming_port: int, command_port: int):
    loop = asyncio.get_event_loop()
    try:
        streaming_server = await create_server(host, streaming_port, DawnStreamingProtocol)
        command_server = await create_server(host, command_port, CommandProtocol)
        async with streaming_server, command_server:
            await asyncio.gather(streaming_server.serve_forever(),
                                 command_server.serve_forever())
    except asyncio.CancelledError:
        LOGGER.info('Event loop cancelled.')
    finally:
        await asyncio.gather(streaming_server.wait_closed(),
                             command_server.wait_closed())
        LOGGER.info('Closed streaming and command servers.')


def stop(_signum, _stack_frame):
    tasks = asyncio.all_tasks()
    for task in tasks:
        if not task.cancelled():
            task.cancel()
    tasks = asyncio.gather(*tasks, return_exceptions=True)
    tasks = asyncio.wait_for(tasks, )


# def start(host, streaming_port, command_port):
#     signal.signal(signal.SIGTERM, stop)
#     asyncio.run(run(host, streaming_port, command_port))


def start(hostname, tcp_port, udp_send_port, udp_recv_port):
    time.sleep(5)

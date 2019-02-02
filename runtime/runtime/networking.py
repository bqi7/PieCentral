import asyncio
import errno
from threading import Thread
import socket

from runtime.statemanager import StateManager


class DawnRecvProtocol(asyncio.DatagramProtocol):
    pass


class DawnSendProtocol(asyncio.DatagramProtocol):
    pass


async def handle_dawn_stream(reader, writer):
    pass


async def run(manager):
    server = await asyncio.start_server()


def bootstrap(addr):
    with StateManagerProxy(addr) as manager:
        try:
            asyncio.run(run(manager))
        except:
            pass


# def run(addr):
#     with StateManager(addr) as manager:
#         asyncio.run()
#         asyncio.start_server()
#         asyncio.create_datagram_endpoint(DawnRecvProtocol, remote_addr=addr,
#                                          family=socket.AF_INET, reuse_address=True, reuse_port=True)

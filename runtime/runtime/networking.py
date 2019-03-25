import asyncio
import signal
import socket
import time

from runtime.logger import make_logger

LOGGER = make_logger(__name__)

class DawnStreamingProtocol(asyncio.DatagramProtocol):
    """UDP Send/Recv"""
    
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        pass

    def datagram_received(self, data, addr):
        """I'm assuming that data in is a string in the form:
        "state gamepad1 gamepad2 gamepad3 gamepad4 ..."
        """
        
        processed_data = {} # dictionary for final returned data
        
        raw = data.decode().split() # split received packet into list of strings
        new_state = raw[0] # first thing is the new state of the system
        unpackaged_data["student_code_status"] = [new_state, time.time()]
        
        # somehow get the current robot state from statemanager (shard memory?)
        control_state = NULL # <-- change this
        
        # send the new state to state manager
        if control_state is None or new_state != control_state:
            sm_state_command = self.sm_mapping[new_state]
            self.state_queue.put([sm_state_command, []])
            
        all_gamepad_dict = {}
        for gamepad in raw[1:]:
            gamepad_dict = {}
            gamepad_dict["axes"] = dict(enumerate(gamepad.axes)) # these need to change, not sure how to process these
            gamepad_dict["buttons"] = dict(enumerate(gamepad.buttons))
            all_gamepad_dict[gamepad.index] = gamepad_dict
        processed_data["gamepads"] = [all_gamepad_dict, time.time()]
        
        # put processed_data onto shared memory to state manager

    def error_received(self, exc):
        pass

    async def send_datagrams(self):
        pass
        
        # 1) have a clock that periodically pulls data from SM and sends it periodicaly
            # probelm is, 
            # probably better bc
        # 2) have thread wait for new data to arrive on SM


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
    loop = asyncio.get_event_loop()
    try:
        streaming_server = await create_server(host, tcp_port, DawnStreamingProtocol) # UDP two-way connection to dawn
        command_server = await create_server(host, udp_recv_port, CommandProtocol) # TCP connection to dawn (will need another one for TCP to Shepherd)
        
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
    pass


def start(host, tcp_port, udp_send_port, udp_recv_port):
    signal.signal(signal.SIGTERM, stop)
    LOGGER.debug('Attached SIGTERM handler.')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # open a socket on a port to broadcast on
    sock.connect((UDP_IP, UDP_BROADCAST_PORT))
    ##TODO: put sock as an argument to the hotplugging and device_disconnected async coroutines
    asyncio.run(run(host, tcp_port, udp_send_port, udp_recv_port))

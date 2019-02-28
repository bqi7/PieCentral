"""Functions and classes for communication with Dawn."""

import socket
import asyncio
import time
import sys
import selectors
import csv
import runtime_pb2
import ansible_pb2
import notification_pb2
from runtimeUtil import *

UDP_SEND_PORT = 1235
UDP_RECV_PORT = 1236
TCP_DAWN_PORT = 1234 """changed name from TCP_PORT to TCP_DAWN_PORT"""
TCP_SHEP_PORT = 1233 """new port for TCP connection to Shepherd"""

TCP_HZ = 5.0
# Only for UDPSend Process
PACKAGER_HZ = 5.0
SOCKET_HZ = 5.0

class AnsibleClass:
    """Class that handles of all of robot's external communcation
    
    Four tasks in event loop:
    - UDP Receive, between robot and Dawn (commands from GamePad)
    - UDP Send, between robot and Dawn (information about robot state)
    - TCP Send/Receive, between robot and Dawn (important events from Robot)
    - TCP Send/Receive, between robot and Shephert (Autonomous, Tele-op start and stop)
    """
    
    """Create an instance of AnsibleClass, called from runtime
    
    - sets up instance variables
    - creates new instances of the UDPSend, UDPRecv, and TCP classes
    """
    def __init__(self, badThingsQueue, stateQueue, pipe):
        self.bad_things_queue = badThingsQueue
        self.state_queue = stateQueue
        self.pipe = pipe
        self.dawn_ip = pipe.recv()[0]
        
        self.udp_send = UDPSendClass(badThingsQueue, stateQueue, pipe)
        self.udp_receive = UDPRecvClass(badThingsQueue, stateQueue, pipe)
        self.tcp_dawn = TCPClass("dawn", badThingsQueue, stateQueue, pipe)
        self.tcp_shep = TCPClass("shepherd", badThingsQueue, stateQueue, pipe))
    
    """Performs configuration procedures when starting Ansible
    
    - Opens sockets to needed ports
    - Sets up and runs the event loop   
    """
    def start():
        
          

class UDPSendClass():
    
    """Wrapper class for sending operations over UDP""" 
    def __init__(self, badThingsQueue, stateQueue, pipe):
        pass
        
    def package_data(self, bad_things_queue, state_queue, pipe):
        """Function which packages data to be sent.

        The robot's current state is received from StateManager via pipe and packaged
        by the package function, defined internally. 
        """
        def package(state):
            """Helper function that packages the current state.

            Parses through the state dictionary in key-value pairs, creates a new message in the
            proto for each sensor, and adds corresponding data to each field. Currently only
            supports a single limit_switch switch as the rest of the state is just test fields.
            """
            try:
                proto_message = runtime_pb2.RuntimeData()
                proto_message.robot_state = state['studentCodeState'][0]
                for uid, values in state['hibike'][0]['devices'][0].items():
                    sensor = proto_message.sensor_data.add()
                    sensor.uid = str(uid)
                    sensor.device_type = SENSOR_TYPE[uid >> 72]
                    for param, value in values[0].items():
                        if value[0] is None:
                            continue
                        param_value_pair = sensor.param_value.add()
                        param_value_pair.param = param
                        if isinstance(value[0], bool):
                            param_value_pair.bool_value = value[0]
                        elif isinstance(value[0], float):
                            param_value_pair.float_value = value[0]
                        elif isinstance(value[0], int):
                            param_value_pair.int_value = value[0]
                return proto_message.SerializeToString()
            except Exception as e:
                bad_things_queue.put(
                    BadThing(
                        sys.exc_info(),
                        "UDP packager thread has crashed with error:" +
                        str(e),
                        event=BAD_EVENTS.UDP_SEND_ERROR,
                        printStackTrace=True))
        while True:
            try:
                next_call = time.time()
                state_queue.put([SM_COMMANDS.SEND_ANSIBLE, []])
                raw_state = pipe.recv()
                pack_state = package(raw_state)
                self.send_buffer.replace(pack_state)
                next_call += 1.0 / PACKAGER_HZ
                time.sleep(max(next_call - time.time(), 0))
            except Exception as e:
                bad_things_queue.put(
                    BadThing(
                        sys.exc_info(),
                        "UDP packager thread has crashed with error:" +
                        str(e),
                        event=BAD_EVENTS.UDP_SEND_ERROR,
                        printStackTrace=True))

    def udp_sender(self, bad_things_queue, _state_queue, _pipe):
        """Function run as a thread that sends a packaged state from the TwoBuffer

        The current state that has already been packaged is gotten from the
        TwoBuffer, and is sent to Dawn via a UDP socket.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            while True:
                try:
                    next_call = time.time()
                    msg = self.send_buffer.get()
                    if msg != 0 and msg is not None and self.dawn_ip is not None:
                        sock.sendto(msg, (self.dawn_ip, UDP_SEND_PORT))
                    next_call += 1.0 / SOCKET_HZ
                    time.sleep(max(next_call - time.time(), 0))
                except Exception as e:
                    bad_things_queue.put(
                        BadThing(
                            sys.exc_info(),
                            "UDP sender thread has crashed with error: " +
                            str(e),
                            event=BAD_EVENTS.UDP_SEND_ERROR,
                            printStackTrace=True))
    
    async def send():
        pass

"""Wrapper class for receiving operations over UDP"""
class UDPRecvClass():
    
    def __init__():
        pass
    
    async def receive():
        pass

"""Wrapper class for send and receive over TCP"""
class TCPClass():
    
    def __init__(dest):
        self.dest = dest
    
    async def tcp_send():
        pass
    
    async def tcp_recv():
        pass
        
        
        
        
        
        
    
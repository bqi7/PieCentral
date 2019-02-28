"""Functions and classes for communication with Dawn."""

import socket
import threading
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
TCP_PORT = 1234

TCP_HZ = 5.0
# Only for UDPSend Process
PACKAGER_HZ = 5.0
SOCKET_HZ = 5.0

class AnsibleClass:
    
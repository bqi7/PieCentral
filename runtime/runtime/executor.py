import os
import sys
import socket
import time
import inspect
import importlib

import runtime.logger
from runtime.api import Robot
import runtime.devices

def blank_function():
    pass


async def blank_coroutine():
    pass


class StudentCodeExecutor:
    required_functions = {
        'autonomous_setup': blank_function,
        'autonomous_main': blank_function,
        'teleop_setup': blank_function,
        'teleop_main': blank_function,
        'autonomous_actions': blank_coroutine,
    }

    def __init__(self, path: str):
        self.path = os.path.abspath(os.path.expanduser(path))
        dirname, basename = os.path.split(self.path)
        self.module_name, _ = os.path.splitext(basename)
        if dirname not in sys.path:
            sys.path.append(dirname)
            LOGGER.debug(f'Added "{dirname}" to "sys.path".')

    def __call__(self, student_freq, student_timeout):
        while True:
            self.reload()
            time.sleep(1)

    def patch(self, module):
        """ Monkey-patch student code. """
        module.Robot = Robot
        for name, default_function in self.required_functions.items():
            if not hasattr(module, name):
                setattr(module, name, default_function)

    def validate(self, module):
        for name, default_function in self.required_functions.items():
            function = getattr(module, name)
            if not inspect.isfunction(function):
                raise RuntimeExecutorException(f'"{name}" is not a function.',
                                               function_name=name)
            expects_coro = inspect.iscoroutinefunction(default_function)
            actually_coro = inspect.iscoroutinefunction(function)
            if expects_coro and not actually_coro:
                raise RuntimeExecutorException(
                    f'"{name}" is not a coroutine function when it should be.',
                    function_name=name,
                )
            if not expects_coro and actually_coro:
                raise RuntimeExecutorException(
                    f'"{name}" is a corountine function when it should not be.',
                    function_name=name,
                )
            if inspect.signature(default_function) != inspect.signature(function):
                raise RuntimeExecutorException(f'"{name}" signature is not correct.',
                                               function_name=name)

    def reload(self):
        if not hasattr(self, 'module'):
            self.module = importlib.import_module(self.module_name)
        else:
            self.module = importlib.reload(self.module)
        self.patch(self.module)
        self.validate(self.module)
        # except Exception as exc:
        #     LOGGER.error('Unable to import student code module.',
        #                  msg=str(exc), type=type(exc).__name__)
        # else:
        #     LOGGER.debug('Imported student code module.')

def stop(_signum, _stack_frame):
    pass


def start(student_code, student_freq, student_timeout):
    signal.signal(signal.SIGTERM, stop)
    LOGGER.debug('Attached SIGTERM handler.')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # open a socket on a port to broadcast on
    sock.connect((UDP_IP, UDP_BROADCAST_PORT))
    ##TODO: put sock as an argument to the hotplugging and device_disconnected async coroutines
    sc_exc = StudentCodeExecutor(student_code)
    sc_exc(student_freq, student_timeout)

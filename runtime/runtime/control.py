"""
runtime.control -- Runtime control and event loop.
"""

import asyncio
import atexit
from enum import Enum, auto
import multiprocessing
import importlib
import os
import sys
import time
from types import ModuleType
from typing import Callable, Tuple, Dict
import aioprocessing
import runtime.logging
from runtime.api import Robot
from runtime import networking, devices
from runtime.util import RuntimeException, RuntimeIPCException
from collections import UserDict

LOGGER = runtime.logging.make_logger(__name__)


class Mode(Enum):
    IDLE = auto()
    AUTO = auto()
    TELEOP = auto()
    ESTOP = auto()


class StudentCodeExecutor:
    def __init__(self, path: str):
        self.path = os.path.abspath(os.path.expanduser(path))
        dirname, basename = os.path.split(self.path)
        self.module_name, _ = os.path.splitext(basename)
        sys.path.append(dirname)
        LOGGER.debug(f'Added "{dirname}" to "sys.path".')

    def __call__(self, student_freq, student_timeout):
        while True:
            self.reload()
            time.sleep(1)

    def patch(self):
        self.module.Robot = Robot

    def reload(self):
        try:
            if not hasattr(self, 'module'):
                self.module = importlib.import_module(self.module_name)
            else:
                self.module = importlib.reload(self.module)
        except Exception as exc:
            LOGGER.error('Unable to import student code module.',
                         msg=str(exc), type=type(exc).__name__)
        else:
            LOGGER.debug('Imported student code module.')


def run_student_code(module_file):
    pass


class SubprocessMonitor(UserDict):
    def __init__(self, max_respawns: int, respawn_reset: float):
        self.max_respawns, self.respawn_reset = max_respawns, respawn_reset
        self.subprocesses = {}
        super().__init__()

    def add(self, name: str, target: Callable, args: Tuple = None, kwargs: Dict = None):
        self[name] = (target, args or (), kwargs or {})

    async def start_process(self, name):
        if name in self.subprocesses and self.subprocesses[name].is_alive():
            raise RuntimeIPCException('Cannot start subprocess: already running.',
                                      name=name)
        target, args, kwargs = self[name]
        subprocess = self.subprocesses[name] = aioprocessing.AioProcess(
            name=name,
            target=target,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        subprocess.start()
        return subprocess

    async def monitor_process(self, name):
        failures = 0
        while True:
            start = time.time()
            subprocess = await self.start_process(name)
            await subprocess.coro_join()
            end = time.time()
            if end - start > self.respawn_reset:
                failures = 0
            failures += 1
            ctx = {'start': start, 'end': end, 'failures': failures, 'subprocess_name': name}
            LOGGER.warn('Subprocess failed.', **ctx)
            if failures >= self.max_respawns:
                raise RuntimeIPCException('Subprocess failed too many times.', **ctx)
            else:
                LOGGER.warn('Attempting to respawn subprocess.', subprocess_name=name)

    async def spin(self):
        monitors = [self.monitor_process(name) for name in self]
        await asyncio.gather(*monitors)

    def terminate(self, timeout=None):
        for name in self:
            subprocess = self.subprocesses[name]
            if subprocess.is_alive():
                LOGGER.warn('Sending SIGTERM to subprocess.', subprocess_name=name)
                subprocess.terminate()
                subprocess.join(timeout)
                time.sleep(0.05)  # Wait for "exitcode" to set.
                if subprocess.exitcode is None:
                    LOGGER.critical('Sending SIGKILL to subprocess. '
                                    'Unable to shut down gracefully.',
                                    subprocess_name=name)
                    subprocess.kill()

    def running_count(self):
        return sum(subprocess.is_alive() for subprocess in self.subprocesses.values())


def bootstrap(options):
    runtime.logging.initialize(options['log_level'])
    monitor = SubprocessMonitor(options['max_respawns'], options['respawn_reset'])
    monitor.add('networking', networking.start, (
        options['host'],
        options['tcp'],
        options['udp_send'],
        options['udp_recv'],
    ))
    monitor.add('devices', devices.start, (
        options['poll'],
        options['poll_period'],
        options['encoders'],
        options['decoders'],
    ))
    monitor.add('executor', StudentCodeExecutor(options['student_code']), (
        options['student_freq'],
        options['student_timeout'],
    ))
    try:
        asyncio.run(monitor.spin())
    except KeyboardInterrupt:
        LOGGER.warn('Received keyboard interrupt. Exiting.')
    except Exception as exc:
        # If we reach the top of the call stack, something is seriously wrong.
        ctx = exc.data if isinstance(exc, RuntimeException) else {}
        msg = 'Fatal exception: Runtime cannot recover from this failure.'
        LOGGER.critical(msg, msg=str(exc), type=type(exc).__name__, ctx=ctx,
                        options=options)
    finally:
        monitor.terminate(options['terminate_timeout'])

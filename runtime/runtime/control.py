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


class StudentCode:
    def __init__(self, path: str):
        self.path = os.path.abspath(os.path.expanduser(path))
        dirname, basename = os.path.split(self.path)
        sys.path.append(dirname)
        LOGGER.debug(f'Added "{dirname}" to `sys.path`.')

        self.module_name, _ = os.path.splitext(basename)
        self.module = importlib.import_module(self.module_name)
        LOGGER.debug('Imported student code module.', module=self.module_name)

    def patch(self):
        self.module.Robot = Robot

    def reload(self):
        self.module = importlib.reload(self.module)


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
            LOGGER.warn('Subprocess failed.', name=name, start=start, end=end, failures=failures)
            if failures >= self.max_respawns:
                raise RuntimeIPCException('Subprocess failed too many times.', failures=failures)
            else:
                LOGGER.warn('Attempting to respawn subprocess.', name=name)

    async def spin(self):
        monitors = [self.monitor_process(name) for name in self]
        await asyncio.gather(*monitors)

    def terminate(self):
        for name in self:
            self.subprocesses[name].terminate()


def bootstrap(options):
    runtime.logging.initialize(options['log_level'])
    monitor = SubprocessMonitor(options['max_respawns'], options['respawn_reset'])
    monitor.add('networking', networking.start, (
        options['hostname'],
        options['tcp'],
        options['udp_send'],
        options['udp_recv'],
    ))
    monitor.add('devices', devices.start, (
        options['poll_period'],
    ))
    try:
        asyncio.run(monitor.spin())
    except KeyboardInterrupt:
        LOGGER.warn('Received keyboard interrupt. Exiting.')
    except Exception as exc:
        # If we reach the top of the call stack, something is seriously wrong.
        ctx = exc.data if isinstance(exc, RuntimeException) else {}
        msg = 'Fatal exception: Runtime cannot recover from this failure.'
        LOGGER.critical(msg, msg=str(exc), ctx=ctx, options=options)
    finally:
        monitor.terminate()

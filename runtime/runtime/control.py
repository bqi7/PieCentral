"""
runtime.control -- Runtime control and event loop.
"""

import asyncio
import atexit
from enum import Enum, auto
import importlib
import os
import sys
import runtime.logging
from types import ModuleType

LOGGER = runtime.logging.make_logger(__name__)


class Mode(Enum):
    IDLE = auto()
    AUTO = auto()
    TELEOP = auto()
    ESTOP = auto()


class EventLoop:
    def __init__(self, state=Mode.IDLE):
        self.state = state


class StudentCode:
    def __init__(self, path: str):
        self.path = os.path.abspath(os.path.expanduser(path))
        sys.path.append(self.path)
        dirname, basename = os.path.split(self.path)
        LOGGER.debug(f'Added "{dirname}" to `sys.path`.')
        self.module_name, _ = os.path.splitext(basename)
        self.module = importlib.import_module(self.module_name)
        LOGGER.debug('Imported student code module.', module_name=self.module_name)

    def reload(self):
        self.module = importlib.reload(self.module)


def run_student_code(module_file):
    pass


def bootstrap(options):
    runtime.logging.initialize(options['log_level'])
    student_code = StudentCode(options['student_code'])

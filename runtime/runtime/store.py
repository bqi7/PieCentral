"""
runtime.store -- Runtime data storage
"""

import asyncio
import ctypes
import enum
import collections
from functools import lru_cache
import time
import posix_ipc
from runtime import __version__
import runtime.journal
from runtime.util import read_conf_file, RuntimeBaseException
from runtime.studentcode import *

LOGGER = runtime.journal.make_logger(__name__)


Parameter = collections.namedtuple(
    'Parameter',
    ['name', 'type', 'lower', 'upper', 'read', 'write', 'choices', 'default'],
    defaults=[float('-inf'), float('inf'), True, False, [], None],
)

Device = collections.namedtuple(
    'Device',
    ['name'],
)

CTYPES_SIGNED_INT = {ctypes.c_byte, ctypes.c_short, ctypes.c_int, ctypes.c_long,
                     ctypes.c_longlong, ctypes.c_ssize_t}
CTYPES_UNSIGNED_INT = {ctypes.c_ubyte, ctypes.c_ushort, ctypes.c_uint,
                       ctypes.c_ulong, ctypes.c_ulonglong, ctypes.c_size_t}
CTYPES_REAL = {ctypes.c_float, ctypes.c_double, ctypes.c_longdouble}
CTYPES_NUMERIC = CTYPES_SIGNED_INT | CTYPES_UNSIGNED_INT | CTYPES_REAL


class Alliance(enum.Enum):
    BLUE = enum.auto()
    GOLD = enum.auto()
    UNKNOWN = enum.auto()


class StartingZone(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()
    VENDING = enum.auto()
    SHELF = enum.auto()
    UNKNOWN = enum.auto()


class Mode(enum.Enum):
    IDLE = enum.auto()
    AUTO = enum.auto()
    TELEOP = enum.auto()
    ESTOP = enum.auto()


class StoreService(collections.UserDict):
    version_number_names = ('major', 'minor', 'patch')

    def __init__(self, options: dict):
        super().__init__()
        self.access = asyncio.Lock()
        self.update({
            'options': options,
            'fieldcontrol': {
                'alliance': Alliance.UNKNOWN,
                'startingzone': StartingZone.UNKNOWN,
                'mode': Mode.IDLE,
            },
            'smartsensor': {
                'names': {},
                'descriptors': {},
            },
        })

        try:
            self['smartsensor']['names'].update(read_conf_file(options['dev_names']))
        except (FileNotFoundError, RuntimeBaseException):
            LOGGER.warning('Unable to read Smart Sensor names.')

    def get_version(self):
        return dict(zip(self.version_number_names, __version__))

    def get_time(self):
        return time.time()

    @property
    def options(self):
        return self['options']

    @property
    def field_params(self):
        return self['fieldcontrol']

    @property
    def device_names(self):
        return self['smartsensor']['names']

    @property
    def device_descriptors(self):
        return self['smartsensor']['descriptors']

    async def get_options(self):
        async with self.access:
            return self.options

    async def set_options(self, persist=True, **options):
        async with self.access:
            self.options.update(options)
            if persist:
                with open(self.options['config']) as options_file:
                    write_conf_file(options_file, self.options)

    async def get_field_parameters(self):
        async with self.access:
            return {name: value.name.lower() for name, value in self.field_params.items()}

    async def set_alliance(self, alliance: str):
        async with self.access:
            self.field_params['alliance'] = Alliance.__members__[alliance.upper()]

    async def set_starting_zone(self, zone: str):
        async with self.access:
            self.field_params['startingzone'] = StartingZone.__members__[zone.upper()]

    async def set_mode(self, mode: str):
        async with self.access:
            # TODO: dispatch to executor
            self.field_params['mode'] = Mode.__members__[mode.upper()]

    async def run_coding_challenge(self, seed: int) -> int:
        async with self.access:
            self.field_params['challengesolution'] = None
            async def get_student_solution(f, seed: int) -> int:
                return f(seed)
            challenge_functions = [tennis_ball, remove_duplicates, rotate, next_fib, most_common, get_coins]
            solution = seed
            for f in challenge_functions:
                try:
                    solution = await asyncio.wait_for(get_student_solution(f, solution), timeout=1.0)
                except asyncio.TimeoutError as e:
                    LOGGER.error(str(f) + " took too long to provide an answer")
                    raise e
            return solution

    async def get_challenge_solution(self):
        async with self.access:
            return self.field_params.get('challengesolution')

    async def write_device_names(self):
        with open(self.options['dev_names']) as dev_name_file:
            write_conf_file(dev_name_file, self.device_names)

    async def get_device_names(self):
        async with self.access:
            return self.device_names

    async def set_device_name(self, name: str, uid: str):
        async with self.access:
            self.device_names[uid] = name
            await self.write_device_names()

    async def del_device_name(self, uid: str):
        async with self.access:
            del self.device_names[uid]
            await self.write_device_names()

    async def register_device(self, uid: str, description):
        async with self.access:
            pass  # TODO

    async def unregister_device(self, uid: str):
        async with self.access:
            pass  # TODO


def validate_param_value(param: Parameter, value):
    ctype = getattr(ctypes, f'c_{param.type}')
    ctype(value)  # Will raise a ``TypeError`` if the value is not correct.
    if ctype in CTYPES_NUMERIC and not param.lower <= value <= param.upper:
        raise RuntimeBaseException(
            'Parameter value not in bounds.',
            param_name=param.name,
            param_value=value,
            bounds=(param.lower, param.upper),
        )
    if value not in param.choices:
        raise RuntimeBaseException(
            'Parameter value is not a valid choice.',
            param_name=param.name,
            param_value=value,
            choices=param.choices,
        )


def parse_data_sources_schema(schema):
    for protocol, sources in schema.items():
        for source, descriptor in sources:
            pass

"""
runtime.store -- Runtime data storage
"""

import asyncio
import ctypes
import enum
import collections
from functools import lru_cache
import inspect
import time
import aio_msgpack_rpc as rpc
from runtime import __version__
from runtime.util import read_conf_file, RuntimeBaseException


Parameter = collections.namedtuple(
    'Parameter',
    ['name', 'type', 'lower', 'upper', 'read', 'write', 'choices', 'default'],
    defaults=[float('-inf'), float('inf'), True, False, [], None],
)

CTYPES_SIGNED_INT = {ctypes.c_byte, ctypes.c_short, ctypes.c_int, ctypes.c_long,
                     ctypes.c_longlong, ctypes.c_ssize_t}
CTYPES_UNSIGNED_INT = {ctypes.c_ubyte, ctypes.c_ushort, ctypes.c_uint,
                       ctypes.c_ulong, ctypes.c_ulonglong, ctypes.c_size_t}
CTYPES_REAL = {ctypes.c_float, ctypes.c_double, ctypes.c_longdouble}
CTYPES_NUMERIC = CTYPES_SIGNED_INT | CTYPES_UNSIGNED_INT | CTYPES_REAL


class StoreService(collections.UserDict):
    version_number_names = ('major', 'minor', 'patch')

    def __init__(self, config: dict):
        super().__init__()
        self.access = asyncio.Lock()
        self.config = config
        self.device_schema = read_conf_file(config['dev_schema'])
        self.fc_schema = read_conf_file(config['fc_schema'])
        self.device_names, self.device_uids = {}, {}

    def get_version(self):
        return dict(zip(self.version_number_names, __version__))

    def get_time(self):
        return time.time()

    async def get_field_param(self, key):
        async with self.access:
            return self[f'fieldcontrol:{key}']

    async def set_field_param(self, key, value):
        async with self.access:
            pass

    async def get_device_names(self):
        async with self.access:
            return self['smartsensor']['devicenames']

    async def set_device_name(self, name: str, uid: str):
        async with self.access:
            self['smartsensor']['devicenames'][uid] = name

    async def del_device_name(self, uid: str):
        async with self.access:
            del self['smartsensor']['devicenames'][uid]

    async def register_device(self, uid: str, description):
        pass

    async def unregister_device(self, uid: str):
        pass


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

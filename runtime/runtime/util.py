from collections import UserDict
from enum import IntEnum
import os
import json
import yaml


class RuntimeException(UserDict, Exception):
    """
    Base class for runtime-related exceptions.

    Example:

        >>> err = RuntimeException('Error', input=1, valid=[2, 3])
        >>> err['input']
        1
        >>> err['valid']
        [2, 3]
    """
    def __init__(self, msg: str, **data):
        super().__init__(data)
        super(Exception, self).__init__(msg)

    def __repr__(self):
        cls_name, (msg, *_) = self.__class__.__name__, self.args
        if self:
            kwargs = ', '.join(f'{name}={repr(value)}' for name, value in self.items())
            return f'{cls_name}({repr(msg)}, {kwargs})'
        return f'{cls_name}({repr(msg)})'


class AutoIntEnum(IntEnum):
    """
    An enum with automatically incrementing integer values, starting from zero.

    References:
        .. _Python `enum` Reference
            https://docs.python.org/3/library/enum.html#using-automatic-values
    """
    # pylint: disable=no-self-argument
    def _generate_next_value_(name, start, count, last_values):
        return count


CONF_FILE_FORMATS = {
    '.yml': yaml.load,
    '.yaml': yaml.load,
    '.json': json.load,
}


def read_conf_file(filename: str):
    """
    Read and parse a configuration file.

    Example:

        >>> read_conf_file('bad.csv')
        Traceback (most recent call last):
          ...
        runtime.util.RuntimeException: Configuration file format not recognized.
    """
    _, extension = os.path.splitext(filename)
    if extension not in CONF_FILE_FORMATS:
        raise RuntimeException(f'Configuration file format not recognized.',
                               valid_formats=list(CONF_FILE_FORMATS))
    with open(filename) as conf_file:
        return CONF_FILE_FORMATS[extension]

import asyncio
from collections import UserDict
from enum import IntEnum
import os
import json
import yaml
import threading


class RuntimeException(UserDict, Exception):
    """
    Base class for Runtime-specific exceptions.

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


class RuntimeIPCException(RuntimeException):
    pass


class RuntimeExecutorException(RuntimeException):
    pass


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


class AsyncioThread(threading.Thread):
    def __init__(self, *thread_args, target=None, args=None, kwargs=None,
                 cleanup_timeout=5, **thread_kwargs):
        args, kwargs = args or (), kwargs or {}
        if target:
            self.target, self.args, self.kwargs = target, args, kwargs
            target, args, kwargs = self.bootstrap, (), {}
            self.cleanup_timeout = cleanup_timeout
        super().__init__(*thread_args, **thread_kwargs, target=target, args=args, kwargs=kwargs)

    def bootstrap(self):
        self.loop = asyncio.new_event_loop()
        self.task = self.loop.create_task(self.target(*self.args, **self.kwargs))
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            pass
        finally:
            tasks = asyncio.all_tasks(self.loop)
            for task in tasks:
                if not task.cancelled():
                    self.loop.call_soon_threadsafe(task.cancel)
            tasks = asyncio.gather(*tasks, return_exceptions=True)
            tasks = asyncio.wait_for(tasks, self.cleanup_timeout)
            self.loop.run_until_complete(tasks)
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.stop()
            self.loop.close()

    def run(self):
        if hasattr(self, 'loop') and self.loop.is_running():
            raise OSError('AsyncioThread is already running.')
        super().run()

    def stop(self):
        if hasattr(self, 'loop') and hasattr(self, 'task'):
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.task.cancel)

r"""
Runtime structured logging.

Example:
    The command-line tool ingests records from standard input to pretty-print
    them::

        $ echo '{
        >   "name": "runtime.monitoring",
        >   "level": 30,
        >   "pid": 460,
        >   "time": "Mon Apr 10 20:26:26 2017",
        >   "message": "Logging OK",
        >   "readings": [1.1, 1.2, 1.3],
        >   "context": {
        >     "mapping": {
        >       "083940": 129384
        >     }
        >   }
        > }' | tr '\n' ' ' | python -m runtime.monitoring

    This gives the following output::

        [Mon Apr 10 20:26:26 2017] WARN runtime.monitoring: Logging OK (pid=460)
          {
            "readings": [
              1.1,
              1.2,
              1.3
            ],
            "mappings": {
              "083940": 129384
            }
          }
"""

__all__ = ['initialize', 'make_logger', 'shutdown', 'make_colorizer', 'format_record']


from enum import IntEnum
import functools
import logging
import json
import platform
import sys
from typing import Callable, Tuple
import click

def wrap_log_method(name: str) -> Callable:
    """ Make a decorator that will wrap a logging method. """
    def wrapper(cls):
        @functools.wraps(getattr(cls, name))
        def log(self, *args, **context):
            method = getattr(super(cls, self), name)
            return method(*args, extra={'context': json.dumps(context)})
        setattr(cls, name, log)
        return cls
    return wrapper

@wrap_log_method('debug')
@wrap_log_method('info')
@wrap_log_method('warning')
@wrap_log_method('error')
@wrap_log_method('critical')
@wrap_log_method('exception')
@wrap_log_method('log')
class RuntimeLogger(logging.getLoggerClass()):
    """
    A logger that supports keyword arguments providing context.
    """


class RuntimeFormatter(logging.Formatter):
    REQUIRED_ATTRS = frozenset({'time', 'level', 'name', 'message', 'context'})
    DEFAULT_ATTRS = REQUIRED_ATTRS | frozenset({'pid', 'tid', 'host'})
    TEMPLATE = {'name': '"%(name)s"', 'time': '"%(asctime)s"',
                'host': f'"{platform.node()}"', 'message': '"%(message)s"',
                'level': '%(levelno)s', 'level_name': '"%(levelname)s"',
                'pid': '%(process)d', 'process_name': '"%(processName)s"',
                'tid': '%(thread)d', 'thread_name': '"%(threadName)s"',
                'module': '"%(module)s"', 'func': '"%(funcName)s"',
                'path': '"%(pathname)s"', 'lineno': '%(lineno)d',
                'context': '%(context)s'}

    def __init__(self, attrs: frozenset = None):
        self.attrs = (attrs or self.DEFAULT_ATTRS) | self.REQUIRED_ATTRS
        pairs = (f'"{attr}": {value}' for attr, value in self.TEMPLATE.items()
                 if attr in self.attrs)
        fmt = '{' + ', '.join(pairs) + '}'
        super().__init__(fmt)

    def formatException(self, exc_info):
        return ''  # TODO

    def format(self, record):
        record.msg = str(record.msg).replace('"', r'\"').replace('\n', '')
        if not hasattr(record, 'context'):
            record.context = {}
        return super().format(record)


def initialize(level: str):
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RuntimeFormatter())
    root_logger.addHandler(handler)
    root_logger.debug('Initialized root logger handler.')


def make_logger(name: str) -> RuntimeLogger:
    if logging.getLoggerClass() is not RuntimeLogger:
        logging.setLoggerClass(RuntimeLogger)
    logger = logging.getLogger(name)
    logger.propagate = True
    logger.debug('Initialized logger.')
    return logger


def terminate():
    logging.shutdown()


ESCAPE = '\x1b['

class ConsoleCode(IntEnum):
    """
    See `man console_codes` for more information.
    """
    RESET = 0
    BOLD, HALF, NORMAL = 1, 2, 22  # Intensity
    UNDERLINE_ON, UNDERLINE_OFF = 4, 24
    BLINK_ON, BLINK_OFF = 5, 25
    BLACK_FG, BLACK_BG = 30, 40
    RED_FG, RED_BG = 31, 41
    GREEN_FG, GREEN_BG = 32, 42
    BROWN_FG, BROWN_BG = 33, 43
    BLUE_FG, BLUE_BG = 34, 44
    MAGENTA_FG, MAGENTA_BG = 35, 45
    CYAN_FG, CYAN_BG = 36, 46
    WHITE_FG, WHITE_BG = 37, 47


def make_console_codes(*codes: ConsoleCode) -> str:
    return f'{ESCAPE}{";".join(str(code.value) for code in codes)}m'


def make_colorizer(use_color: bool) -> Callable[[str, ConsoleCode, bool], str]:
    if use_color:
        def colorize(message, color, bold=True):
            codes = ((color,) if color else ())
            codes += ((ConsoleCode.BOLD,) if bold else ())
            return (f'{make_console_codes(*codes)}{message}'
                    f'{make_console_codes(ConsoleCode.RESET)}')
        return colorize
    return lambda message, color, bold=True: message


def separate_optional_attrs(record: dict) -> Tuple[dict, dict]:
    primitives, objs = {}, {}
    for attr, value in record.items():
        if attr not in RuntimeFormatter.REQUIRED_ATTRS:
            if isinstance(value, (dict, list)):
                objs[attr] = record[attr]
            else:
                primitives[attr] = record[attr]
    return primitives, objs


def format_primitives(primitives: dict) -> str:
    """
    Example:

        >>> print(format_primitives({"a": "b"}))
        a='b'
        >>> print(format_primitives({"a": 1.2}))
        a=1.2
    """
    return ', '.join(f'{key}={repr(value)}' for key, value in primitives.items())


def format_objs(objs: dict, indent: int) -> str:
    """
    Example:

        >>> print(format_objs({"mapping": {"123": 456}}, 2))
          {
            "mapping": {
              "123": 456
            }
          }
    """
    lines = json.dumps(objs, indent=indent).split('\n')
    return '\n'.join(indent*' ' + line for line in lines)


def format_record(record: dict, options: dict, colorize: Callable) -> str:
    formatted_levels = {
        logging.DEBUG: colorize('DEBUG', ConsoleCode.WHITE_FG),
        logging.INFO: colorize('INFO', ConsoleCode.CYAN_FG, bold=False),
        logging.WARNING: colorize('WARN', ConsoleCode.MAGENTA_FG, bold=False),
        logging.ERROR: colorize('ERROR', ConsoleCode.BROWN_FG),
        logging.CRITICAL: colorize('CRIT', ConsoleCode.RED_FG),
    }

    level = record['level']
    components = [
        '[' + record['time'] + ']',
        formatted_levels.get(level, '{:>5}'.format(level)),
        record['name'] + ':',
        colorize(record['message'], ConsoleCode.CYAN_FG, bold=False),
    ]

    record.update(record['context'])
    primitives, objs = separate_optional_attrs(record)
    if primitives:
        components.append('(' + format_primitives(primitives) + ')')
    message = ' '.join(components)
    if objs:
        message += '\n' + format_objs(objs, options.get('indent', 2))
    return message


@click.command()
@click.option('--color/--no-color', default=True, help='Print with colors.')
@click.option('--indent', default=2, help='Indentation level (spaces).',
              show_default=True)
def cli(**options):
    """ TODO """
    colorize = make_colorizer(options['color'])
    for line in sys.stdin:
        line = line.strip()
        try:
            record = json.loads(line)
            print(format_record(record, options, colorize))
        except (json.JSONDecodeError, KeyError):
            print(f'Fatal: "{line}" is not a valid log record.')
            sys.exit(1)


if __name__ == '__main__':
    cli()

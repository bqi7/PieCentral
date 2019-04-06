"""
runtime.executor
"""

import asyncio
import runtime.journal

LOGGER = runtime.journal.make_logger(__name__)


def blank_function():
    """ Blank function stub for replacing bad functions in student code. """


async def blank_coroutine():
    """ Blank coroutine function stub for replacing bad functions in student code. """


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

    # def patch(self, module):
    #     """ Monkey-patch student code. """
    #     module.Robot = Robot
    #     for name, default_function in self.required_functions.items():
    #         if not hasattr(module, name):
    #             setattr(module, name, default_function)
    #
    # def validate(self, module):
    #     for name, default_function in self.required_functions.items():
    #         function = getattr(module, name)
    #         if not inspect.isfunction(function):
    #             raise RuntimeExecutorException(f'"{name}" is not a function.',
    #                                            function_name=name)
    #         expects_coro = inspect.iscoroutinefunction(default_function)
    #         actually_coro = inspect.iscoroutinefunction(function)
    #         if expects_coro and not actually_coro:
    #             raise RuntimeExecutorException(
    #                 f'"{name}" is not a coroutine function when it should be.',
    #                 function_name=name,
    #             )
    #         if not expects_coro and actually_coro:
    #             raise RuntimeExecutorException(
    #                 f'"{name}" is a corountine function when it should not be.',
    #                 function_name=name,
    #             )
    #         if inspect.signature(default_function) != inspect.signature(function):
    #             raise RuntimeExecutorException(f'"{name}" signature is not correct.',
    #                                            function_name=name)
    #
    # def reload(self):
    #     if not hasattr(self, 'module'):
    #         self.module = importlib.import_module(self.module_name)
    #     else:
    #         self.module = importlib.reload(self.module)
    #     self.patch(self.module)
    #     self.validate(self.module)
    #     # except Exception as exc:
    #     #     LOGGER.error('Unable to import student code module.',
    #     #                  msg=str(exc), type=type(exc).__name__)
    #     # else:
    #     #     LOGGER.debug('Imported student code module.')


async def start():
    pass

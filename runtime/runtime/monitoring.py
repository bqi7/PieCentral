from typing import Callable, Tuple, Dict
import aioprocessing
import runtime.logging

LOGGER = runtime.logger.make_logger(__name__)


class SubprocessMonitor(UserDict):
    """
    A monitor for managing multiple subprocesses, restarting them when they fail.
    """
    def __init__(self, max_respawns: int, respawn_reset: float):
        self.max_respawns, self.respawn_reset = max_respawns, respawn_reset
        self.subprocesses = {}
        super().__init__()

    def add(self, name: str, target: Callable, args: Tuple = None, kwargs: Dict = None):
        """ Register a subprocess this monitor should watch. """
        self[name] = (target, args or (), kwargs or {})

    async def start_process(self, name):
        """ Starts a long-term daemon process. """
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
        """ Run a daemon process indefinitely, restarting it if necessary. """
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

    async def log_statistics(self, period: float):
        while True:
            await asyncio.sleep(period)

    async def spin(self):
        """ Run multiple daemon processes indefinitely.  """
        monitors = [self.monitor_process(name) for name in self]
        await asyncio.gather(*monitors, self.log_statistics())

    def terminate(self, timeout=None):
        """
        Terminate all subprocesses this monitor is managing.

        First, a ``SIGTERM`` signal is sent to each process to give them a
        chance to shutdown gracefully. Upon a timeout, this subprocess is
        forcefully killed with ``SIGKILL``. Subprocesses may be terminated in
        any order.
        """
        for name, subprocess in self.subprocesses.items():
            if subprocess.is_alive():
                subprocess.terminate()
                LOGGER.warn('Sent SIGTERM to subprocess.', subprocess_name=name)
                subprocess.join(timeout)
                time.sleep(0.05)  # Wait for "exitcode" to set.
                if subprocess.is_alive():
                    subprocess.kill()
                    LOGGER.critical('Sent SIGKILL to subprocess. '
                                    'Unable to shut down gracefully.',
                                    subprocess_name=name)


def bootstrap(options):
    """ Initializes subprocesses and catches any fatal exceptions. """
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

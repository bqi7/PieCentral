"""
The runtime command-line interface.
"""

import os
import platform
import click
from runtime import __version__
import runtime.journal
import runtime.monitoring
from runtime.util import read_conf_file, RuntimeBaseException


def get_module_path(filename: str) -> str:
    """ Return a path relative to the module's top-level directory. """
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_dir, filename)


def override_options(options: dict):
    """ Override options with mandatory defaults. """
    if 'linux' not in platform.system().casefold():
        options['poll'] = True


@click.command()
@click.option('-r', '--max-respawns', default=3,
              help='Number of times to attempt to respawn a failing subprocess.')
@click.option('--fail-reset', default=120,
              help='Seconds before the subprocess failure counter is reset.')
@click.option('--terminate-timeout', default=5,
              help='Timeout in seconds for subprocesses to terminate.')
@click.option('-f', '--student-freq', default=20,
              help='Student code execution frequency in Hertz.')
@click.option('--host', default='127.0.0.1', help='Hostname to bind servers to.')
@click.option('--tcp', default=1234, help='TCP port.')
@click.option('--udp-send', default=1235, help='UDP send port.')
@click.option('--udp-recv', default=1236, help='UDP receive port.')
@click.option('-p', '--poll', is_flag=True, help='Poll for hotplugged sensors. '
              'By default, sensors are detected asynchronously with udev. '
              'For non-Linux platforms without udev, this flag is always set.')
@click.option('--poll-period', default=0.04, help='Hotplug polling period.')
@click.option('--monitor-period', default=60, help='Monitor logging period.')
@click.option('-l', '--log-level', default='INFO', help='Lowest visible log level.',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']))
@click.option('-d', '--data-schema', default=get_module_path('datasources.yaml'),
              help='Path to data source schema.', type=click.Path(exists=True, dir_okay=False))
@click.option('--decoders', default=2, help='Number of decoder threads.')
@click.option('--encoders', default=2, help='Number of encoder threads.')
@click.option('-s', '--student-code', default=get_module_path('studentcode.py'),
              type=click.Path(exists=True, dir_okay=False),
              help='Path to student code module.')
@click.option('-c', '--config', default=get_module_path('config.yaml'),
              type=click.Path(dir_okay=False),
              help='Path to configuration file. Overrides any command line options.')
@click.option('-v', '--version', is_flag=True, help='Show the runtime version and exit.')
def cli(version, **options):
    """
    The PiE runtime daemon manages the state of a robot, controls student code
    execution, and communicates with Dawn and Shepherd.
    """
    if version:
        print('.'.join(map(str, __version__)))
    else:
        override_options(options)
        try:
            options.update(read_conf_file(options['config']))
        except (FileNotFoundError, RuntimeBaseException):
            pass
        runtime.journal.initialize(options['log_level'])
        runtime.monitoring.bootstrap(options)


if __name__ == '__main__':
    cli()

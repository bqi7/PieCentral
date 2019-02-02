"""
The runtime command-line interface.
"""

import os
import click
from runtime import __version__
from runtime.control import bootstrap


def get_module_path(filename):
    module_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_dir, filename)


@click.command()
@click.option('-r', '--max-respawns', default=3,
              help='Number of times to attempt to respawn a child process.')
@click.option('-t', '--student-time', default=1.0,
              help='Student code timeout in seconds.')
@click.option('-f', '--student-freq', default=20,
              help='Number of times to execute student code per second.')
@click.option('--tcp', default=1234, help='TCP port.')
@click.option('--udp-send', default=1235, help='UDP send port.')
@click.option('--udp-recv', default=1236, help='UDP receive port.')
@click.option('-p', '--poll', is_flag=True, help='Poll for hotplugged sensors. '
              'By default, sensors are detected asynchronously with udev. '
              'For non-Linux platforms without udev, this flag is always set.')
@click.option('--poll-period', default=0.04, help='Hotplug polling period.')
@click.option('-l', '--log-level', default='INFO', help='Lowest visible log level.',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']))
@click.option('-d', '--device-schema', default=get_module_path('devices.yaml'),
              help='Path to device schema.',
              type=click.Path(exists=True, dir_okay=False))
@click.option('--decoders', default=2, help='Number of decoder threads.')
@click.option('--encoders', default=2, help='Number of encoder threads.')
@click.option('-v', '--version', is_flag=True,
              help='Show the runtime version and exit.')
@click.argument('student-code', default=get_module_path('studentcode.py'),
                type=click.Path(exists=True, dir_okay=False))
def cli(version, **options):
    """
    The PiE runtime daemon manages the state of a robot, controls student code
    execution, and communicates with Dawn and Shepherd.
    """
    if version:
        print('.'.join(map(str, __version__)))
    else:
        bootstrap(options)


if __name__ == '__main__':
    cli()

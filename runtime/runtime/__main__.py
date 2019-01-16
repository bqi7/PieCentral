"""
The runtime command-line interface.
"""

import click
from runtime import __version__
from runtime.control import bootstrap


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
@click.option('-p', is_flag=True, help='Poll for hotplugged sensors. '
              'By default, sensors are detected asynchronously with udev. '
              'For non-Linux platforms without udev, this flag is always set.')
@click.option('--hotplug-poll', default=0.04, help='Hotplug polling period.')
@click.option('-l', '--log-level', default='INFO', help='Lowest visible log level.',
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']))
@click.option('-v', '--version', is_flag=True,
              help='Show the runtime version and exit.')
@click.argument('student-code', type=click.Path(exists=True, dir_okay=False))
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

#!/usr/bin/env python3

import sys
import click

try:
    sys.path.append('..')
    from runtime.__main__ import cli as runtime_cli
except ImportError:
    print('Unable to import runtime.')
    print('Ensure runtime is invoked from "runtime/tests".')
    exit(1)


@click.command()
@click.pass_context
def cli(ctx):
    ctx.invoke(runtime_cli)


if __name__ == '__main__':
    cli()

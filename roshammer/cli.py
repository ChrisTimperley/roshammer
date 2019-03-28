# -*- coding: utf-8 -*-
"""
This module provides a simple command-line interface to ROSHammer.
"""
import click

from .ui import ROSHammerUI


@click.group()
def cli():
    pass


@cli.command()
@click.argument('image', type=str)
def fuzz(image: str) -> None:
    """Fuzzes a given Docker IMAGE."""
    click.echo(f"fuzzing {image}")
    ui = ROSHammerUI(image)
    ui.run()


def main():
    cli()

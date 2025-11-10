"""Backoffice CLI entry point."""

from __future__ import annotations

import sys

import click

from .commands.channels import channels
from .commands.digest import digest


@click.group()
@click.version_option(package_name="ai-challenge")
def cli() -> None:
    """AI Challenge backoffice CLI."""


# Register nested command groups
cli.add_command(channels)
cli.add_command(digest)


def main(argv: list[str] | None = None) -> None:
    """Execute CLI entry point."""
    cli(prog_name="ai-backoffice", args=argv)


if __name__ == "__main__":
    main(sys.argv[1:])


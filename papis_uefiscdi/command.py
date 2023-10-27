# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import click

import papis.cli


@click.command()
@click.help_option("--help", "-h")
@papis.cli.query_argument()
def cli(query: str) -> None:
    """Manage UEFISCDI journal impact factors and other indicators."""

#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Command line entry — the FastAPI counterpart of the legacy ``flask`` CLI.

The legacy side registered every click command found under ``api/commands``
on the flask CLI (see ``api/app.py::register_commands``), so docker-compose
could run ``flask db-setup``, ``flask cmdb-init-cache`` ... . Here the same
commands are exposed through a plain click group, keeping the command names
identical::

    python cli.py db-setup
    python cli.py common-check-new-columns
    python cli.py cmdb-init-cache
    python cli.py cmdb-init-acl
    python cli.py init-import-user-from-acl
    python cli.py init-department
    python cli.py cmdb-patch -v 2.4.17
"""
import importlib
import os
from inspect import getmembers

import click

HERE = os.path.abspath(os.path.dirname(__file__))
COMMANDS_DIR = os.path.join(HERE, "api", "commands")


@click.group()
def cli():
    """CMDB management commands."""


def register_commands(group):
    """Import every module under ``api/commands`` and register all click
    commands found (mirrors the legacy ``register_commands``)."""
    for root, _, files in os.walk(COMMANDS_DIR):
        for filename in sorted(files):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue
            module = importlib.import_module(
                "api.commands." + os.path.splitext(filename)[0])
            for _, obj in getmembers(module):
                if isinstance(obj, click.core.Command):
                    group.add_command(obj)


register_commands(cli)

if __name__ == "__main__":
    cli()

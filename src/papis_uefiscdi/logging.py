# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

import logging
import os


def get_logger(
    module: str,
    level: int | str = logging.INFO,
) -> logging.Logger:
    """Create a new logging for the module *module*.

    The logger is created using a :class:`rich.logging.RichHandler` for fancy
    highlighting. The ``NO_COLOR`` environment variable can be used to
    disable colors.

    If *papis* is installed, this defaults to using :func:`papis.logging.get_logger`.

    :arg module: a name for the module to create a logger for.
    :arg level: default logging level.
    """
    try:
        import papis.logging

        return papis.logging.get_logger(module)
    except ImportError:
        pass

    if isinstance(level, str):
        level = getattr(logging, level.upper())

    assert isinstance(level, int)

    name, *rest = module.split(".", maxsplit=1)
    root = logging.getLogger(name)

    if not root.handlers:
        from rich.highlighter import NullHighlighter
        from rich.logging import RichHandler

        no_color = "NO_COLOR" in os.environ
        handler = RichHandler(
            level,
            show_time=True,
            omit_repeated_times=False,
            show_level=True,
            show_path=True,
            highlighter=NullHighlighter() if no_color else None,
            markup=True,
        )

        root.addHandler(handler)

    root.setLevel(level)
    return root.getChild(rest[0]) if rest else root

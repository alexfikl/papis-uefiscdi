# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import sys
import tempfile
from typing import Any, Sequence

import papis.logging

logger = papis.logging.get_logger(__name__)


def download_document(
    url: str,
    expected_document_extension: str | None = None,
    cookies: dict[str, Any] | None = None,
) -> str | None:
    """Download a document from *url* and store it in a local file.

    :param url: the URL of a remote file.
    :param expected_document_extension: an expected file type. If *None*, then
        an extension is guessed from the file contents, but this can also fail.
    :returns: a path to a local file containing the data from *url*.
    """
    if cookies is None:
        cookies = {}

    from papis.utils import get_session

    try:
        with get_session() as session:
            response = session.get(url, cookies=cookies, allow_redirects=True)
    except Exception as exc:
        logger.error("Failed to fetch '%s'.", url, exc_info=exc)
        return None

    if not response.ok:
        logger.error(
            "Could not download document '%s'. (HTTP status: %s %d).",
            url,
            response.reason,
            response.status_code,
        )
        return None

    ext = expected_document_extension
    if ext is None:
        from papis.filetype import guess_content_extension

        ext = guess_content_extension(response.content)
        if not ext:
            logger.warning(
                "Downloaded document does not have a "
                "recognizable (binary) mimetype: '%s'.",
                response.headers["Content-Type"],
            )

    ext = f".{ext}" if ext else ""
    with tempfile.NamedTemporaryFile(mode="wb+", suffix=ext, delete=False) as f:
        f.write(response.content)

    return f.name


def run(
    cmd: Sequence[str],
    *,
    wait: bool = True,
    env: dict[str, Any] | None = None,
    cwd: str | None = None,
) -> None:
    """Run a given command with :mod:`subprocess`.

    This is a simple wrapper around :class:`subprocess.Popen` with custom
    defaults used to call Papis commands.

    :arg cmd: a sequence of arguments to run, where the first entry is expected
        to be the command name and the remaining entries its arguments.
    :param wait: if *True* wait for the process to finish, otherwise detach the
        process and return immediately.
    :param env: a mapping that defines additional environment variables for
        the child process.
    :param cwd: current working directory in which to run the command.
    """

    cmd = list(cmd)
    if not cmd:
        return

    if cwd:
        cwd = os.path.expanduser(cwd)
        logger.debug("Changing directory to '%s'.", cwd)

    logger.debug("Running command: '%s'.", cmd)

    # NOTE: detached processes do not fail properly when the command does not
    # exist, so we check for it manually here
    import shutil

    if not shutil.which(cmd[0]):
        raise FileNotFoundError(f"Command not found: '{cmd[0]}'")

    import subprocess  # noqa: S404

    if wait:
        logger.debug("Waiting for process to finish.")
        subprocess.call(cmd, shell=False, cwd=cwd, env=env)  # noqa: S603
    else:
        # NOTE: detach process so that the terminal can be closed without also
        # closing the 'opentool' itself with the open document
        platform_kwargs: dict[str, Any] = {}
        if sys.platform == "win32":
            platform_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # NOTE: 'close_fds' is not supported on windows with stdout/stderr
            # https://docs.python.org/3/library/subprocess.html#subprocess.Popen
            platform_kwargs["close_fds"] = True
            cmd.insert(0, "nohup")

        logger.debug("Not waiting for process to finish.")
        subprocess.Popen(
            cmd,
            shell=False,  # noqa: S603
            cwd=cwd,
            env=env,
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **platform_kwargs,
        )

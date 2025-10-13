# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import pathlib
import sys
import tempfile
from typing import TYPE_CHECKING, Any

from papis_uefiscdi.logging import get_logger

# FIXME: remove when we can depend on Papis >=0.15
try:
    from papis.strings import FormatPattern  # type: ignore[attr-defined,unused-ignore]
except ImportError:
    from typing import NamedTuple

    class FormatPattern(NamedTuple):  # type: ignore[no-redef,unused-ignore]
        formatter: str | None
        pattern: str

        def __str__(self) -> str:
            return self.pattern

        def __repr__(self) -> str:
            return repr(self.pattern)

        def __bool__(self) -> bool:
            return bool(self.pattern)

        def __eq__(self, other: Any) -> bool:
            if isinstance(other, str):
                return self.pattern == other
            elif isinstance(other, FormatPattern):
                return bool(self.pattern == other.pattern)
            else:
                return False

        def __hash__(self) -> int:
            return hash(self.pattern)


if TYPE_CHECKING:
    from collections.abc import Sequence

    import requests

log = get_logger(__name__)

__all__ = (
    "FormatPattern",
    "download_document",
    "get_session",
    "run",
)


def get_session() -> requests.Session:
    try:
        from papis.utils import get_session

        return get_session()
    except ImportError:
        import requests

        return requests.Session()


def download_document(
    url: str,
    *,
    expected_document_extension: str | None = None,
    cookies: dict[str, Any] | None = None,
    filename: str | None = None,
) -> pathlib.Path | None:
    """Download a document from *url* and store it in a local file.

    An appropriate filename is deduced from the HTTP response in most cases.
    If this is not possible, a temporary file is created instead. To ensure that
    the desired filename is chosen, provide the *filename* argument instead.

    :param url: the URL of a remote file.
    :param expected_document_extension: an expected file extension. If *None*, then
        an extension is guessed from the file contents or from the *filename*.
    :param filename: a file name for the document, regardless of the given URL and
        extension.

    :returns: an absolute path to a local file containing the data from *url*.
    """
    if cookies is None:
        cookies = {}

    try:
        with get_session() as session:
            response = session.get(url, cookies=cookies, allow_redirects=True)
    except Exception as exc:
        log.error("Failed to fetch '%s'.", url, exc_info=exc)
        return None

    if not response.ok:
        log.error(
            "Could not download document '%s'. (HTTP status: %s %d).",
            url,
            response.reason,
            response.status_code,
        )
        return None

    # NOTE: we can guess the filename from the response headers
    #   Content-Disposition: inline; filename="some_file_name.ext"
    #   Content-Disposition: attachment; filename="some_file_name.ext"
    key = "Content-Disposition"
    if not filename and key in response.headers:
        from email.message import EmailMessage

        msg = EmailMessage()
        msg[key] = response.headers[key]
        filename = msg.get_filename()

    key = "Content-Type"
    if not filename and key in response.headers:
        from email.message import EmailMessage

        msg = EmailMessage()
        msg[key] = response.headers[key]

        from mimetypes import guess_extension

        ext = guess_extension(msg.get_content_type())

        from urllib.parse import urlsplit

        result = urlsplit(url)
        if result.path.strip("/"):
            basename = os.path.basename(result.path)
        else:
            basename = result.netloc
        filename = f"{basename}{ext}"

    # try go guess an extension
    ext = expected_document_extension
    if ext is None:
        try:
            if filename is None:
                from papis.filetype import guess_content_extension

                ext = guess_content_extension(response.content)
                ext = f".{ext}"
            else:
                _, ext = os.path.splitext(filename)
        except ImportError:
            ext = ".txt"
    else:  # noqa: PLR5501
        if not ext.startswith("."):
            ext = f".{ext}"

    # write out the file contents
    if filename:
        root, _ = os.path.splitext(os.path.basename(filename))
        outfile = os.path.join(tempfile.gettempdir(), f"{root}{ext}")

        with open(outfile, mode="wb") as f:
            f.write(response.content)
    else:
        with tempfile.NamedTemporaryFile(
            mode="wb+", suffix=f"{ext}", delete=False
        ) as f:
            f.write(response.content)
            outfile = f.name

    return pathlib.Path(outfile)


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
        log.debug("Changing directory to '%s'.", cwd)

    log.debug("Running command: '%s'.", cmd)

    # NOTE: detached processes do not fail properly when the command does not
    # exist, so we check for it manually here
    import shutil

    if not shutil.which(cmd[0]):
        raise FileNotFoundError(f"Command not found: '{cmd[0]}'")

    import subprocess  # noqa: S404

    if wait:
        log.debug("Waiting for process to finish.")
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

        log.debug("Not waiting for process to finish.")
        subprocess.Popen(  # noqa: S603
            cmd,
            shell=False,
            cwd=cwd,
            env=env,
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **platform_kwargs,
        )

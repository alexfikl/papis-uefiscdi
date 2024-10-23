# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pypdf

from papis_uefiscdi.config import INDEX_ID_TO_NAME
from papis_uefiscdi.logging import get_logger
from papis_uefiscdi.uefiscdi import Entry

log = get_logger(__name__)


# {{{ extract_text


@dataclass(frozen=True)
class PositionedText:
    text: str
    x: float
    y: float


def extract_text(page: pypdf.PageObject) -> list[PositionedText]:
    """Extracts text from a PDF page."""
    lines = []

    def visit_text(
        text: str,
        cm_matrix: list[float],
        tm_matrix: list[float],
        font_dict: dict[str, Any],
        font_size: float,
    ) -> None:
        text = text.strip()
        if not text:
            return

        lines.append(PositionedText(text, tm_matrix[4], tm_matrix[5]))

    page.extract_text(visitor_text=visit_text)
    return lines


# }}}


# {{{ parse_zone_entry_2024

_ISSN_RE = re.compile(r"\d{4}-\d{3}[\dxX]|N/A")
_LINE_2024_RE = re.compile(
    r"([\(\)\w &\-]+?)\s?"  # journal name
    r"(\d{4}-\d{3}[\dxX]|N/A) (\d{4}-\d{3}[\dxX]|N/A)\s?"  # issn | eissn
    r"([\w &,\-]+?)\s?(AHCI|ESCI|SCIE|SSCI) "  # category | index
    "(Q[1234]|N/A) (Q[1234]|N/A)"  # JIF | AIS quartile
)

# NOTE: the case should match the PDF here
HEADER_NAMES_2024 = (
    "Journal name",
    "ISSN",
    "eISSN",
    "Category",
    "Edition",
    "JIF Quartile",
    "AIS Quartile",
)


def parse_2024_zone_entries(lines: list[str], quartile: int = 0) -> list[Entry]:
    """Row format is given as

    JOURNAL | ISSN | EISSN | WOS_CATEGORY | INDEX | JIF QUARTILE | AIS QUARTILE

    This is not always what we get in *line*, since it some rows are spread over
    multiple lines.
    """
    from titlecase import titlecase

    if quartile not in {0, 1}:
        raise ValueError(f"Unsupported 'quartile': {quartile}")

    def row2entry(row: tuple[str, ...]) -> Entry:
        return Entry(
            category=titlecase(row[3].strip()),
            index=row[4].upper(),
            name=titlecase(row[0].strip()),
            issn=None if row[1] == "N/A" else row[1].upper(),
            eissn=None if row[2] == "N/A" else row[2].upper(),
            quartile=None if row[5 + quartile] == "N/A" else row[5 + quartile].upper(),
            position=-1,
            score=None,
        )

    # find header location (and hope it's not glued to anything)
    offset = 0
    for i, line in enumerate(lines):
        if all(name in line for name in HEADER_NAMES_2024):
            offset = i + 1
            break

    entries = []
    row = ""

    for _, line in enumerate(lines[offset:-1]):
        row = f"{row} {line}"

        new_entries = []
        for match in _LINE_2024_RE.finditer(row):
            new_entries.append(row2entry(match.groups()))

        if new_entries:
            row = ""
            entries.extend(new_entries)

    if not entries:
        raise RuntimeError("No journals found on page")

    return entries


# }}}


# {{{ parse_zone_entry_2023

_SUPPORTED_QUARTILES = {"Q1", "Q2", "Q3", "Q4", "N/A"}


def parse_2023_zone_entry(before: tuple[str, str], current: str) -> Entry | None:
    """Row format is given as

            WOS_CATEGORY - INDEX | JOURNAL | ISSN | EISSN | QUARTILE | POSITION

        where

        * *INDEX* is a four letter citation index database name.
        * *ISSN* is has a format of ``XXXX-XXXX`` and can also be *N/A*.
    * *EISSN* is the same as *ISSN*.
        * *QUARTILE* is one of *Q1, Q2, Q3, Q4* but can also be *N/A*.
        * *POSITION* is a single integer.
    """
    if " " not in current:
        return None

    rest, position = current.rsplit(" ", maxsplit=1)

    if not position.isdigit():
        return None

    rest, quartile = rest.rsplit(" ", maxsplit=1)
    quartile = quartile.upper()

    if quartile not in _SUPPORTED_QUARTILES:
        return None

    rest, eissn = rest.rsplit(" ", maxsplit=1)
    eissn = eissn.strip().upper()

    if not _ISSN_RE.match(eissn):
        return None

    rest, issn = rest.rsplit(" ", maxsplit=1)
    issn = issn.strip().upper()

    if not _ISSN_RE.match(issn):
        return None

    if " - " not in rest:
        # NOTE: some entries are multiline, so we try to guess
        # * add the -1 line and see if it contains a -
        # * add the -2 line too if it does not end in a digit (for the position)
        rest = f"{before[1]} {rest}"
        if " - " not in rest or (not before[0][-1].isdigit() and before[0][0] != "Q"):
            rest = f"{before[0]} {rest}"

    # NOTE: we're now left with WOS_CATEGORY - INDEX JOURNAL
    category, rest = rest.split(" - ", maxsplit=1)
    index = rest[:4]
    journal = rest[4:]

    if index not in INDEX_ID_TO_NAME:
        return None

    from titlecase import titlecase

    return Entry(
        category=titlecase(category.strip()),
        index=index.upper(),
        name=titlecase(journal.strip()),
        issn=None if issn == "N/A" else issn,
        eissn=None if eissn == "N/A" else eissn,
        quartile=None if quartile == "N/A" else quartile,
        position=int(position),
        score=None,
    )


# }}}

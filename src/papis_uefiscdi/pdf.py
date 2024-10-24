# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pypdf

from papis_uefiscdi.logging import get_logger
from papis_uefiscdi.uefiscdi import Entry

log = get_logger(__name__)


# {{{ extract_text


@dataclass(frozen=True)
class PositionedText:
    text: str
    """Text extracted from the PDF."""
    x: float
    """Coordinate of the start of the text."""
    y: float
    """Coordinate of the start of the text."""


def extract_text(page: pypdf.PageObject) -> list[PositionedText]:
    """Extracts text from a PDF page.

    Note that this is very similar to :meth:`pypdf.PageObject.extract_text`
    (it just uses ``visitor_text``).

    However, it seems like :mod:`pypdf` merges some text fragments in a smarter way
    sometimes. This is not always wanted and this function can be used in those
    cases.
    """
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


# {{{ parse_2024_quartile_zone_entries

_ISSN_RE = re.compile(r"\d{4}-\d{3}[\dxX]|N/A")
_LINE_2024_RE = re.compile(
    r"([\(\)\w &\-]+?)\s?"  # journal name
    r"(\d{4}-\d{3}[\dxX]|N/A) (\d{4}-\d{3}[\dxX]|N/A)\s?"  # issn | eissn
    r"([\w &,\-]+?)\s?(AHCI|ESCI|SCIE|SSCI) "  # category | index
    r"(Q[1234]|N/A) (Q[1234]|N/A)"  # JIF | AIS quartile
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


def parse_2024_quartile_zone_entries(lines: list[str], fmt: str = "jif") -> list[Entry]:
    """Row format is given as

    JOURNAL | ISSN | EISSN | WOS_CATEGORY | INDEX | JIF QUARTILE | AIS QUARTILE

    This is not always what we get in *line*, since it some rows are spread over
    multiple lines.
    """
    from titlecase import titlecase

    if fmt not in {"ais", "jif"}:
        raise ValueError(f"Unsupported 'fmt': {fmt}")

    quartile_index = 5 if fmt == "jif" else 6

    def row2entry(group: tuple[str, ...]) -> Entry:
        group = tuple(entry.strip() for entry in group)
        return Entry(
            category=titlecase(group[3].strip()),
            index=group[4].upper(),
            name=titlecase(group[0].strip()),
            issn=None if group[1] == "N/A" else group[1].upper(),
            eissn=None if group[2] == "N/A" else group[2].upper(),
            quartile=(
                None
                if group[quartile_index] == "N/A"
                else group[quartile_index].upper()
            ),
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

    for line in lines[offset:-1]:
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


# {{{ parse_2023_quartile_zone_entries

# NOTE: the case should match the PDF here
HEADER_JIF_NAMES_2023 = (
    "Web of Science Category-Index",
    "Revista",
    "ISSN",
    "eISSN",
    "Q JIF 2022 (conform JCR iunie 2023)",
    "Loc in zona/Q JIF",
)
HEADER_AIS_NAMES_2023 = (
    "Web of Science Category-Index",
    "Revista",
    "ISSN",
    "eISSN",
    "Q AIS 2022 (conform JCR iunie 2023)",
    "Loc in zona/Q AIS",
)

_HEADER_FRAGMENTS_2023 = (
    re.compile("Web of Science Category-Index"),
    re.compile("Revista"),
    re.compile("ISSN"),
    re.compile("eISSN"),
    re.compile("Q (JIF|AIS) 2022"),
    re.compile("conform JCR"),
    re.compile("iunie 2023"),
    re.compile("Loc in zona"),
    re.compile("Q (JIF|AIS)"),
)
_LINE_2023_RE = re.compile(
    r"([\w &,\-]+) - (AHCI|ESCI|SCIE|SSCI)\s?"  # category | index
    r"([\(\)\w &\-]+?)\s?"  # journal name
    r"(\d{4}-\d{3}[\dxX]|N/A) (\d{4}-\d{3}[\dxX]|N/A)\s?"  # issn | eissn
    r"(Q[1234]|N/A) (\d+)"  # quartile | position
)


def parse_2023_quartile_zone_entries(lines: list[str], fmt: str = "jif") -> list[Entry]:
    """Row format is given as

    WOS_CATEGORY - INDEX | JOURNAL | ISSN | EISSN | QUARTILE | POSITION

    This is not always what we get in *line*, since it some rows are spread over
    multiple lines.
    """
    from titlecase import titlecase

    if fmt not in {"ais", "jif"}:
        raise ValueError(f"Unsupported 'fmt': {fmt}")

    def row2entry(group: tuple[str, ...]) -> Entry:
        group = tuple(entry.strip() for entry in group)
        return Entry(
            category=titlecase(group[0]),
            index=group[1].upper(),
            name=titlecase(group[2]),
            issn=None if group[3] == "N/A" else group[3].upper(),
            eissn=None if group[4] == "N/A" else group[4].upper(),
            quartile=(None if group[5] == "N/A" else group[5].upper()),
            position=int(group[6]),
            score=None,
        )

    # find header location (and hope it's not glued to anything)
    offset = 0
    is_on_line = is_on_prev_line = False
    for i, line in enumerate(lines):
        is_on_line = any(regex.search(line) for regex in _HEADER_FRAGMENTS_2023)
        if not is_on_line and is_on_prev_line:
            offset = i
            break

        is_on_prev_line = is_on_line

    entries = []
    row = ""

    for line in lines[offset:-1]:
        row = f"{row} {line}"

        new_entries = []
        for match in _LINE_2023_RE.finditer(row):
            new_entries.append(row2entry(match.groups()))

        if new_entries:
            row = ""
            entries.extend(new_entries)

    if not entries:
        raise RuntimeError("No journals found on page")

    return entries


# }}}

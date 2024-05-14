# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import re
from typing import Iterator, TypedDict

import papis.logging

logger = papis.logging.get_logger(__name__)


# {{{ utils

INDEX_ID_TO_NAME = {
    "AHCI": "Arts Humanities Citation Index",
    "SCIE": "Science Citation Index Expanded",
    "SSCI": "Social Sciences Citation Index",
}
"""A mapping of indexes (as they appear in the UEFISCDI databases) to their
full names.
"""


class Entry(TypedDict):
    """Journal entry information from the UEFISCDI databases.

    This entry corresponds to the Web of Science Core Collection data for
    Journal Impact Factors (JIF) and Article Influence Scores (AIS) gathered
    by the UEFISCDI.
    """

    category: str | None
    """Web of Science category for this journal."""
    index: str | None
    """Citation index identifier (see :data:`INDEX_ID_TO_NAME`)."""

    name: str | None
    """Name of the journal in the provided format."""
    issn: str | None
    """International Standard Serial Number (ISSN) assigned to the journal."""
    eissn: str | None
    """Electronic ISSN assigned to the journal."""
    quartile: str | None
    """Quartile to which the journal belongs to, in the ``QX`` format."""
    position: int | None
    """Position in its quartile based on the Journal Impact factor (JIF)
    or the Article Influence Score (AIS).
    """
    score: float | None
    """Numerical score of the journal."""


def stringify(entry: Entry, database: str) -> str:
    name = entry["name"]
    category = entry["category"] or "unknown category"

    score = entry["score"]
    quartile = entry["quartile"]
    if score is not None:
        value = str(score)
    elif quartile is not None:
        value = str(quartile)
    else:
        value = "N/A"

    return f"[{database.upper()} {value}] {name} ({category})"


# }}}

# {{{ Journal Impact Factor


_SUPPORTED_VERSIONS = {2023}

_SUPPORTED_QUARTILES = {"Q1", "Q2", "Q3", "Q4", "N/A"}

_ISSN_RE = re.compile(r"\w{4}-\w{4}|N/A")


def window(iterable: list[str]) -> Iterator[tuple[tuple[str, str], str]]:
    for i, x in enumerate(iterable[2:]):
        yield (iterable[i], iterable[i + 1]), x


def _parse_jif_zone_entry_2023(before: tuple[str, str], current: str) -> Entry | None:
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


def parse_uefiscdi_journal_impact_factor(
    filename: str | pathlib.Path, *, version: int = 2023
) -> list[Entry]:
    """Parse Journal Impact Factor (JIF) ranking data from the given filename.

    Some versions of the UEFISCDI database are given in PDF format. Table
    parsing from PDFs is notoriously difficult, so this procedure is not
    exact. Additional heuristics and edge cases will be added in time.

    :returns: a :class:`list` of journals ordered by index, category, quartile
        and the position in quartile.
    """
    filename = pathlib.Path(filename)
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    import pypdf

    with open(filename, "rb") as f:
        pdf = pypdf.PdfReader(f)

        if version == 2023:
            parse = _parse_jif_zone_entry_2023
        else:
            raise AssertionError

        results: list[Entry] = []
        for i, p in enumerate(pdf.pages):
            lines = [line.strip() for line in p.extract_text().split("\n")]

            journals = [
                journal
                for before, current in window(lines)
                if (journal := parse(before, current)) is not None
            ]
            logger.debug(
                "Parsing page %4d / %4d. Extracted %d journals for a total of %d",
                i + 1,
                len(pdf.pages),
                len(journals),
                len(results) + len(journals),
            )
            results.extend(journals)

        logger.info("Extracted %d journal from %d pages", len(results), len(pdf.pages))

    return sorted(
        results,
        key=lambda j: (
            j["index"],
            j["category"],
            j["quartile"] if j["quartile"] is not None else "Q9",
            j["position"],
        ),
    )


# }}}

# {{{ Article Influence Score

_parse_ais_zone_entry_2023 = _parse_jif_zone_entry_2023


def parse_uefiscdi_article_influence_score(
    filename: str | pathlib.Path, *, version: int = 2023
) -> list[Entry]:
    """Parse Article Influence Score (AIS) ranking data from the given filename.

    Some versions of the UEFISCDI database are given in PDF format. Table
    parsing from PDFs is notoriously difficult, so this procedure is not
    exact. Additional heuristics and edge cases will be added in time.

    :returns: a :class:`list` of journals ordered by index, category, quartile
        and the position in quartile.
    """
    filename = pathlib.Path(filename)
    if not filename.exists():
        raise FileNotFoundError(filename)

    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    import pypdf

    with open(filename, "rb") as f:
        pdf = pypdf.PdfReader(f)

        if version == 2023:
            parse = _parse_ais_zone_entry_2023
        else:
            raise AssertionError

        results: list[Entry] = []
        for i, p in enumerate(pdf.pages):
            lines = [line.strip() for line in p.extract_text().split("\n")]

            journals = [
                journal
                for before, current in window(lines)
                if (journal := parse(before, current)) is not None
            ]
            logger.debug(
                "Parsing page %4d / %4d. Extracted %d journals for a total of %d",
                i + 1,
                len(pdf.pages),
                len(journals),
                len(results) + len(journals),
            )
            results.extend(journals)

        logger.info("Extracted %d journal from %d pages", len(results), len(pdf.pages))

    return sorted(
        results,
        key=lambda j: (
            j["index"],
            j["category"],
            j["quartile"] if j["quartile"] is not None else "Q9",
            j["position"],
        ),
    )


# }}}


# {{{ Article Influence Score


def _decrypt_file(filename: pathlib.Path, password: str) -> pathlib.Path:
    import tempfile

    import msoffcrypto

    try:
        with tempfile.NamedTemporaryFile(suffix=filename.suffix, delete=False) as outf:
            with open(filename, "rb") as f:
                msfile = msoffcrypto.OfficeFile(f)
                msfile.load_key(password=password)
                msfile.decrypt(outf)

            return pathlib.Path(outf.name)
    except msoffcrypto.exceptions.DecryptionError:
        return filename


def _parse_ais_score_entries_2023(filename: pathlib.Path) -> list[Entry]:
    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        logger.error("Could not load workbook.")
        return []

    rows = wb.active.rows  # type: ignore[union-attr]
    _ = next(rows)

    from titlecase import titlecase

    results: list[Entry] = []
    for row in rows:
        if len(row) == 4:
            # NOTE: RIS and RIF entries have 4 columns
            journal, issn, eissn, score = row
            category = index = quartile = None
        elif len(row) == 6:
            # NOTE: AIS has 6 columns
            journal, issn, eissn, category_index, score, quartile_value = row

            category, index = str(category_index.value).split(" - ")
            category = titlecase(category.strip())
            index = index.strip().upper()
            quartile = None if (q := str(quartile_value.value).upper()) == "N/A" else q
        else:
            continue

        if score.value is None:
            break

        try:
            score = float(score.value)  # type: ignore[arg-type]
        except ValueError:
            score = None

        issn_clean = str(issn.value).strip().upper()
        eissn_clean = str(eissn.value).strip().upper()

        results.append(
            Entry(
                category=category,
                index=index,
                name=titlecase(journal.value),
                # NOTE: all ISSNs are of the form XXXX-XXX, so we ignore others
                issn=None if len(issn_clean) != 9 else issn_clean,
                eissn=None if len(eissn_clean) != 9 else eissn_clean,
                quartile=quartile,
                position=None,
                score=score,
            )
        )

    return results


def parse_uefiscdi_article_influence_scores(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = "uefiscdi",  # noqa: S107
) -> list[Entry]:
    """Parse Article Influence Score (AIS) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the documents.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    decrypted_filename = pathlib.Path(filename)
    if password is not None:
        decrypted_filename = _decrypt_file(decrypted_filename, password)

    if version == 2023:
        results = _parse_ais_score_entries_2023(decrypted_filename)
    else:
        raise AssertionError

    logger.info("Extracted %d journals from '%s'", len(results), filename)
    return results


# }}}

# {{{ Relative Influence Score

_parse_ris_score_entries_2023 = _parse_ais_score_entries_2023


def parse_uefiscdi_relative_influence_scores(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = None,
) -> list[Entry]:
    """Parse Relative Influence Score (RIS) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the document.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    decrypted_filename = pathlib.Path(filename)
    if password is not None:
        decrypted_filename = _decrypt_file(decrypted_filename, password)

    if version == 2023:
        results = _parse_ris_score_entries_2023(decrypted_filename)
    else:
        raise AssertionError

    logger.info("Extracted %d journals from '%s'", len(results), filename)
    return results


# }}}

# {{{ Relative Impact Factor

_parse_rif_score_entries_2023 = _parse_ais_score_entries_2023


def parse_uefiscdi_relative_impact_factors(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = None,
) -> list[Entry]:
    """Parse Relative Impact Factor (RIF) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the document.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    decrypted_filename = pathlib.Path(filename)
    if password is not None:
        decrypted_filename = _decrypt_file(decrypted_filename, password)

    if version == 2023:
        results = _parse_rif_score_entries_2023(decrypted_filename)
    else:
        raise AssertionError

    logger.info("Extracted %d journals from '%s'", len(results), filename)
    return results


# }}}

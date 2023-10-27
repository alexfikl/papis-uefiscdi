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


class ZoneEntry(TypedDict):
    """Journal entry information from the UEFISCDI databases.

    This entry corresponds to the Web of Science Core Collection data for
    Journal Impact Factors (JIF) and Article Influence Scores (AIS) gathered
    by the UEFISCDI. These entries are distinguished based on their quartile,
    referred to as zones in the UEFISCDI nomenclature.
    """

    #: Web of Science category for this journal.
    category: str
    #: Citation index identifier.
    index: str

    #: Name of the journal in the provided format.
    name: str
    #: International Standard Serial Number (ISSN) assigned to the journal.
    issn: str
    #: Electronic ISSN assigned to the journal.
    eissn: str
    #: Quartile to which the journal belongs to, in the ``QX`` format.
    quartile: str
    #: Position in its quartile based on the Journal Impact factor (JIF)
    #: or the Article Influence Score (AIS).
    position: int


class ScoreEntry(TypedDict):
    """Journal entry information from the UEFISCDI databases.

    This entry corresponds to the Journal Citation Report (JCR) indicators that
    are published by the UEFISCDI. These entries are distinguished based on their
    score.
    """

    #: Name of the journal.
    name: str
    #: International Standard Serial Number (ISSN) assigned to the journal.
    issn: str
    #: Electronic ISSN assigned to the journal.
    eissn: str

    #: Numerical score as a floating point number. If the journal does not have
    #: a score, but is still in the database, this is set to -1.
    score: float


# }}}

# {{{ Journal Impact Factor


_SUPPORTED_VERSIONS = {2023}

_SUPPORTED_QUARTILES = {"Q1", "Q2", "Q3", "Q4", "N/A"}

_ISSN_RE = re.compile(r"\w{4}-\w{4}|N/A")


def window(iterable: list[str]) -> Iterator[tuple[tuple[str, str], str]]:
    for i, x in enumerate(iterable[2:]):
        yield (iterable[i], iterable[i + 1]), x


def _parse_jif_zone_entry_2023(
    before: tuple[str, str], current: str
) -> ZoneEntry | None:
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

    if not _ISSN_RE.match(eissn):
        return None

    rest, issn = rest.rsplit(" ", maxsplit=1)

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

    return ZoneEntry(
        category=titlecase(category.strip()),
        index=index.upper(),
        name=titlecase(journal.strip()),
        issn=issn.upper(),
        eissn=eissn.upper(),
        quartile=quartile,
        position=int(position),
    )


def parse_uefiscdi_journal_impact_factor(
    filename: str | pathlib.Path, *, version: int = 2023
) -> list[ZoneEntry]:
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

        results: list[ZoneEntry] = []
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
        results, key=lambda j: (j["index"], j["category"], j["quartile"], j["position"])
    )


# }}}

# {{{ Article Influence Score

_parse_ais_zone_entry_2023 = _parse_jif_zone_entry_2023


def parse_uefiscdi_article_influence_score(
    filename: str | pathlib.Path, *, version: int = 2023
) -> list[ZoneEntry]:
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

        results: list[ZoneEntry] = []
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
        results, key=lambda j: (j["index"], j["category"], j["quartile"], j["position"])
    )


# }}}


# {{{ Article Influence Score


def _decrypt_file(filename: pathlib.Path, password: str) -> pathlib.Path:
    import tempfile

    import msoffcrypto

    with tempfile.NamedTemporaryFile(suffix=filename.suffix, delete=False) as outf:
        with open(filename, "rb") as f:
            msfile = msoffcrypto.OfficeFile(f)
            msfile.load_key(password=password)
            msfile.decrypt(outf)

        return outf.name


def _parse_ais_score_entries_2023(filename: pathlib.Path) -> list[ScoreEntry]:
    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        logger.error("Could not load workbook.")
        return []

    rows = wb.active.rows   # type: ignore[union-attr]
    _ = next(rows)

    from titlecase import titlecase

    results: list[ScoreEntry] = []
    for row in rows:
        if len(row) == 4:
            # NOTE: RIS and RIF entries have 4 columns
            journal, issn, eissn, score = row
        elif len(row) == 6:
            # NOTE: AIS has 6 columns
            journal, issn, eissn, _, score, _ = row
        else:
            continue

        if score.value is None:
            break

        try:
            score = float(score.value)
        except ValueError:
            score = -1

        results.append(
            ScoreEntry(
                name=titlecase(journal.value),
                issn=issn.value,
                eissn=eissn.value,
                score=score,
            )
        )

    logger.info("Extracted %d journal from '%s'", len(results), filename)

    return results


def parse_uefiscdi_article_influence_scores(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = "uefiscdi",  # noqa: S107
) -> list[ScoreEntry]:
    """Parse Article Influence Score (AIS) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the documents.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    filename = pathlib.Path(filename)
    if password is not None:
        filename = _decrypt_file(filename, password)

    if version == 2023:
        return _parse_ais_score_entries_2023(filename)
    else:
        raise AssertionError


# }}}

# {{{ Relative Influence Score

_parse_ris_score_entries_2023 = _parse_ais_score_entries_2023


def parse_uefiscdi_relative_influence_scores(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = None,
) -> list[ScoreEntry]:
    """Parse Relative Influence Score (RIS) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the document.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    filename = pathlib.Path(filename)
    if password is not None:
        filename = _decrypt_file(filename, password)

    if version == 2023:
        return _parse_ris_score_entries_2023(filename)
    else:
        raise AssertionError


# }}}

# {{{ Relative Impact Factor

_parse_rif_score_entries_2023 = _parse_ais_score_entries_2023


def parse_uefiscdi_relative_impact_factors(
    filename: str | pathlib.Path,
    *,
    version: int = 2023,
    password: str | None = None,
) -> list[ScoreEntry]:
    """Parse Relative Impact Factor (RIF) data from the given filename.

    This data is usually given in the XLSX Excel format and can be easily
    retrieved from the document.

    :arg password: password for the *filename*, if any, as given on the
        `official website <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
    """
    if version not in _SUPPORTED_VERSIONS:
        raise ValueError(f"Unknown version '{version}'")

    filename = pathlib.Path(filename)
    if password is not None:
        filename = _decrypt_file(filename, password)

    if version == 2023:
        return _parse_ris_score_entries_2023(filename)
    else:
        raise AssertionError


# }}}

# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
import time
from typing import TYPE_CHECKING, Any, TypedDict

from papis_uefiscdi.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

log = get_logger(__name__)

_SUPPORTED_VERSIONS = {2023, 2024}


# {{{ utils


class Entry(TypedDict):
    """Journal entry information from the UEFISCDI databases.

    This entry corresponds to the Web of Science Core Collection data for
    Journal Impact Factors (JIF) and Article Influence Scores (AIS) gathered
    by the UEFISCDI.
    """

    category: str | None
    """Web of Science category for this journal."""
    index: str | None
    """Citation index identifier."""

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


def window(iterable: list[str]) -> Iterator[tuple[tuple[str, str], str]]:
    for i, x in enumerate(iterable[2:]):
        yield (iterable[i], iterable[i + 1]), x


def parse_uefiscdi_journal_impact_factor_quartile(
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

    from papis_uefiscdi.pdf import (
        extract_text,
        parse_2023_quartile_zone_entries,
        parse_2024_quartile_zone_entries,
    )

    with open(filename, "rb") as f:
        pdf = pypdf.PdfReader(f)

        t_start = time.time()
        results: list[Entry] = []
        for i, page in enumerate(pdf.pages):
            if version == 2024:
                lines = [line.text for line in extract_text(page)]
                journals = parse_2024_quartile_zone_entries(lines, fmt="jif")
            elif version == 2023:
                lines = [
                    text
                    for line in page.extract_text().split("\n")
                    if (text := line.strip())
                ]
                journals = parse_2023_quartile_zone_entries(lines, fmt="jif")
            else:
                raise AssertionError

            log.debug(
                "Parsing page %4d / %4d. Extracted %d journals for a total of %d",
                i + 1,
                len(pdf.pages),
                len(journals),
                len(results) + len(journals),
            )
            results.extend(journals)
        t_end = time.time()

        log.info(
            "Extracted JIF for %d journals from %d pages (%.3fs)",
            len(results),
            len(pdf.pages),
            t_end - t_start,
        )

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


def parse_uefiscdi_article_influence_score_quartile(
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

    from papis_uefiscdi.pdf import (
        extract_text,
        parse_2023_quartile_zone_entries,
        parse_2024_quartile_zone_entries,
    )

    with open(filename, "rb") as f:
        pdf = pypdf.PdfReader(f)

        t_start = time.time()
        results: list[Entry] = []
        for i, page in enumerate(pdf.pages):
            if version == 2024:
                lines = [line.text for line in extract_text(page)]
                journals = parse_2024_quartile_zone_entries(lines, fmt="ais")
            elif version == 2023:
                lines = [
                    text
                    for line in page.extract_text().split("\n")
                    if (text := line.strip())
                ]
                journals = parse_2023_quartile_zone_entries(lines, fmt="ais")
            else:
                raise AssertionError

            log.debug(
                "Parsing page %4d / %4d. Extracted %d journals for a total of %d",
                i + 1,
                len(pdf.pages),
                len(journals),
                len(results) + len(journals),
            )
            results.extend(journals)
        t_end = time.time()

        log.info(
            "Extracted AIS for %d journals from %d pages (%.3fs)",
            len(results),
            len(pdf.pages),
            t_end - t_start,
        )

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


def _normalize_2024_ais_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    journal, issn, eissn, category, index, score = row

    return journal, issn, eissn, category, index, score, None


def _normalize_2023_ais_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    journal, issn, eissn, category_index, score, quartile_value = row

    category, index = str(category_index.value).split(" - ")
    quartile = None if (q := str(quartile_value.value).upper()) == "N/A" else q

    return journal, issn, eissn, category, index, score, quartile


def _normalize_rif_ris_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    journal, issn, eissn, score = row
    category = index = None
    return journal, issn, eissn, category, index, score, None


def _parse_score_entries(
    filename: pathlib.Path, getter: Callable[[tuple[Any, ...]], tuple[Any, ...]]
) -> list[Entry]:
    import openpyxl

    wb = openpyxl.load_workbook(filename, read_only=True)
    if wb is None:
        log.error("Could not load workbook.")
        return []

    rows = wb.active.rows  # type: ignore[union-attr]
    _ = next(rows)

    from titlecase import titlecase

    def cell2str(row: tuple[Any, ...]) -> tuple[str | None, ...]:
        result = []
        for entry in row:
            value = getattr(entry, "value", entry)
            result.append(str(value) if value is not None else None)

        return tuple(result)

    results: list[Entry] = []
    for row in rows:
        journal, issn, eissn, category, index, score, quartile = cell2str(getter(row))
        if score is None:
            break

        try:
            scoref = float(score)
        except ValueError:
            scoref = None

        issn = str(issn).strip().upper()
        eissn = str(eissn).strip().upper()

        results.append(
            Entry(
                category=titlecase(category.strip()) if category is not None else None,
                index=index.strip().upper() if index is not None else None,
                name=titlecase(journal.strip()) if journal is not None else None,
                # NOTE: all ISSNs are of the form XXXX-XXX, so we ignore others
                issn=None if len(issn) != 9 else issn,
                eissn=None if len(eissn) != 9 else eissn,
                quartile=quartile,
                position=None,
                score=scoref,
            )
        )

    return results


def parse_uefiscdi_article_influence_score(
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

    t_start = time.time()
    if version == 2024:
        results = _parse_score_entries(decrypted_filename, _normalize_2024_ais_row)
    elif version == 2023:
        results = _parse_score_entries(decrypted_filename, _normalize_2023_ais_row)
    else:
        raise AssertionError
    t_end = time.time()

    log.info(
        "Extracted AIS for %d journals from '%s' (%.3fs)",
        len(results),
        filename,
        t_end - t_start,
    )
    return results


# }}}

# {{{ Relative Influence Score


def parse_uefiscdi_relative_influence_score(
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

    t_start = time.time()
    if version == 2024:  # noqa: SIM114
        results = _parse_score_entries(decrypted_filename, _normalize_rif_ris_row)
    elif version == 2023:
        results = _parse_score_entries(decrypted_filename, _normalize_rif_ris_row)
    else:
        raise AssertionError
    t_end = time.time()

    log.info(
        "Extracted RIS for %d journals from '%s' (%.3fs)",
        len(results),
        filename,
        t_end - t_start,
    )
    return results


# }}}

# {{{ Relative Impact Factor


def parse_uefiscdi_relative_impact_factor(
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

    t_start = time.time()
    if version == 2024:  # noqa: SIM114
        results = _parse_score_entries(decrypted_filename, _normalize_rif_ris_row)
    elif version == 2023:
        results = _parse_score_entries(decrypted_filename, _normalize_rif_ris_row)
    else:
        raise AssertionError
    t_end = time.time()

    log.info(
        "Extracted RIF for %d journals from '%s' (%.3fs)",
        len(results),
        filename,
        t_end - t_start,
    )
    return results


# }}}


# {{{ parse_uefiscdi_database


class Database(TypedDict):
    id: str
    """Identifier for the current database."""
    version: int
    """The version (year of release) of the database."""
    url: str
    """The URL (or filename) it was parsed from."""
    entries: list[Entry]
    """A list of parsed journal entries."""


def parse_uefiscdi_database_from_url(
    database: str,
    url: str | None = None,
    *,
    version: int | None = None,
    password: str | None = None,
) -> Database:
    from papis_uefiscdi.config import UEFISCDI_DATABASE_URL, UEFISCDI_DEFAULT_PASSWORD

    if password is None:
        password = UEFISCDI_DEFAULT_PASSWORD

    if version is None:
        version = max(UEFISCDI_DATABASE_URL)

    if version not in UEFISCDI_DATABASE_URL:
        raise ValueError(
            f"Unsupported version: '{version}'. "
            f"Known versions are: {list(UEFISCDI_DATABASE_URL)}"
        )

    supported_databases = UEFISCDI_DATABASE_URL[version]
    if database not in supported_databases:
        raise ValueError(
            f"Unknown database '{database}'. "
            f"Known databases are: {list(supported_databases)}"
        )

    if url is None:
        url = supported_databases[database]

    from papis_uefiscdi.utils import download_document

    log.info("Getting data from '%s'.", url)

    filename = pathlib.Path(url)
    if not filename.exists():
        result = download_document(
            url,
            expected_document_extension=pathlib.Path(url).suffix[1:],
        )

        if result is None:
            raise FileNotFoundError(url)
        else:
            filename = result
            log.info("Downloaded file at '%s'.", filename)
    else:
        raise FileNotFoundError(filename)

    entries: list[Entry]
    if database == "aisq":
        entries = parse_uefiscdi_article_influence_score_quartile(
            filename, version=version
        )
    elif database == "jifq":
        entries = parse_uefiscdi_journal_impact_factor_quartile(
            filename, version=version
        )
    elif database == "ais":
        entries = parse_uefiscdi_article_influence_score(
            filename, version=version, password=password
        )
    elif database == "ris":
        entries = parse_uefiscdi_relative_influence_score(filename, version=version)
    elif database == "rif":
        entries = parse_uefiscdi_relative_impact_factor(filename, version=version)
    else:
        raise ValueError(f"Unknown database name: '{database}'")

    return Database(id=database, version=version, url=url, entries=entries)


# }}}

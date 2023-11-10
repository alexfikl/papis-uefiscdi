# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from typing import Any

import click

import papis.cli
import papis.config
import papis.document
import papis.logging
import papis.strings
from papis.document import Document

logger = papis.logging.get_logger(__name__)

# {{{ utils

UEFISCDI_SUPPORTED_DATABASES = {
    "aisq": "Article Influence Score (Quartiles)",
    "jifq": "Journal Impact Factor (Quartiles)",
    "ais": "Article Influence Score (Scores)",
    "ris": "Relative Influence Score (Scores)",
    "rif": "Relative Impact Factor (Scores)",
}

UEFISCDI_DATABASE_TO_KEY = {
    "aisq": "uefiscdi_ais_quartile",
    "jifq": "uefiscdi_jif_quartile",
    "ais": "uefiscdi_ais_score",
    "ris": "uefiscdi_ris_score",
    "rif": "uefiscdi_rif_score",
}

papis.config.register_default_settings(
    {
        "uefiscdi": {
            "version": 2023,
            "aisq-url": (
                "https://uefiscdi.gov.ro/resource-866007-zone.iunie.2023.ais.pdf"
            ),
            "jifq-url": (
                "https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf"
            ),
            "ais-url": "https://uefiscdi.gov.ro/resource-863884-ais_2022.xlsx",
            "rif-url": "https://uefiscdi.gov.ro/resource-863887-rif_2022.xlsx",
            "ris-url": "https://uefiscdi.gov.ro/resource-863882-ris_2022.xlsx",
            "password": "uefiscdi",
        }
    }
)


def get_uefiscdi_database_path(database: str) -> pathlib.Path:
    config_dir = pathlib.Path(papis.config.get_config_folder())
    return config_dir / "uefiscdi" / f"{database}.json"


def get_uefiscdi_database(
    database: str, *, overwrite: bool = False, use_password: bool = False
) -> dict[str, Any]:
    import json

    filename = get_uefiscdi_database_path(database)
    if not filename.exists() or overwrite:
        try:
            db = parse_uefiscdi(database, use_password=use_password)
        except Exception as exc:
            logger.error(
                "Could not parse UEFISCDI database '%s'", database, exc_info=exc
            )
            return {}

        if not filename.parent.exists():
            filename.parent.mkdir()

        with open(filename, "w", encoding="utf-8") as outf:
            json.dump(db, outf, indent=2, sort_keys=False)

        logger.info("Database saved in '%s'.", filename)
    else:
        logger.info("Database loaded from '%s'.", filename)

        with open(filename, encoding="utf-8") as inf:
            db = json.load(inf)

    return db


def parse_uefiscdi(
    database: str,
    url: str | None = None,
    *,
    version: int | None = None,
    use_password: bool = True,
) -> dict[str, Any]:
    if version is None:
        version = papis.config.getint("version", section="uefiscdi")

    if version is None:
        raise ValueError("Could not determine database version")

    if database not in UEFISCDI_SUPPORTED_DATABASES:
        raise ValueError(f"Unknown database '{database}'")

    if url is None:
        url = papis.config.getstring(f"{database}-url", section="uefiscdi")

    from papis_uefiscdi.utils import download_document

    logger.info("Getting data from '%s'.", url)
    filename = download_document(
        url,
        expected_document_extension=pathlib.Path(url).suffix[1:],
    )
    if filename is None:
        raise FileNotFoundError(url)

    logger.info("Downloaded file at '%s'.", filename)

    password = None
    if use_password:
        password = papis.config.get("password", section="uefiscdi")

    entries: list[Any]
    if database == "aisq":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_article_influence_score

        entries = parse_uefiscdi_article_influence_score(filename, version=version)
    elif database == "jifq":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_journal_impact_factor

        entries = parse_uefiscdi_journal_impact_factor(filename, version=version)
    elif database == "ais":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_article_influence_scores

        entries = parse_uefiscdi_article_influence_scores(
            filename, version=version, password=password
        )
    elif database == "ris":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_relative_influence_scores

        entries = parse_uefiscdi_relative_influence_scores(
            filename, version=version, password=password
        )
    elif database == "rif":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_relative_impact_factors

        entries = parse_uefiscdi_relative_impact_factors(
            filename, version=version, password=password
        )
    else:
        raise ValueError(f"Unknown database name: '{database}'")

    return {"version": version, "url": url, "entries": entries}


def find_uefiscdi(
    db: dict[str, Any], doc: Document, key: str, *, batch: bool = True
) -> str | None:
    journal = doc.get("journal")
    if not journal:
        return None

    from difflib import SequenceMatcher

    journal = journal.lower()
    if journal in db:
        matches = db[journal]
    else:
        matches = [
            entry
            for name, entry in db.items()
            if SequenceMatcher(None, journal, name).ratio() > 0.8
        ]

    if not matches:
        return None

    if len(matches) == 1:
        (match,) = matches
    elif batch:
        # NOTE: this usually happens because the same journal is in multiple
        # categories; should use interactive mode for better options
        logger.info(
            "Found multiple matches: '%s'. Picking the first one!",
            "', '".join(m["name"] for m in matches),
        )
        match = matches[0]
    else:
        from papis.tui.utils import select_range

        indices: list[int] = []
        while len(indices) != 1:
            indices = select_range(
                [
                    f"{match['name']} ({match.get('category', 'unknown')})"
                    for match in matches
                ],
                "Select matching journal",
            )

            if len(indices) != 1:
                logger.error("Can only select a single journal")

        match = matches[indices[0]]

    return str(match[key])


# }}}


# {{{ command


@click.command("uefiscdi")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@click.option(
    "--database",
    type=click.Choice(list(UEFISCDI_SUPPORTED_DATABASES)),
    help="Add quartiles or scores from the database",
)
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@click.option(
    "--no-password",
    flag_value=True,
    default=False,
    is_flag=True,
    help="Do not attempt do descrypt remote file before parsing",
)
@click.option(
    "--overwrite",
    flag_value=True,
    default=False,
    is_flag=True,
    help="Overwrite existing UEFISCDI databases",
)
@click.option(
    "--batch",
    flag_value=True,
    default=False,
    is_flag=True,
    help="Run in batch mode (no interactive prompts)",
)
@click.option(
    "--list-databases",
    "list_databases",
    flag_value=True,
    default=False,
    is_flag=True,
    help="List all known databases and their descriptions",
)
def cli(
    query: str,
    database: str,
    doc_folder: str | tuple[str, ...],
    _all: bool,
    sort_field: str | None,
    sort_reverse: bool,
    no_password: bool,
    overwrite: bool,
    batch: bool,
    list_databases: bool,
) -> None:
    """Manage UEFISCDI journal impact factors and other indicators."""
    if list_databases:
        import colorama

        for did, description in UEFISCDI_SUPPORTED_DATABASES.items():
            click.echo(f"{colorama.Style.BRIGHT}{did}{colorama.Style.RESET_ALL}")
            click.echo(f"    {description}")

        return

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all  # type: ignore[arg-type]
    )

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    from collections import defaultdict

    db = get_uefiscdi_database(
        database, overwrite=overwrite, use_password=not no_password
    )
    journal_to_entry = defaultdict(list)
    for entry in db["entries"]:
        journal_to_entry[entry["name"].lower()].append(entry)

    from papis.api import save_doc

    for doc in documents:
        doc_key = UEFISCDI_DATABASE_TO_KEY[database]
        entry_key = doc_key.split("_")[-1]
        result = find_uefiscdi(journal_to_entry, doc, key=entry_key, batch=batch)
        if not result:
            continue

        logger.info(
            "Setting key '%s' to '%s' (journal '%s').",
            doc_key,
            result,
            doc["journal"],
        )
        doc[doc_key] = result
        save_doc(doc)


# }}}


# {{{ explorer


def entry_to_papis(entry: dict[str, Any], version: int) -> papis.document.Document:
    # NOTE: this is essentially constructed so that it looks nice with the default
    # picker header format used by papis at the moment, but it should look ok
    # with other pickers as well

    return papis.document.from_data(
        {
            "title": "{} ({})".format(
                entry["name"], entry.get("issn") or entry.get("eissn")
            ),
            "author": "Category: {} / Index: {}".format(
                entry.get("category", "unknown"), entry.get("index", "unknown")
            ),
            "year": version,
            "tags": (
                "Quartile: {}".format(entry["quartile"])
                if "quartile" in entry
                else "Score: {}".format(entry["score"])
            ),
        }
    )


@click.command("uefiscdi")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default="")
@click.option(
    "--database",
    type=click.Choice(list(UEFISCDI_SUPPORTED_DATABASES)),
    default="jifq",
    help="Add quartiles or scores from the database",
)
def explorer(ctx: click.core.Context, query: str, database: str) -> None:
    from difflib import SequenceMatcher

    query = query.lower()

    def match(journal: str) -> bool:
        if not query:
            return True

        journal = journal.lower()
        if query in journal:
            return True

        return SequenceMatcher(None, query, journal).ratio() > 0.8

    db = get_uefiscdi_database(database)
    matches = [entry for entry in db["entries"] if match(entry["name"])]
    logger.info("Found %s documents.", len(matches))

    ctx.obj["documents"] += [
        entry_to_papis(match, version=db["version"]) for match in matches
    ]


# }}}

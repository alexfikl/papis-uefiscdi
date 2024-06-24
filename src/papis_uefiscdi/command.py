# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import pathlib
from typing import Any, Match, Pattern

import click

import papis.cli
import papis.config
import papis.document
import papis.logging
import papis.strings
from papis_uefiscdi.config import (
    INDEX_ID_TO_NAME,
    UEFISCDI_DATABASE_URL,
    UEFISCDI_SUPPORTED_DATABASES,
)

logger = papis.logging.get_logger(__name__)

# {{{ utils

UEFISCDI_DATABASE_YEAR = 2023

papis.config.register_default_settings({
    "uefiscdi": {
        "version": UEFISCDI_DATABASE_YEAR,
        "aisq-url": UEFISCDI_DATABASE_URL[UEFISCDI_DATABASE_YEAR]["aisq"],
        "jifq-url": UEFISCDI_DATABASE_URL[UEFISCDI_DATABASE_YEAR]["jifq"],
        "ais-url": UEFISCDI_DATABASE_URL[UEFISCDI_DATABASE_YEAR]["ais"],
        "rif-url": UEFISCDI_DATABASE_URL[UEFISCDI_DATABASE_YEAR]["rif"],
        "ris-url": UEFISCDI_DATABASE_URL[UEFISCDI_DATABASE_YEAR]["ris"],
        "password": "uefiscdi",
    }
})


def get_uefiscdi_database_path(database: str, version: int) -> pathlib.Path:
    config_dir = pathlib.Path(papis.config.get_config_folder())
    return config_dir / "uefiscdi" / str(version) / f"{database}.json"


def load_uefiscdi_database(database: str, version: int | None = None) -> dict[str, Any]:
    if version is None:
        version = papis.config.getint("version", section="uefiscdi")

    assert version is not None

    filename = get_uefiscdi_database_path(database, version)
    if not filename.exists():
        logger.error("File for database '%s' does not exist: '%s'", database, filename)
        logger.error("Run 'papis uefiscdi index -d %s' to download it.", database)
        return {}

    logger.info("Database loaded from '%s'.", filename)

    with open(filename, encoding="utf-8") as inf:
        db = json.load(inf)

    return dict(db)


def get_uefiscdi_database(
    database: str,
    *,
    overwrite: bool = False,
    password: str | None = None,
    version: int | None = None,
) -> dict[str, Any]:
    config_version = papis.config.getint("version", section="uefiscdi")

    if version is None:
        version = config_version

    assert version is not None

    if version == config_version:
        url = None
    else:
        if version not in UEFISCDI_DATABASE_URL:
            logger.error(
                "Cannot determine URL for the '%s' database from '%s'",
                database,
                version,
            )
            return {}

        url = UEFISCDI_DATABASE_URL[version][database]

    filename = get_uefiscdi_database_path(database, version)
    if not filename.exists() or overwrite:
        try:
            db = parse_uefiscdi(database, url, password=password, version=version)
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
    password: str | None = None,
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

    if password is None:
        password = papis.config.get("password", section="uefiscdi")

    from papis_uefiscdi import uefiscdi

    entries: list[Any]
    if database == "aisq":
        entries = uefiscdi.parse_uefiscdi_article_influence_score(
            filename, version=version
        )
    elif database == "jifq":
        entries = uefiscdi.parse_uefiscdi_journal_impact_factor(
            filename, version=version
        )
    elif database == "ais":
        entries = uefiscdi.parse_uefiscdi_article_influence_scores(
            filename, version=version, password=password
        )
    elif database == "ris":
        entries = uefiscdi.parse_uefiscdi_relative_influence_scores(
            filename, version=version
        )
    elif database == "rif":
        entries = uefiscdi.parse_uefiscdi_relative_impact_factors(
            filename, version=version
        )
    else:
        raise ValueError(f"Unknown database name: '{database}'")

    return {"id": database, "version": version, "url": url, "entries": entries}


def to_dummy_document(
    entry: dict[str, Any],
    *,
    index: int,
    name: str,
    version: int,
) -> papis.document.Document:
    # NOTE: this is essentially constructed so that it looks nice with the default
    # picker header format used by papis at the moment, but it should look ok
    # with other pickers as well

    quartile = entry["quartile"] or "N/A"
    score = entry["score"] or "N/A"
    if score != "N/A":
        score = f"{score:.3f}"

    return papis.document.from_data({
        # NOTE: used to retrieve original entry
        "_id": index,
        "title": "[{}] {}".format(
            entry["issn"] or entry["eissn"],
            entry["name"],
        ),
        "author": "Category: {} | Index: {}".format(
            entry["category"] or "unknown",
            entry["index"] or "unknown",
        ),
        "tags": f"{name.upper()} Score {score} | Quartile {quartile}",
        "year": version,
        **entry,
    })


def match_journal(
    document: papis.document.Document,
    search: Pattern[str],
    match_format: str | None = None,
    doc_key: str | None = None,
) -> Match[str] | None:
    match_format = match_format or "{doc[title]}{doc[author]}"
    if doc_key is not None:
        match_string = str(document[doc_key])
    else:
        match_string = papis.format.format(match_format, document)

    return search.match(match_string)


# }}}


# {{{ command


@click.group("uefiscdi")
@click.help_option("--help", "-h")
@click.option(
    "--list-databases",
    "list_databases",
    flag_value=True,
    default=False,
    is_flag=True,
    help="List all known databases and their descriptions",
)
def cli(list_databases: bool) -> None:
    """Managed UEFISCDI scientometric databases"""
    if not list_databases:
        return

    import colorama

    for did, description in UEFISCDI_SUPPORTED_DATABASES.items():
        click.echo(f"{colorama.Style.BRIGHT}{did}{colorama.Style.RESET_ALL}")
        click.echo(f"    {description}")


# }}}


# {{{ index


@cli.command("index")
@click.help_option("--help", "-h")
@click.option(
    "-p",
    "--password",
    help="Password to use when opening the remote database file",
)
@click.option(
    "--year",
    type=int,
    default=None,
    help="Year the database was released",
)
@click.option(
    "--overwrite",
    flag_value=True,
    default=False,
    is_flag=True,
    help="Overwrite existing UEFISCDI databases",
)
def cli_index(password: str, year: int | None, overwrite: bool) -> None:
    """Download and parse UEFISCDI databases"""
    if year is None:
        year = papis.config.get("version", section="uefiscdi")

    for name in UEFISCDI_SUPPORTED_DATABASES:
        get_uefiscdi_database(
            name, overwrite=overwrite, password=password, version=year
        )


# }}}


# {{{ search


@cli.command("search")
@click.help_option("--help", "-h")
@click.argument("query", default=".", type=str)
@click.option(
    "-d",
    "--database",
    type=click.Choice(list(UEFISCDI_SUPPORTED_DATABASES), case_sensitive=False),
    default="ais",
    help="Database to search for scores",
)
@click.option(
    "--year",
    type=int,
    default=None,
    help="Year the database was released",
)
@click.option(
    "-c",
    "--category",
    default=None,
    help="A Web of Science category to restrict the results to",
)
@click.option(
    "-i",
    "--index",
    type=click.Choice(list(INDEX_ID_TO_NAME), case_sensitive=False),
    help="Web of Science citation index identifier",
)
@click.option(
    "-q",
    "--quartile",
    default=None,
    type=int,
    help="Minimum quartile to display",
)
@click.option(
    "--sort",
    "sort_field",
    default="name",
    help="Sort results with respect to the FIELD",
    metavar="FIELD",
)
@click.option(
    "--reverse",
    "sort_reverse",
    flag_value=False,
    default=True,
    is_flag=True,
    help="List all known databases and their descriptions",
)
def cli_search(
    query: str,
    database: str,
    year: int | None,
    category: str | None,
    index: str | None,
    quartile: int | None,
    sort_field: str,
    sort_reverse: bool,
) -> None:
    """Search UEFISCDI databases"""

    if year is None:
        year = papis.config.get("version", section="uefiscdi")

    if category is not None:
        category = category.lower()

    if index is not None:
        index = index.lower()

    assert year is not None

    def match(entry: dict[str, Any]) -> bool:
        e_category = entry.get("category")
        in_category = not category or (e_category and category in e_category.lower())

        e_index = entry.get("index")
        in_index = not index or (e_index and index == e_index.lower())

        e_quartile = entry.get("quartile")
        in_quartile = not quartile or (not e_quartile or quartile >= int(e_quartile[1]))

        return bool(in_category and in_index and in_quartile)

    db = load_uefiscdi_database(database, year)
    docs = [
        to_dummy_document(entry, index=n, name=database, version=year)
        for n, entry in enumerate(db["entries"])
        if match(entry)
    ]

    from papis.docmatcher import DocMatcher

    DocMatcher.match_format = "{doc[title]}{doc[author]}"
    DocMatcher.set_search(query)
    DocMatcher.set_matcher(match_journal)
    DocMatcher.parse()

    from papis.utils import parmap

    if query == ".":
        filtered_docs = docs
    else:
        result = parmap(DocMatcher.return_if_match, docs)
        filtered_docs = [e for e in result if e is not None]

    from papis.pick import pick_doc

    def key_func(d: papis.document.Document) -> str | float | int:
        field = d[sort_field]
        if field is None:
            return 0.0 if sort_field == "score" else "ZZ"
        else:
            assert isinstance(field, (str, float, int))
            return field

    filtered_docs = sorted(filtered_docs, key=key_func, reverse=sort_reverse)
    filtered_docs = [entry for entry in pick_doc(filtered_docs) if entry]
    filtered_entries = [db["entries"][d["_id"]] for d in filtered_docs]

    click.echo(json.dumps(filtered_entries, indent=2, sort_keys=True))


# }}}


# {{{ add


@cli.command("add")
@click.help_option("--help", "-h")
@click.option(
    "-d",
    "--database",
    type=click.Choice(list(UEFISCDI_SUPPORTED_DATABASES), case_sensitive=False),
    default="ais",
    help="Database to search for scores",
)
def cli_add(database: str) -> None:
    """Add UEFISCDI scores and quartiles to documents"""
    logger.error("Not implemented yet. :(")


# }}}

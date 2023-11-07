# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pathlib
from typing import Any

import click

import papis.cli
import papis.config
import papis.logging
from papis.document import Document

logger = papis.logging.get_logger(__name__)

UEFISCDI_SUPPORTED_DATABASES = {"aisq", "jifq", "ais", "ris", "rif"}

_DATABASE_TO_URL = {
    "aisq": "ais-ranking-url",
    "jifq": "jif-ranking-url",
    "ais": "ais-score-url",
    "rif": "rif-score-url",
    "ris": "ris-score-url",
}


papis.config.register_default_settings(
    {
        "uefiscdi": {
            "version": 2023,
            "ais-ranking-url": (
                "https://uefiscdi.gov.ro/resource-866007-zone.iunie.2023.ais.pdf"
            ),
            "jif-ranking-url": (
                "https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf"
            ),
            "ais-score-url": "https://uefiscdi.gov.ro/resource-863884-ais_2022.xlsx",
            "rif-score-url": "https://uefiscdi.gov.ro/resource-863887-rif_2022.xlsx",
            "ris-score-url": "https://uefiscdi.gov.ro/resource-863882-ris_2022.xlsx",
            "password": "uefiscdi",
        }
    }
)


@click.group()
@click.help_option("--help", "-h")
def cli() -> None:
    """Manage UEFISCDI journal impact factors and other indicators."""


# {{{ update


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

    if database not in _DATABASE_TO_URL:
        raise ValueError(f"Unknown database '{database}'")

    if url is None:
        url = papis.config.getstring(_DATABASE_TO_URL[database], section="uefiscdi")

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


@cli.command("update")
@click.help_option("--help", "-h")
@click.option("--database", type=click.Choice(list(UEFISCDI_SUPPORTED_DATABASES)))
@papis.cli.option("--no-password", flag_value=True, default=False, is_flag=True)
def update(database: str, no_password: str | None) -> None:
    config_dir = pathlib.Path(papis.config.get_config_folder())

    uefiscdi_dir = config_dir / "uefiscdi"
    if not uefiscdi_dir.exists():
        uefiscdi_dir.mkdir()

    try:
        result = parse_uefiscdi(database, use_password=not no_password)
    except Exception as exc:
        logger.error("Could not parse UEFISCDI database '%s'", database, exc_info=exc)
        return

    import json

    filename = uefiscdi_dir / f"{database}.json"
    with open(filename, "w", encoding="utf-8") as outf:
        json.dump(result, outf, indent=2, sort_keys=False)

    logger.info("Database saved in '%s'.", filename)


# }}}

# {{{


def add_uefiscdi(doc: Document) -> None:
    pass


@cli.command("add")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
def add(
    query: str,
    doc_folder: tuple[str, ...],
    all_: bool,
    sort_field: str | None,
    sort_reverse: bool,
) -> None:
    from papis.api import save_doc

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder[0], sort_field, sort_reverse, all_
    )

    for doc in documents:
        add_uefiscdi(doc)
        save_doc(doc)


# }}}

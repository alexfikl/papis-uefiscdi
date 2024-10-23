# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

import csv

import pytest

from papis_uefiscdi.config import UEFISCDI_DATABASE_URL
from papis_uefiscdi.testing import TemporaryConfiguration


@pytest.mark.parametrize(
    ("fmt", "version", "url"),
    [
        ("jif", 2024, UEFISCDI_DATABASE_URL[2024]["jifq"]),
        # ("jif", 2023, UEFISCDI_DATABASE_URL[2023]["jifq"]),
        # ("ais", 2023, UEFISCDI_DATABASE_URL[2023]["aisq"]),
    ],
)
def test_parse_zone_data(
    tmp_config: TemporaryConfiguration, fmt: str, version: int, url: str
) -> None:
    from papis_uefiscdi.utils import download_document

    filename = download_document(url, expected_document_extension="pdf")
    assert filename is not None

    if fmt == "jif":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_journal_impact_factor

        result = parse_uefiscdi_journal_impact_factor(filename, version=version)
    elif fmt == "ais":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_article_influence_score

        result = parse_uefiscdi_article_influence_score(filename, version=version)
    else:
        raise ValueError(f"Unknown data format: '{fmt}'")

    outfile = "{}.csv".format(url.split("/")[-1][:-4])
    with open(outfile, "w", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=list(result[0]), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


@pytest.mark.parametrize(
    ("fmt", "version", "url"),
    [
        ("ais", 2023, UEFISCDI_DATABASE_URL[2023]["ais"]),
        ("ris", 2023, UEFISCDI_DATABASE_URL[2023]["ris"]),
        ("rif", 2023, UEFISCDI_DATABASE_URL[2023]["rif"]),
    ],
)
def test_parse_score_data(
    tmp_config: TemporaryConfiguration, fmt: str, version: int, url: str
) -> None:
    from papis_uefiscdi.utils import download_document

    filename = download_document(url, expected_document_extension="xlsx")
    assert filename is not None

    if fmt == "ais":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_article_influence_scores

        result = parse_uefiscdi_article_influence_scores(filename, version=version)
    elif fmt == "ris":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_relative_influence_scores

        result = parse_uefiscdi_relative_influence_scores(
            filename, version=version, password=None
        )
    elif fmt == "rif":
        from papis_uefiscdi.uefiscdi import parse_uefiscdi_relative_impact_factors

        result = parse_uefiscdi_relative_impact_factors(
            filename, version=version, password=None
        )
    else:
        raise ValueError(f"Unknown data format: '{fmt}'")

    outfile = "{}.csv".format(url.split("/")[-1][:-5])
    with open(outfile, "w", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=list(result[0]), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

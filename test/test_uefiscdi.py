# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

import csv

import pytest

from papis_uefiscdi.testing import TemporaryConfiguration


def test_parse_journal_impact_factor(tmp_config: TemporaryConfiguration) -> None:
    from papis.downloaders import download_document

    url = "https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf"
    filename = download_document(url, expected_document_extension="pdf")
    assert filename is not None

    from papis_uefiscdi.uefiscdi import parse_uefiscdi_journal_impact_factor

    result = parse_uefiscdi_journal_impact_factor(filename, version=2023)
    with open("jif.csv", "w", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=list(result[0]), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


def test_parse_article_influence_score(tmp_config: TemporaryConfiguration) -> None:
    from papis.downloaders import download_document

    url = "https://uefiscdi.gov.ro/resource-866007-zone.iunie.2023.ais.pdf"
    filename = download_document(url, expected_document_extension="pdf")
    assert filename is not None

    from papis_uefiscdi.uefiscdi import parse_uefiscdi_article_influence_score

    result = parse_uefiscdi_article_influence_score(filename, version=2023)
    with open("ais.csv", "w", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=list(result[0]), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(result)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        pytest.main([__file__])

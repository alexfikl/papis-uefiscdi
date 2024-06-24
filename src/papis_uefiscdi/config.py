# SPDX-FileCopyrightText: 2023 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: MIT

from __future__ import annotations

INDEX_ID_TO_NAME = {
    "AHCI": "Arts Humanities Citation Index",
    "SCIE": "Science Citation Index Expanded",
    "SSCI": "Social Sciences Citation Index",
}
"""A mapping of citation indexes (as they appear in the UEFISCDI databases) to their
full names.
"""


UEFISCDI_SUPPORTED_DATABASES = {
    "aisq": "Article Influence Score (Quartiles)",
    "jifq": "Journal Impact Factor (Quartiles)",
    "ais": "Article Influence Score (Scores)",
    "ris": "Relative Influence Score (Scores)",
    "rif": "Relative Impact Factor (Scores)",
}
"""A mapping of database identifiers to their full names (that can be used for
display purposes).
"""

UEFISCDI_DATABASE_TO_KEY = {
    "aisq": "uefiscdi_ais_quartile",
    "jifq": "uefiscdi_jif_quartile",
    "ais": "uefiscdi_ais_score",
    "ris": "uefiscdi_ris_score",
    "rif": "uefiscdi_rif_score",
}
"""A mapping of database identifier to unique key names."""

UEFISCDI_DATABASE_URL = {
    2023: {
        "aisq": "https://uefiscdi.gov.ro/resource-866007-zone.iunie.2023.ais.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-863884-ais_2022.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-863882-ris_2022.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-863887-rif_2022.xlsx",
    }
}
"""A mapping of database identifiers to URLs containing the databases themselves.
"""

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

# NOTE: This mostly has the last 5 years, since those are required for UEFISCDI
# competitions.
UEFISCDI_DATABASE_URL = {
    2024: {
        "aisq": "https://uefiscdi.gov.ro/resource-861733-JCR.iunie.2024.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-861733-JCR.iunie.2024.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-861731-AIS.JCR2023.iunie2024.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-861773-RIS.2023iunie2024.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-861735-FIR.2023iunie2024.xlsx",
    },
    2023: {
        "aisq": "https://uefiscdi.gov.ro/resource-866007-zone.iunie.2023.ais.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-863884-ais_2022.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-863882-ris_2022.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-863887-rif_2022.xlsx",
    },
    2022: {
        "aisq": "https://uefiscdi.gov.ro/resource-862159-zone.2022.ais.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-862151-zone.2022.if.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-862108-ais.2021.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-862102-ris.2021.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-862155-rif.2021.xlsx",
    },
    2021: {
        "aisq": "https://uefiscdi.gov.ro/resource-820923-ais2021.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-820921-if2021.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-820980-ais.2020.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-820984-sri.2020.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-820987-rif.2020.xlsx",
    },
    2020: {
        "aisq": "https://uefiscdi.gov.ro/resource-821878-clasament2020.ais.pdf",
        "jifq": "https://uefiscdi.gov.ro/resource-821873-clasament2020.if.pdf",
        "ais": "https://uefiscdi.gov.ro/resource-821312-ais2019-iunie2020-.valori.cuartile.xlsx",
        "ris": "https://uefiscdi.gov.ro/resource-829001-sri.2019.xlsx",
        "rif": "https://uefiscdi.gov.ro/resource-829003-rif.2019.xlsx",
    },
    2019: {
        "aisq": "https://uefiscdi.gov.ro/resource-822841",
        "jifq": "https://uefiscdi.gov.ro/resource-822843",
        "ais": "https://uefiscdi.gov.ro/resource-828068",
        "ris": "https://uefiscdi.gov.ro/resource-828022",
        "rif": "https://uefiscdi.gov.ro/resource-828027",
    },
}
"""A mapping of database identifiers to URLs containing the databases themselves.
"""

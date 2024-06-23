.. image:: https://github.com/alexfikl/papis-uefiscdi/workflows/CI/badge.svg
    :alt: Build Status
    :target: https://github.com/alexfikl/papis-uefiscdi/actions?query=branch%3Amain+workflow%3ACI

papis-uefiscdi
==============

This library handles downloading data from the `UEFISCDI <https://uefiscdi.gov.ro/>`__
(the main research financing body in Romania) and transforming it into a more open
and easy to manipulate format (e.g. CSV). The plugin supports obtaining:

* Journal Impact Factor (JIF) data . At the moment of writing, this data can be
found `here <https://uefiscdi.gov.ro/scientometrie-reviste>`__.
* Article Influence Score (AIS) data . At the moment of writing, this data can be
  found `here <https://uefiscdi.gov.ro/scientometrie-reviste>`__ or
  `here <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__
* Relative Influence Score (RIS) data. At the moment of writing, this data can be
  found `here <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.
* Relative Impact Factor (RIF) data. At the moment of writing, this data can be
  found `here <https://uefiscdi.gov.ro/scientometrie-baze-de-date>`__.

The `Papis <https://github.com/papis/papis>`__ plugin that comes with it allows
for easy management of the data and adding it to existing documents in a Papis
database.

Workflow
========

``papis-uefiscdi`` supports two slightly separate workflows: exploring the UEFISCDI
databases and adding scores and quartiles from the databases to your Papis
library. We'll describe both of them a bit below.


Exploring
---------

As a first step, we will need to download the UEFISCDI databases and convert
them to a more usable format. At least at the time of writing, they are in a
unholy mix of PDF and Excel files (yuck), which are not easily accessible. The
``papis uefiscdi`` command can be used to transform them a more consistent JSON
format.

To download and convert all the files, run

.. code:: sh

    papis uefiscdi index --overwrite

This command may take a while because it has to download and parse the big
files from UEFISCDI. At the end, it should add some JSON files to your Papis
configuration folder in ``$PAPIS_CONFIG_FOLDER/uefiscdi/$YEAR/$NAME.json``.
The resulting databases can be easily searched and displayed with

.. code:: sh

    papis uefiscdi search --database <NAME> <QUERY>

where we can choose the database we want to search, the minimum quartile that
should be shown, a Web of Science category, etc. The query can also be used to
further restrict the results, e.g. we can search for journal names containing
the word ``nano`` using

.. code:: sh

   papis uefiscdi search --database ais 'name:nano'

Extending
---------

The command can also be used to add scores and quartiles to existing documents
in a Papis library. This can be done using e.g.

.. code:: sh

    papis uefiscdi add -d ais <QUERY>

which will add a ``uefiscdi_ais_quartile`` and a ``uefiscdi_ais_score`` keys
to all the documents that match the query. Unfortunately, matching an existing
Papis document to a UEFISCDI journal entry is not straightforward. The following
caveats apply:

* The match to the UEFISCDI database entries is done by the journal name,
  which is lowercased and cleaned up to remove any variance in spelling, but
  can sometimes still fail.
* If the Papis document itself has an ISSN entry, it is used instead of the
  journal name matching. This can be a lot more reliable.
* Some journals appear in multiple categories, the one with the higher
  quartile / score is chosen. Generally, if we match a journal by name, we then
  use its ISSN to look for other matches.

Configuration
-------------

This command uses the ``uefiscdi`` section for its configuration options. The
possible settings are

* ``version`` (default ``2023``): The year the database was published. This mainly
  affects what parsing is used, as the various documents are not compatible.
* ``password`` (default ``uefiscdi``): Password used for known files, e.g. ``ais``.
* ``aisq-url``: URL to the file containing the AIS quartile data.
* ``jifq-url``: URL to the file containing the JIF quartile data.
* ``ais-url``: URL to the file containing the AIS score data.
* ``rif-url``: URL to the file containing the RIF score data.
* ``ris-url``: URL to the file containing the RIS score data.

Examples URLs are given above, but they will need to be updated as new versions
are released. We strive to keep the latest values as defaults, but this may not
be always possible.

Library
=======

The plugin is also contains a library component that can be used without Papis.
For example, to write the JIF scores to a CSV file, use

.. code:: python

    import csv
    from papis_uefiscdi import uefiscdi

    filename = download("https://uefiscdi.gov.ro/resource-866009-zone.iunie.2023.jif.pdf")
    jifs = uefiscdi.parse_uefiscdi_journal_impact_factor(filename, version=2023)

    with open("jif.csv", "w", encoding="utf-8") as outf:
        writer = csv.DictWriter(outf, fieldnames=list(jifs[0]))
        writer.writeheader()
        writer.writerows(jifs)

Similar functions exist to parse the other scores provided by UEFISCDI.

LICENSE
=======

The library is licensed under GPL-3.0-or-later because it contains functionality
from ``papis``, but any new functionality is licensed under the MIT license.

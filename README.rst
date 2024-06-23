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
database. A usual workflow is as follows: first we must download and index the
required databases with

.. code:: sh

    papis uefiscdi index --overwrite

This command may take a while because it has to download and parse the big
files from UEFISCDI. At the end, it should add some documents to your Papis
configuration folder, i.e. ``$PAPIS_CONFIG_FOLDER/uefiscdi/$YEAR/$NAME.json``.
the resulting databases can be easily searched and displayed with

.. code:: sh

    papis uefiscdi search --database <NAME> --quartile <INT> --category <NAME> <QUERY>

where we can choose the database we want to search, the minimum quartile that
should be show, a Web of Science category, etc. The query can also be used to
further restrict the results, e.g. we can search for for journal names containing
the word ``nano`` using

.. code:: sh

   papis uefiscdi search --database ais 'name:nano'

Finally, the command can be used to add scores and quartiles to existing documents
in a Papis library. This can be done using e.g.

.. code:: sh

    papis uefiscdi add -d ais <QUERY>

which will add a ``uefiscdi_ais_quartile`` and a ``uefiscdi_ais_score`` keys
to all the documents that match the query. The match to the UEFISCDI database
entries is done by the journal name, which is lowercased and cleaned up to
remove any variance in spelling, but can sometimes still fail. Furthermore,
since some journals appear in multiple categories, the one with the higher
quartile / score is chosen.

Configuration options
=====================

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

LICENSE
=======

The library is licensed under GPL-3.0-or-later because it contains functionality
from ``papis``, but any new functionality is licensed under the MIT license.

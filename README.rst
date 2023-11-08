.. image:: https://github.com/alexfikl/papis-uefiscdi/workflows/CI/badge.svg
    :alt: Build Status
    :target: https://github.com/alexfikl/papis-uefiscdi/actions?query=branch%3Amain+workflow%3ACI

papis-uefiscdi
==============

This library handles downloading data from the `UEFISCDI <https://uefiscdi.gov.ro/>`__
(the main research financing body in Romania) and trasforming it into a more open
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

The `papis <https://github.com/papis/papis>`__ plugin that comes with it allows
for easy management of the data and adding it to existing documents in a Papis
database. For example, add AIS scores to documents, use

.. code:: sh

    papis uefiscdi --database jif <QUERY>

This command will match the journal of each document in the query against those
in the JIF database and add appropriate fields to the document. If an ISSN or
an eISSN is available in the document, those will take priority. To see a list
of all databases, run

.. code:: sh

   papis uefiscdi --list-databases

Configuration options
=====================

This command uses the ``uefiscdi`` section for its configuration options. Then
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

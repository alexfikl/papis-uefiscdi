.. image:: https://github.com/alexfikl/papis-uefiscdi/workflows/CI/badge.svg
    :alt: Build Status
    :target: https://github.com/alexfikl/papis-uefiscdi/actions?query=branch%3Amain+workflow%3ACI

papis-uefiscdi
==============

This library handles downloading data from the `UEFISCDI` and trasforming it into
a more open and easy to manipulate format (e.g. CSV). The plugin supports obtaining:

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
database. For example, to download the latest data

.. code::

    papis uefiscdi update --format jif [url]

which can then be added to existing documents using

.. code::

    papis uefiscdi add --from jif [QUERY]

This command will match the journal of each document in the query against those
in the JIF database and add appropriate fields to the document. If an ISSN or
an eISSN is available in the document, those will take priority.

Configuration options
=====================

TODO

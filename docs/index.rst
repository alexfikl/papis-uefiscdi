UEFISCDI
========

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

Command
=======

This package contains a `Papis <https://github.com/papis/papis>`__ plugin that
allows for easy management of UEFISCDI data and adding it to existing documents
in a Papis database.

Examples
--------

Configuration Options
---------------------

Command-line Interface
----------------------

.. click:: papis_uefiscdi.command:cli
    :prog: papis uefiscdi

Library
=======

.. automodule:: papis_uefiscdi.uefiscdi

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

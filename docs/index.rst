UEFISCDI
========

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

Command
=======

This package contains a `Papis <https://github.com/papis/papis>`__ plugin that
allows for easy management of UEFISCDI data and adding it to existing documents
in a Papis database. When used, the command will add the following keys to the
document:

* ``uefiscdi_ais_quartile``: for the AIS quartile.
* ``uefiscdi_jif_quartile``: for the JIF quartile.
* ``uefiscdi_ais_score``: for the AIS score.
* ``uefiscdi_rif_score``: for the RIF score.
* ``uefiscdi_ris_score``: for the RIS score.

Examples
--------

* To download and index the available databases, run

  .. code:: sh

      papis uefiscdi index --year 2024

  This call should be performed before adding or searching any database. It will
  not be performed automatically.

* To add the Article Impact Score (AIS) score to a document

  .. code:: sh

      papis uefiscdi add --database ais <QUERY>

  If the chosen database has not yet been downloaded, you need to call
  ``papis uefiscdi index --database ais`` first.

* To explore the various databases, use

  .. code:: sh

      papis uefiscdi search --database ais <JOURNAL>

  which allows searching for journal names. Other entries of the entry can be
  searched in a similar fashion, e.g. ISSN or Web of Science categories.

Configuration Options
---------------------

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

Command-line Interface
----------------------

.. click:: papis_uefiscdi.command:cli
    :prog: papis uefiscdi
    :nested: full

Library
=======

.. automodule:: papis_uefiscdi.uefiscdi

.. automodule:: papis_uefiscdi.config

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

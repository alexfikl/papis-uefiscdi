# SPDX-FileCopyrightText: 2020-2024 Alexandru Fikl <alexfikl@gmail.com>
# SPDX-License-Identifier: CC0-1.0

# {{{ Project information

from importlib import metadata

m = metadata.metadata("papis_uefiscdi")
project = m["Name"]
author = m["Author-email"]
copyright = f"2023 {author}"  # noqa: A001
version = m["Version"]
release = version

# }}}

# {{{ General configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_click.ext",
]

# extension for source files
source_suffix = ".rst"
# name of the main (master) document
master_doc = "index"
# min sphinx version
needs_sphinx = "4.0"
# files to ignore
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
# highlighting
pygments_style = "sphinx"
# language
language = "en"

html_theme = "sphinx_book_theme"
html_title = project
html_theme_options = {
    "show_toc_level": 2,
    "use_source_button": True,
    "use_repository_button": True,
    "repository_url": "https://github.com/alexfikl/papis-uefiscdi",
    "repository_branch": "main",
}

# autodoc settings
autoclass_content = "class"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": None,
    "show-inheritance": None,
}

#  links
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "papis": ("https://papis.readthedocs.io/en/latest/", None),
}

nitpick_ignore_regex = [
    # https://github.com/sphinx-doc/sphinx/issues/13178
    ["py:class", r"pathlib._local.Path"],
    ]

# }}}

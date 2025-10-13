PYTHON := "python -X dev"

_default:
    @just --list

# {{{ formatting

alias fmt: format

[doc("Reformat all source code")]
format: isort black pyproject justfmt

[doc("Run ruff isort fixes over the source code")]
isort:
    ruff check --fix --select=I src test docs
    ruff check --fix --select=RUF022 src
    @echo -e "\e[1;32mruff isort clean!\e[0m"

[doc("Run ruff format over the source code")]
black:
    ruff format src test docs
    @echo -e "\e[1;32mruff format clean!\e[0m"

[doc("Run pyproject-fmt over the configuration")]
pyproject:
    {{ PYTHON }} -m pyproject_fmt \
        --indent 4 --max-supported-python "3.13" \
        pyproject.toml
    @echo -e "\e[1;32mpyproject clean!\e[0m"

[doc("Run just --fmt over the justfiles")]
justfmt:
    just --unstable --fmt
    @echo -e "\e[1;32mjust --fmt clean!\e[0m"

# }}}
# {{{ linting

[doc("Run all linting checks over the source code")]
lint: typos reuse ruff mypy

[doc("Run typos over the source code and documentation")]
typos format="brief":
    typos --sort --format={{ format }}
    @echo -e "\e[1;32mtypos clean!\e[0m"

[doc("Check REUSE license compliance")]
reuse:
    {{ PYTHON }} -m reuse lint
    @echo -e "\e[1;32mREUSE compliant!\e[0m"

[doc("Run ruff checks over the source code")]
ruff:
    ruff check src test docs
    @echo -e "\e[1;32mruff clean!\e[0m"

[doc("Run mypy checks over the source code")]
mypy:
    {{ PYTHON }} -m mypy src
    @echo -e "\e[1;32mmypy clean!\e[0m"

# }}}
# {{{ pin

[private]
requirements_build_txt:
    uv pip compile --upgrade --universal --python-version "3.10" \
        -o .ci/requirements-build.txt .ci/requirements-build.in

[private]
requirements_dev_txt:
    uv pip compile --upgrade --universal --python-version "3.10" \
        --extra papis --extra dev --extra docs \
        -o .ci/requirements-dev.txt pyproject.toml

[private]
requirements_txt:
    uv pip compile --upgrade --universal --python-version "3.10" \
        -o requirements.txt pyproject.toml

[private]
requirements_docs_txt:
    uv pip compile --upgrade --universal --python-version "3.10" \
        --extra papis --extra docs \
        -o docs/requirements.txt pyproject.toml

[doc("Pin dependency versions to requirements.txt")]
pin: requirements_txt requirements_dev_txt requirements_build_txt requirements_docs_txt

# }}}
# {{{ develop

[doc("Install project in editable mode")]
develop:
    @rm -rf build
    @rm -rf dist
    {{ PYTHON }} -m pip install \
        --verbose \
        --no-build-isolation \
        --editable .

[doc("Editable install using pinned dependencies from requirements-dev.txt")]
pip-install:
    {{ PYTHON }} -m pip install --verbose --requirement .ci/requirements-build.txt
    {{ PYTHON }} -m pip install \
        --verbose \
        --requirement .ci/requirements-dev.txt \
        --no-build-isolation \
        --editable .

[doc("Remove various build artifacts")]
clean:
    rm -rf *.png
    rm -rf build dist
    rm -rf docs/build.sphinx

[doc("Remove various temporary files and caches")]
purge: clean
    rm -rf .ruff_cache .pytest_cache .pytest-cache .mypy_cache tags

[doc("Regenerate ctags")]
ctags:
    ctags --recurse=yes \
        --tag-relative=yes \
        --exclude=.git \
        --exclude=docs \
        --python-kinds=-i \
        --language-force=python

# }}}
# {{{ tests

[doc("Run pytest tests")]
test *PYTEST_ADDOPTS:
    {{ PYTHON }} -m pytest \
        --junit-xml=pytest-results.xml \
        {{ PYTEST_ADDOPTS }}

# }}}

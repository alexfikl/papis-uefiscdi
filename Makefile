PYTHON?=python -X dev
PYTEST_ADDOPTS?=

all: help

help: 			## Show this help
	@echo -e "Specify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

# {{{ linting

format: pyproject isort black				## Run all formatting scripts
.PHONY: format

fmt: format
.PHONY: fmt

pyproject:		## Run pyproject-fmt over the configuration
	$(PYTHON) -m pyproject_fmt --indent 4 pyproject.toml
	@echo -e "\e[1;32mpyproject clean!\e[0m"
.PHONY: pyproject

isort:			## Run ruff isort fixes over the source code
	ruff check --fix --select=I src test docs
	ruff check --fix --select=RUF022 src
	@echo -e "\e[1;32mruff isort clean!\e[0m"
.PHONY: isort

black:			## Run ruff format over the source code
	ruff format src test docs
	@echo -e "\e[1;32mruff format clean!\e[0m"
.PHONY: black

lint: typos reuse ruff mypy				## Run all linting checks

typos:			## Run typos over the source code and documentation
	@typos
	@echo -e "\e[1;32mtypos clean!\e[0m"
.PHONY: typos

reuse:			## Check REUSE license compliance
	$(PYTHON) -m reuse lint
	@echo -e "\e[1;32mREUSE compliant!\e[0m"
.PHONY: reuse

ruff:			## Run ruff checks over the source code
	ruff check src test
	@echo -e "\e[1;32mruff clean!\e[0m"
.PHONY: ruff

mypy:			## Run mypy checks over the source code
	$(PYTHON) -m mypy src test
	@echo -e "\e[1;32mmypy (strict) clean!\e[0m"
.PHONY: mypy

# }}}

# {{{ testing

REQUIREMENTS=\
	requirements.txt \
	requirements-dev.txt \
	docs/requirements.txt

requirements.txt: pyproject.toml
	uv pip compile --upgrade --resolution highest --python-version '3.10' \
		-o $@ $<
.PHONY: requirements.txt

requirements-dev.txt: pyproject.toml
	uv pip compile --upgrade --resolution highest --python-version '3.10' \
		--extra dev --extra docs \
		-o $@ $<
.PHONY: requirements-dev.txt

docs/requirements.txt: pyproject.toml
	uv pip compile --upgrade --resolution highest --python-version '3.10' \
		--extra docs \
		-o $@ $<
.PHONY: docs/requirements.txt

pin: $(REQUIREMENTS) 	## Pin dependencies versions to requirements.txt
.PHONY: pin

pip-install:			## Install pinned dependencies from requirements.txt
	$(PYTHON) -m pip install --upgrade pip hatchling wheel
	$(PYTHON) -m pip install -r requirements-dev.txt -e .
.PHONY: pip-install

pytest:		## Run pytest tests
	$(PYTHON) -m pytest -rswx -v -s --durations=25 test
.PHONY: pytest

# }}}

ctags:			## Regenerate ctags
	ctags --recurse=yes \
		--tag-relative=yes \
		--exclude=.git \
		--exclude=docs \
		--exclude=.ruff_cache \
		--exclude=.mypy_cache \
		--exclude=.pytest_cache \
		--python-kinds=-i \
		--language-force=python
.PHONY: ctags

clean:						## Remove various build artifacts
	rm -rf build dist
	rm -rf docs/_build
.PHONY: clean

purge: clean				## Remove various temporary files
	rm -rf .ruff_cache .pytest_cache .mypy_cache
.PHONY: purge

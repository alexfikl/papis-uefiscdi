PYTHON?=python -X dev
PYTEST_ADDOPTS?=

all: help

help: 			## Show this help
	@echo -e "Specify a command. The choices are:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help

# {{{ linting

format: black isort		## Run all formatting scripts
	$(PYTHON) -m pyproject_fmt --indent 4 pyproject.toml
	@echo -e "\e[1;32msetup formatted!\e[0m"
.PHONY: format

fmt: format
.PHONY: fmt

black:			## Run black over the source code
	$(PYTHON) -m black \
		--safe --target-version py39 --preview \
		papis_uefiscdi test
	@echo -e "\e[1;32mblacked!\e[0m"
.PHONY: black

isort:			## Run isort over the source code
	$(PYTHON) -m isort papis_uefiscdi test
	@echo -e "\e[1;32misorted!\e[0m"
.PHONY: isort

ruff:			## Run ruff checks over the source code
	ruff check papis_uefiscdi test
	@echo -e "\e[1;32mruff clean!\e[0m"
.PHONY: ruff

mypy:			## Run mypy checks over the source code
	$(PYTHON) -m mypy --strict --show-error-codes papis_uefiscdi test
	@echo -e "\e[1;32mmypy (strict) clean!\e[0m"
.PHONY: mypy

codespell:		## Run codespell checks over the documentation
	@codespell --summary \
		--skip _build \
		--ignore-words .codespell-ignore \
		papis_uefiscdi test
.PHONY: codespell

reuse:			## Check REUSE license compliance
	$(PYTHON) -m reuse lint
	@echo -e "\e[1;32mREUSE compliant!\e[0m"
.PHONY: reuse

# }}}

# {{{ testing

REQUIREMENTS=\
	requirements.txt \
	requirements-dev.txt

requirements.txt: pyproject.toml
	$(PYTHON) -m piptools compile \
		--resolver=backtracking --strip-extras --upgrade \
		-o $@ $<

requirements-dev.txt: pyproject.toml
	$(PYTHON) -m piptools compile \
		--resolver=backtracking --upgrade \
		--extra dev --extra docs \
		-o $@ $<

pin: $(REQUIREMENTS) 	## Pin dependencies versions to requirements.txt
.PHONY: pin

pip-install:	## Install pinned depdencies from requirements.txt
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
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
		--python-kinds=-i \
		--language-force=python
.PHONY: ctags

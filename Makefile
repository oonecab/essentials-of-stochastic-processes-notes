.PHONY: help doctor check check-fast check-stochastic check-weiss figures build serve
PYTHON ?= python3

help:
	@$(PYTHON) tools/project.py --help

doctor:
	$(PYTHON) tools/project.py doctor

check:
	$(PYTHON) tools/project.py check

check-fast:
	$(PYTHON) tools/project.py check --quick

check-stochastic:
	$(PYTHON) tools/project.py check --book stochastic

check-weiss:
	$(PYTHON) tools/project.py check --book weiss

figures:
	$(MAKE) -C books/weiss/c check

build:
	$(PYTHON) tools/project.py build

serve:
	$(PYTHON) tools/project.py serve

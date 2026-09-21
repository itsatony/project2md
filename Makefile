# project2md — local development gate.
#
# Hosted GitHub Actions is retired for this repository (operator decision,
# 2026-09-19). `make ci-local` is the only gate; it must be at least as strict
# as any CI it replaces. For this repo there WAS no CI to replace -- the single
# workflow only published to PyPI -- so this file is the first gate the package
# has ever had.

VENV    := .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
SRC     := project2md
TESTS   := tests

# A floor, not an equality: the gate must fail loudly if the suite stops
# running rather than pass vacuously on zero collected tests. Raise it when the
# suite grows; never lower it to make a red run green.
MIN_TESTS := 100

.DEFAULT_GOAL := help
.PHONY: help dev-setup ci-local fmt fmt-check lint typecheck test test-floor coverage release-check build clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate: pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -e .
	$(PIP) install --quiet pytest pytest-cov black isort ruff mypy build twine
	@touch $(VENV)/bin/activate

dev-setup: $(VENV)/bin/activate ## Create .venv and install the package + dev tools

ci-local: dev-setup fmt-check lint typecheck test-floor ## THE GATE: format, lint, types, tests
	@echo ""
	@echo "ci-local: PASS"

fmt: dev-setup ## Apply the formatters in place
	$(VENV)/bin/isort $(SRC) $(TESTS)
	$(VENV)/bin/black $(SRC) $(TESTS)

fmt-check: dev-setup ## Formatting check (isort + black, no writes)
	@echo "== format =="
	$(VENV)/bin/isort --check-only --diff $(SRC) $(TESTS)
	$(VENV)/bin/black --check $(SRC) $(TESTS)

lint: dev-setup ## Lint (ruff, rule set pinned in pyproject.toml)
	@echo "== lint =="
	$(VENV)/bin/ruff check $(SRC) $(TESTS)

typecheck: dev-setup ## Type check (mypy; the package is partially annotated)
	@echo "== typecheck =="
	$(VENV)/bin/mypy $(SRC)

test: dev-setup ## Run the test suite
	@echo "== test =="
	$(PY) -m pytest

test-floor: dev-setup ## Run the suite AND fail if fewer than MIN_TESTS ran
	@echo "== test =="
	@$(PY) -m pytest --junitxml=.pytest-report.xml; status=$$?; \
	  if [ $$status -ne 0 ]; then rm -f .pytest-report.xml; exit $$status; fi; \
	  count=$$($(PY) -c "import xml.etree.ElementTree as E;r=E.parse('.pytest-report.xml').getroot();s=r if r.tag=='testsuite' else r[0];print(int(s.get('tests'))-int(s.get('skipped','0')))"); \
	  rm -f .pytest-report.xml; \
	  echo "tests executed: $$count (floor: $(MIN_TESTS))"; \
	  if [ "$$count" -lt "$(MIN_TESTS)" ]; then \
	    echo "FAIL: only $$count tests executed, floor is $(MIN_TESTS)."; \
	    echo "      A suite that collects nothing must not report success."; \
	    exit 1; \
	  fi

coverage: dev-setup ## Run the suite with a coverage report
	$(PY) -m pytest --cov=$(SRC) --cov-report=term-missing

release-check: dev-setup ## Verify version/tag agreement, build, and twine check
	./scripts/release-check.sh

build: dev-setup ## Build the sdist and wheel into dist/
	rm -rf dist build *.egg-info
	$(PY) -m build

clean: ## Remove build and test artifacts
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache .pytest-report.xml
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +

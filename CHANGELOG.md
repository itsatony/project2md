# Changelog

All notable changes to project2md are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before 1.4.0 were not recorded in a changelog; see `git log`.

## [1.4.0] - 2026-09-22

### Added

- **`make ci-local` — the first gate this package has ever had.** Hosted GitHub
  Actions is retired (operator decision, 2026-09-19), and this repository had no
  CI to retire: the only workflow published to PyPI, and nothing ever ran the
  tests, a linter or a type checker on a change. The gate runs formatting
  (`isort` + `black --check`), lint (`ruff`), types (`mypy`) and the test suite,
  and **fails if fewer than `MIN_TESTS` tests execute** so it cannot pass
  vacuously on a suite that stopped collecting.
- `scripts/release-check.sh` / `make release-check`: version ↔ tag agreement,
  a CHANGELOG entry for the version, a clean build, the built artefact names
  carrying that version, and `twine check`. **None of these guards existed
  before**, in the workflow or in `scripts/publish.sh` — a tag and a
  `pyproject.toml` version could disagree silently.
- This CHANGELOG.

### Fixed

- **`project2md explicit` reported every file as excluded.** It called
  `walker._matches_include_exclude()`, a method that does not exist, behind a
  bare `except:` — so every entry in the generated `explicit.config.project2md.yml`
  came out `include: false`, making the command's whole output wrong and silent.
  It now uses the walker's real `_should_process_path()`, with the include and
  exclude specs actually built first, and no longer walks `.git/`.
- **Neither pytest config was in effect.** `pytest.ini` used the `setup.cfg`
  section header (`[tool:pytest]`), so pytest read none of its options — and
  because the file still counted as the configfile, it also shadowed the
  `[tool.pytest.ini_options]` block in `pyproject.toml`. `--strict-markers`, the
  marker registrations and `--tb=short` were all inert. `pytest.ini` is removed
  and `pyproject.toml` is now the single authority.
- `Config.target_dir` defaulted to `Path.cwd()` evaluated once at import time,
  freezing the interpreter's startup directory; it is now a `default_factory`.
- `FileSystemWalker.read_file()` could pass `None` to `bytes.decode()` when
  chardet reported a confident detection with no encoding name.
- `get_version()` rebound the imported `importlib.metadata.version` symbol as a
  local, so name resolution inside the function depended on which branch ran.
- Exceptions raised while handling another exception now chain (`raise ... from`),
  21 sites, so tracebacks keep the original cause.

### Changed

- Whole tree formatted with `black` and `isort` (`line-length = 100`); the ruff
  rule set is pinned in `pyproject.toml` so the gate answers the same on every
  machine.
- Dev dependencies: `pylint` (declared for years, never configured, never run)
  replaced by `ruff` and `mypy`; `build` and `twine` added for the release gate.
- `scripts/publish.sh` now runs `release-check.sh` first and asks before
  uploading.

### Removed

- `.github/workflows/publish.yml` moved to `.github/workflows-disabled/`, with a
  README explaining what it did, where its work went and how to re-enable it.
  Actions is also disabled at the repository level.
- Dead duplicate formatters `project2md/formatters/{markdown,json,yaml}.py`.
  Nothing imported them — the package uses `*_formatter.py` — and all three
  referenced a `self.console` attribute that `BaseFormatter` does not define, so
  they would have raised `AttributeError` if they ever had been used.

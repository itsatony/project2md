#!/usr/bin/env bash
#
# Publish project2md to PyPI.
#
# This is the ONLY publish path. `.github/workflows/publish.yml` used to do the
# same thing on a GitHub release and is now inert (see
# .github/workflows-disabled/README.md) -- hosted GitHub Actions is retired for
# this repository.
#
# The guards live in scripts/release-check.sh and run first: version<->tag
# agreement, CHANGELOG entry, build, artefact-name check, twine check. Neither
# the workflow nor this script had any of them before.
#
# Usage:
#   scripts/publish.sh            # publish the version on HEAD's tag
#   scripts/publish.sh v1.4.0     # publish, asserting the tag explicitly
#
set -euo pipefail

cd "$(dirname "$0")/.."

./scripts/release-check.sh "${1:-}"

if [[ -x .venv/bin/python ]]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo
read -r -p "Upload dist/* to PyPI? [y/N] " answer
case "${answer}" in
  y|Y|yes|YES) ;;
  *) echo "aborted."; exit 1 ;;
esac

"${PY}" -m twine upload dist/*

#!/usr/bin/env bash
#
# release-check.sh -- the guards that used to live nowhere.
#
# `.github/workflows/publish.yml` built and uploaded on a GitHub release, and
# `scripts/publish.sh` built and uploaded by hand. NEITHER ever compared the
# version being released to the version in pyproject.toml, so "tag v1.4.0,
# upload 1.3.0" was silent -- PyPI would simply reject it as a duplicate, or,
# worse, accept the wrong number. This script is that missing guard, plus the
# build and `twine check` the workflow did.
#
# Usage:
#   scripts/release-check.sh              # check against the tag on HEAD, if any
#   scripts/release-check.sh v1.4.0       # check against an explicit tag
#
set -euo pipefail

cd "$(dirname "$0")/.."

VENV_BIN=".venv/bin"
if [[ -x "${VENV_BIN}/python" ]]; then
  PY="${VENV_BIN}/python"
else
  PY="python3"
fi

fail() { echo "release-check: FAIL: $*" >&2; exit 1; }
ok()   { echo "release-check: ok: $*"; }

# --- 1. the declared version -------------------------------------------------
PKG_VERSION="$("${PY}" - <<'PYEOF'
import sys, tomllib, pathlib
data = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
version = data.get("project", {}).get("version")
if not version:
    sys.exit("no [project].version in pyproject.toml")
print(version)
PYEOF
)"
ok "pyproject.toml declares ${PKG_VERSION}"

# --- 2. version <-> tag agreement -------------------------------------------
TAG="${1:-}"
if [[ -z "${TAG}" ]]; then
  TAG="$(git describe --exact-match --tags HEAD 2>/dev/null || true)"
fi

if [[ -z "${TAG}" ]]; then
  echo "release-check: note: HEAD carries no tag and none was given;"
  echo "               skipping the version<->tag comparison."
  echo "               Pass the tag explicitly before publishing:"
  echo "                 scripts/release-check.sh v${PKG_VERSION}"
else
  TAG_VERSION="${TAG#v}"
  if [[ "${TAG_VERSION}" != "${PKG_VERSION}" ]]; then
    fail "tag ${TAG} means version ${TAG_VERSION}, but pyproject.toml says ${PKG_VERSION}."
  fi
  ok "tag ${TAG} agrees with pyproject.toml"
fi

# --- 3. the CHANGELOG mentions this version ----------------------------------
if [[ -f CHANGELOG.md ]]; then
  if grep -q "\[${PKG_VERSION}\]" CHANGELOG.md; then
    ok "CHANGELOG.md has an entry for ${PKG_VERSION}"
  else
    fail "CHANGELOG.md has no [${PKG_VERSION}] entry."
  fi
fi

# --- 4. build ----------------------------------------------------------------
rm -rf dist build ./*.egg-info
"${PY}" -m build >/dev/null
ok "built sdist + wheel"

# --- 5. the built artefacts carry the declared version -----------------------
# A build backend reading a different version field than step 1 would be
# invisible to the comparison above; this checks what actually gets uploaded.
for artefact in dist/*; do
  case "$(basename "${artefact}")" in
    *"${PKG_VERSION}"*) ;;
    *) fail "built artefact $(basename "${artefact}") does not carry ${PKG_VERSION}" ;;
  esac
done
ok "dist/ artefacts carry ${PKG_VERSION}: $(ls dist | tr '\n' ' ')"

# --- 6. twine check ----------------------------------------------------------
"${PY}" -m twine check dist/*
ok "twine check passed"

echo "release-check: PASS (${PKG_VERSION})"

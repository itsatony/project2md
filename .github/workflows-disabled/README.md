# Disabled GitHub Actions workflows

Hosted GitHub Actions is **retired for this repository** by operator decision
(2026-09-19). Every check runs locally, in a gate at least as complete and
strict as the CI it replaces — here, `make ci-local`.

Actions is also disabled at the **repository** level, not just by moving files.
Moving a workflow out of `.github/workflows/` makes *that file* inert; it does
not stop a newly added or restored workflow from running. Both were done:

```bash
gh api -X PATCH repos/itsatony/project2md/actions/permissions -F enabled=false
```

The workflows are kept here rather than deleted: they are the specification the
local gate is compared against.

## `publish.yml`

**What it did:** on a GitHub release, set up Python, `pip install build twine`,
then `python -m build` and `twine upload dist/*` with `PYPI_API_TOKEN`.

**Was it load-bearing?** Partly. It was the automatic publish path, but it had
no guards at all — in particular it never compared the released tag to the
version in `pyproject.toml`, so tagging `v1.4.0` while `pyproject.toml` still
said `1.3.5` would have uploaded `1.3.5` silently.

**Where its work lives now:** `scripts/publish.sh`, which already did the same
build-and-upload by hand. Retiring the workflow therefore removes an
*automatic* trigger, not a capability — publishing becomes a deliberate local
command. The guards the workflow lacked were added on the way out, in
`scripts/release-check.sh` (also `make release-check`):

1. the version declared in `pyproject.toml`,
2. that version against the git tag (HEAD's tag, or one passed explicitly),
3. a `CHANGELOG.md` entry for that version,
4. a clean `python -m build`,
5. the built artefact filenames actually carrying that version,
6. `twine check dist/*`.

**To publish now:**

```bash
git tag v1.4.0 && make release-check   # or: scripts/release-check.sh v1.4.0
scripts/publish.sh v1.4.0              # runs the guards, then asks before uploading
```

`TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<pypi token>` come from the
publisher's environment; the `PYPI_API_TOKEN` repository secret is no longer
read by anything and can be revoked.

## Re-enabling

Re-enabling is two steps, and **both** are required:

```bash
git mv .github/workflows-disabled/publish.yml .github/workflows/publish.yml
gh api -X PATCH repos/itsatony/project2md/actions/permissions -F enabled=true
```

If you do re-enable it, port the `release-check.sh` guards into the workflow
first — otherwise the version/tag mismatch it never caught comes back.

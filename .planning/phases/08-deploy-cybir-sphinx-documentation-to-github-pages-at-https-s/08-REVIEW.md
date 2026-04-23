---
phase: 08-deploy-cybir-sphinx-documentation-to-github-pages
reviewed: 2026-04-23T00:00:00Z
depth: quick
files_reviewed: 9
files_reviewed_list:
  - pyproject.toml
  - documentation/source/conf.py
  - cybir/core/coxeter.py
  - cybir/core/ekc.py
  - cybir/core/types.py
  - documentation/source/index.rst
  - .github/workflows/docs.yml
  - README.md
  - .gitignore
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-04-23
**Depth:** quick
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 8 is a documentation-infrastructure phase. The review is scoped to:
(a) the new `[docs]` optional-dependency extra in `pyproject.toml`, (b) the
`autodoc_mock_imports` addition in `conf.py`, (c) the notebook symlinks +
Examples toctree entry in `index.rst`, (d) the new GitHub Actions workflow
`docs.yml`, and (e) six docstring prose `|W|` → `` :math:`|W|` `` replacements
in `coxeter.py`, `ekc.py`, and `types.py`.

Overall assessment: changes are clean and minimal. No critical issues. Two
warnings concern the CI workflow's deploy-step gating and build/deploy
coupling. Three info items note minor robustness and dependency-hygiene
considerations.

The six docstring math replacements are correct and consistent: I verified
via `grep '|W|'` that every remaining bare `|W|` occurrence is in an f-string
or a log-format message (runtime output, not Sphinx markup) — exactly where
`:math:` would be wrong. All docstring `|W|` instances are now
`` :math:`|W|` ``.

## Warnings

### WR-01: Deploy step runs inside the build job — a flaky deploy can mask build success

**File:** `.github/workflows/docs.yml:14-48`
**Issue:** The `build` job (line 14) both builds HTML and deploys to
`gh-pages` via `peaceiris/actions-gh-pages@v4` (lines 41-48). Because the
deploy step is part of the same job, a transient failure of the deploy
action (e.g., token rate-limit, network blip) will mark the whole `docs`
workflow run as failed even though the docs built fine. Conversely, PR
builds run the full job up to the deploy step and then skip it via the
`if:` guard — which is fine, but it means PR status checks and
main-branch status checks share the same job name, coupling two concerns.
Not a correctness bug, but a hygiene issue worth noting for a
documentation-deployment workflow.
**Fix:** Split into two jobs, with `deploy` needing `build`:
```yaml
jobs:
  build:
    name: Build Sphinx docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: |
          python -m pip install --upgrade pip
          pip install -e .[docs]
      - run: sphinx-build -b html -W --keep-going documentation/source documentation/build/html
      - run: touch documentation/build/html/.nojekyll
      - uses: actions/upload-pages-artifact@v3
        with:
          path: documentation/build/html

  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```
This also switches to GitHub's first-party Pages actions, which avoids
the `contents: write` permission on the build job (see WR-02).

### WR-02: `contents: write` is granted to the build job, not scoped to deploy

**File:** `.github/workflows/docs.yml:17-18`
**Issue:** The top-level `permissions` block sets `contents: read` (line
11), but the `build` job overrides it with `contents: write` (line 18)
"so the deploy step can push to gh-pages." This means every step in the
job — including `pip install` of the entire `[docs]` extra tree — runs
with write access to repo contents. On PRs originating from forks this
permission is automatically downgraded by GitHub, so it is not a
supply-chain CVE, but it is broader scoping than necessary. A PR build
does not deploy but still runs with `contents: write`.
**Fix:** Either (a) split build/deploy into separate jobs (see WR-01) so
only the deploy job needs elevated permissions, or (b) at minimum, gate
the elevated permission on the deploy condition. Option (a) is cleaner.

## Info

### IN-01: `sphinx-build -W` with `[docs]` extra but no explicit Sphinx version floor check

**File:** `pyproject.toml:26-34`, `.github/workflows/docs.yml:36`
**Issue:** `pyproject.toml` pins `sphinx>=7.0` and related extensions with
floor-only bounds (no upper bounds). The workflow runs
`sphinx-build -W --keep-going` on whatever resolver picks at build time.
If a future Sphinx or extension release introduces a new warning
category (deprecation, etc.), CI goes red without code changes and
main-branch docs stop deploying. This is the standard `-W` trade-off,
not a bug, but worth noting for a doc pipeline that is expected to
deploy on every push.
**Fix:** Optional — either pin upper bounds in the `[docs]` extra (e.g.,
`"sphinx>=7.0,<9"`), or add a `--pip-cache` with a manually-curated
constraints file. Alternatively accept the risk and treat CI breakage as
a signal to update extension versions.

### IN-02: `peaceiris/actions-gh-pages@v4` is a third-party action

**File:** `.github/workflows/docs.yml:43`
**Issue:** `peaceiris/actions-gh-pages@v4` is pinned to a major version
tag, not a full commit SHA. GitHub Actions best practice for third-party
actions in workflows with write permissions is to pin by full 40-char
SHA (mutable `v4` tag could in principle be re-pointed to a malicious
commit). First-party actions (`actions/checkout`, `actions/setup-python`)
are also `@v4` / `@v5` tag-pinned, which is standard for first-party.
This is a hygiene note, not a live vulnerability.
**Fix:** Optional — replace with `peaceiris/actions-gh-pages@<sha>` or
switch to the first-party `actions/deploy-pages@v4` flow (see WR-01
snippet), which avoids third-party write access to `gh-pages` entirely.

### IN-03: `autodoc_mock_imports` list is minimal and correct, but no test guard

**File:** `documentation/source/conf.py:27`
**Issue:** `autodoc_mock_imports = ["cytools", "regfans"]` is the right
pair — these are the non-PyPI runtime imports used inside
`cybir/core/*.py` that would otherwise break `pip install -e .[docs]`
on CI. I grepped the three reviewed core files and confirmed
`import cytools` appears in `coxeter.py` (inside `reflect_phase_data`,
line 705) and `ekc.py` (effective/infinity/extended_kahler_cone
methods). There is no `import regfans` in the reviewed files, but the
plan indicates it is imported elsewhere (e.g., `toric_curves.py`) —
accepted on faith per the "do not review unchanged logic" scope rule.
If a future core module adds another non-PyPI import (e.g., a CGAL
binding), the docs build will fail with an import error, not a missing-
reference warning, because `-W` treats Sphinx warnings as errors but
autodoc import failures still surface as build errors.
**Fix:** No change required. Consider a short comment in `conf.py`
documenting the policy ("mock any non-PyPI runtime import used in
cybir/core/") so future maintainers know to update this list.

---

_Reviewed: 2026-04-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_

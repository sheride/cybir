---
phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s
plan: 01
subsystem: docs
tags: [sphinx, autodoc, myst-nb, sphinx-book-theme, pyproject-toml, github-pages]

# Dependency graph
requires:
  - phase: 03-pipeline-integration
    provides: Initial Sphinx docs scaffolding (conf.py, index.rst, theme, extensions, notebook symlink pattern)
provides:
  - "[project.optional-dependencies.docs] extra in pyproject.toml with seven pinned Sphinx deps"
  - "autodoc_mock_imports = [\"cytools\", \"regfans\"] narrowly scoped to grep-verified lazy imports"
  - "documentation/source/_static/ directory (checked in via .gitkeep) satisfying html_static_path"
  - "Clean sphinx-build -W build in the cytools conda env — CI for Plan 03 can now call the same command"
  - "RST-safe docstrings for |W| (as :math:`|W|`) in cybir/core/{coxeter,ekc,types}.py"
affects: [08-02, 08-03]

# Tech tracking
tech-stack:
  added:
    - "sphinx>=7.0, sphinx-book-theme>=1.0, myst-nb>=1.0, sphinx-autodoc-typehints>=2.0, sphinx-copybutton>=0.5, sphinx_design>=0.5, sphinx-togglebutton>=0.3 (all as docs extra)"
  patterns:
    - "Narrow autodoc_mock_imports — mock only compiled/heavyweight deps that are grep-verified as lazy imports inside function bodies, never module-level"
    - "Prose |W| in docstrings must be wrapped as :math:`|W|` because RST reads `|...|` as a substitution reference (triggers Sphinx -W failure)"

key-files:
  created:
    - ".planning/phases/08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s/08-01-SUMMARY.md"
    - "documentation/source/_static/.gitkeep"
  modified:
    - "pyproject.toml"
    - "documentation/source/conf.py"
    - "cybir/core/coxeter.py"
    - "cybir/core/ekc.py"
    - "cybir/core/types.py"

key-decisions:
  - "Seven docs-extra deps match CLAUDE.md tech stack exactly; no cytools in extras (documented as prerequisite)"
  - "autodoc_mock_imports kept to [\"cytools\", \"regfans\"] only — flint is unused in cybir and hsnf is pure-Python (both grep-verified); over-mocking would mask real autodoc errors"
  - "Created documentation/source/_static/ (with .gitkeep) rather than removing html_static_path entry — keeps conf.py aligned with the rest of the project Sphinx setup and leaves room for future static assets"
  - "Prose |W| fixes in core source files (coxeter.py, ekc.py, types.py) accepted as user-approved scope extension rather than a per-plan deviation, because -W cannot pass without them and editing only docstrings keeps mathematical code untouched"

patterns-established:
  - "docs extra + pip install -e .[docs] is the single source of truth for doc-build deps (no requirements-docs.txt duplication)"
  - "Docstring math convention: use :math:`...` for inline math whose Unicode/text form would collide with RST markup (e.g. |W|, |G|, |M|)"

requirements-completed: []

# Metrics
duration: 20min
completed: 2026-04-23
---

# Phase 8 Plan 1: Sphinx Docs Build Foundation Summary

**docs optional extra in pyproject.toml + autodoc_mock_imports in conf.py — sphinx-build -W now exits 0 in the cytools conda env, de-risking the CI deploy in Plan 03**

## Performance

- **Duration:** ~20 min (including checkpoint pause for user decision on docstring scope)
- **Started:** 2026-04-23T18:20:10Z (prior executor)
- **Completed:** 2026-04-23T19:10:00Z
- **Tasks:** 2 planned + 1 user-approved scope extension (prose `|W|` fixes)
- **Files modified:** 5 (+ 1 created: `_static/.gitkeep`)

## Accomplishments

- `[project.optional-dependencies.docs]` added to `pyproject.toml` with the exact seven pinned Sphinx deps from D-14 in `08-CONTEXT.md`; `pip install -e .[docs]` succeeds in the cytools env.
- `autodoc_mock_imports = ["cytools", "regfans"]` added to `conf.py` (D-10); autodoc can now introspect every `cybir` module without the compiled CYTools/regfans stack.
- `documentation/source/_static/` created (tracked via `.gitkeep`) so `html_static_path = ["_static"]` resolves cleanly.
- Six prose `|W|` docstring occurrences wrapped as `:math:`|W|`` across `cybir/core/{coxeter,ekc,types}.py`; RST no longer mistakes them for substitution references.
- `sphinx-build -b html -W source build/html` exits **0** with zero warnings; `documentation/build/html/index.html` and `documentation/build/html/_static/` both produced.

## Actual deps written to pyproject.toml

```toml
docs = [
    "sphinx>=7.0",
    "sphinx-book-theme>=1.0",
    "myst-nb>=1.0",
    "sphinx-autodoc-typehints>=2.0",
    "sphinx-copybutton>=0.5",
    "sphinx_design>=0.5",
    "sphinx-togglebutton>=0.3",
]
```

## Actual line added to conf.py

```python
autodoc_mock_imports = ["cytools", "regfans"]
```

Placed directly after the `extensions = [...]` list closes and before `templates_path`. No other settings in `conf.py` were modified (extensions list, `nb_execution_mode = "off"`, `html_theme`, etc. all preserved verbatim).

## Task Commits

Atomic per task plus one scope-extension commit:

1. **Task 1: Add [project.optional-dependencies.docs] to pyproject.toml** — `1151617` (chore)
2. **Task 2 (conf.py + _static dir): Add autodoc_mock_imports and create _static directory** — `d5f2028` (feat)
3. **Approved scope extension: prose |W| docstring fixes** — `3835180` (docs)

## Files Created/Modified

- `pyproject.toml` — added `docs` extra with seven pinned Sphinx deps (commit `1151617`).
- `documentation/source/conf.py` — added one line `autodoc_mock_imports = ["cytools", "regfans"]` (commit `d5f2028`).
- `documentation/source/_static/.gitkeep` — created empty placeholder so `html_static_path = ["_static"]` resolves under `-W` (commit `d5f2028`).
- `cybir/core/coxeter.py` — wrapped four prose `|W|` sites as `:math:`|W|`` (docstring bullet, `coxeter_group_order` Parameters/Returns, `enumerate_coxeter_group` Parameters). Logger `|W|` sites at lines 822/845/970 left untouched (commit `3835180`).
- `cybir/core/ekc.py` — wrapped one prose `|W|` site (`CYBirationalClass.coxeter_order` docstring). Logger f-string sites at lines 879/891 left untouched (commit `3835180`).
- `cybir/core/types.py` — wrapped one prose `|W|` site (`CoxeterGroup.order` docstring) (commit `3835180`).

## Decisions Made

- Kept the mock list narrow (`["cytools", "regfans"]`) rather than defensively widening it — future genuine autodoc import errors (e.g. a missing internal module) will surface instead of being silently mocked away. Per D-10 + T-08-02.
- Created `_static/` rather than dropping `html_static_path` from `conf.py` — keeps the Sphinx theme/setup consistent with other cybir docs pages and reserves a location for future logo/CSS/JS assets without touching conf.

## Deviations from Plan

### Approved Scope Extension

**[User-approved during checkpoint] Prose `|W|` wrapped as `:math:\`|W|\`` + `_static/` created**

- **Found during:** Task 2 verification. First `-W` build failed with six `inline substitution reference not found: W` warnings plus one `html_static_path entry '_static' does not exist` warning — seven pre-existing RST correctness issues in the codebase that only became visible once `-W` was enabled.
- **Checkpoint outcome:** User selected Option B ("fix the six prose `|W|` docstring sites directly in `cybir/core/` source files, plus create `_static/.gitkeep`") — explicitly said: "Just do B. now — it's okay that you're doing this tiny tweak in core files. don't need a new plan i don't think."
- **Fix (representative before/after — `cybir/core/ekc.py:436`):**

  Before:
  ```python
  """Order |W| of the Coxeter group, or None.
  ```

  After:
  ```python
  """Order :math:`|W|` of the Coxeter group, or None.
  ```

  Same pattern applied at the five other prose sites:
  - `cybir/core/coxeter.py:13` (module docstring bullet list)
  - `cybir/core/coxeter.py:505` (`coxeter_group_order` first line)
  - `cybir/core/coxeter.py:519` (`coxeter_group_order` Returns description)
  - `cybir/core/coxeter.py:579` (`enumerate_coxeter_group` `expected_order` Parameters description)
  - `cybir/core/types.py:507` (`CoxeterGroup.order` docstring)
- **Explicitly left alone:** logger/f-string `|W|` occurrences at `coxeter.py:822`, `845`, `970` and `ekc.py:879`, `891`. Those strings never reach RST — they're runtime log/print output.
- **`_static/` creation:** `mkdir -p documentation/source/_static` + empty `.gitkeep`. Tracked via git so the directory persists across clones.
- **Files modified:** `cybir/core/coxeter.py`, `cybir/core/ekc.py`, `cybir/core/types.py`, `documentation/source/_static/.gitkeep`.
- **Verification:** `sphinx-build -b html -W source build/html` now exits **0** — see "Final `sphinx-build -W` run" below.
- **Committed in:** `3835180` (docstring fixes) + `d5f2028` (`_static/.gitkeep`).

---

**Total deviations:** 0 auto-fixed (Rule 1/2/3) — the only scope change is the explicitly user-approved extension above.
**Impact on plan:** Zero scope creep beyond what the user green-lit at the checkpoint. All changes stayed within the plan's three named files + the three core source files the user approved + the new `_static/.gitkeep`. Unrelated uncommitted work in the working tree (phase 7 plans, other cybir source edits, notebooks, tests) was not swept into any commit — every commit used explicit `--files` staging.

## Final `sphinx-build -W` run (last 20 lines)

```
writing output... [  6%] cybir
writing output... [ 12%] cybir.core
writing output... [ 19%] cybir.core.build_gv
writing output... [ 25%] cybir.core.classify
writing output... [ 31%] cybir.core.coxeter
writing output... [ 38%] cybir.core.ekc
writing output... [ 44%] cybir.core.flop
writing output... [ 50%] cybir.core.graph
writing output... [ 56%] cybir.core.gv
writing output... [ 62%] cybir.core.patch
writing output... [ 69%] cybir.core.types
writing output... [ 75%] cybir.core.util
writing output... [ 81%] index
writing output... [ 88%] notebooks/h11_2_survey
writing output... [ 94%] notebooks/h11_2_walkthrough
writing output... [100%] notebooks/h11_3_walkthrough

generating indices... genindex py-modindex done
writing additional pages... search done
dumping search index in English (code: en)... done
dumping object inventory... done
build succeeded.

The HTML pages are in build/html.
EXIT_CODE=0
```

Acceptance-criteria spot checks all pass:
- `grep -c 'autodoc_mock_imports' documentation/source/conf.py` → `1`
- `grep -F 'autodoc_mock_imports = ["cytools", "regfans"]' documentation/source/conf.py` → matches
- `grep -c '"flint"' documentation/source/conf.py` → `0`
- `grep -c '"hsnf"' documentation/source/conf.py` → `0`
- `nb_execution_mode = "off"` preserved (D-17 invariant holds)
- `documentation/build/html/index.html` exists
- `documentation/build/html/_static/` exists

## Issues Encountered

- **RST `|W|` substitution collision** — Sphinx `-W` cannot pass until the six prose `|W|` docstring sites are wrapped in `:math:`…``. This is a pre-existing codebase correctness issue that was invisible under the default-warn build. Resolved under the user-approved scope extension above; the fix is mechanically minimal (six docstrings, zero runtime code touched).
- **Working tree had unrelated uncommitted work** in `cybir/core/ekc.py`, `cybir/core/classify.py`, `cybir/core/build_gv.py`, `cybir/core/toric_curves.py`, and elsewhere. Handled by explicit per-file staging (never `git add .`) and, for `ekc.py` specifically, by backing up the user's version, reverting to HEAD, applying only the one-line docstring fix, committing, then restoring the user's work. Result: all three 08-01 commits touch only their intended files, and every pre-existing uncommitted change remains in the working tree exactly as the user left it.

## User Setup Required

None — no external service configuration needed for this plan. Plan 02 will add the notebook symlink and README link; Plan 03 will add the GitHub Actions workflow (which is the plan where the one-time GitHub Pages "Settings → Pages" toggle will be flagged per D-05).

## Next Phase Readiness

- Local `sphinx-build -b html -W source build/html` is green in the cytools conda env. CI in Plan 03 can invoke the exact same command and expect the same result.
- `pip install -e .[docs]` is now the single source of truth for doc-build deps — Plan 03's workflow file should use this verbatim.
- Pattern established: any future prose `|W|`/`|G|`/`|M|` etc. in docstrings must be wrapped as inline math, otherwise `-W` breaks. Worth calling out to contributors in a future `CONTRIBUTING.md`.
- Ready to proceed to Plan 02 (notebook symlink + `index.rst` entry + README link) and then Plan 03 (GitHub Actions deploy).

## Self-Check: PASSED

- `pyproject.toml` present and contains `docs = [` block (committed in `1151617`) — verified.
- `documentation/source/conf.py` present and contains `autodoc_mock_imports = ["cytools", "regfans"]` (committed in `d5f2028`) — verified.
- `documentation/source/_static/.gitkeep` present and tracked (committed in `d5f2028`) — verified.
- `cybir/core/coxeter.py`, `cybir/core/ekc.py`, `cybir/core/types.py` — six prose `|W|` sites wrapped as `:math:`|W|`` (committed in `3835180`) — verified via `git diff --cached` before commit and `git log` after.
- Commits `1151617`, `d5f2028`, `3835180` all present in `git log --oneline 62d51cf..HEAD`.
- `sphinx-build -W` exit code captured as `0`.
- `documentation/build/html/index.html` exists; `documentation/build/html/_static/` exists.

---
*Phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s*
*Completed: 2026-04-23*

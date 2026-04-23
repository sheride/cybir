---
phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s
plan: 02
subsystem: docs
tags: [sphinx, myst-nb, notebook, toctree, symlink]

# Dependency graph
requires:
  - phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s (Plan 01)
    provides: "autodoc_mock_imports in conf.py, _static/ directory, :math:`|W|` docstring fixes — sphinx-build -W exits 0"
provides:
  - "documentation/source/notebooks/h11_3_survey.ipynb as a relative symlink to ../../../notebooks/h11_3_survey.ipynb"
  - "Examples toctree with exactly four entries: h11_2_survey, h11_2_walkthrough, h11_3_survey, h11_3_walkthrough (h11 ascending, survey-before-walkthrough)"
  - "build/html/notebooks/h11_3_survey.html (62,995 bytes) rendered from stored outputs via nb_execution_mode = off"
affects: [08-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Notebook pages are added to documentation via (a) a relative symlink under documentation/source/notebooks/ and (b) a one-line entry in the Examples toctree in index.rst — mirrors the h11_2_survey pattern established in Phase 3"

key-files:
  created:
    - "documentation/source/notebooks/h11_3_survey.ipynb (symlink)"
    - ".planning/phases/08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s/08-02-SUMMARY.md"
  modified:
    - "documentation/source/index.rst"

key-decisions:
  - "Symlink uses exact three-level-up relative target ../../../notebooks/h11_3_survey.ipynb — matches existing h11_2_survey pattern; keeps the repo portable across CI checkouts (T-08-04 accept disposition holds)"
  - "h11_3_survey placed between h11_2_walkthrough and h11_3_walkthrough in the toctree so the four entries read in h11 ascending / survey-before-walkthrough order (D-16)"
  - "Smoke-build acceptance (sphinx-build -W) exercised fully in this plan because Plan 01 already landed; no deferral to Plan 03 CI"

patterns-established:
  - "Add-a-notebook-to-docs recipe: ln -s ../../../notebooks/<name>.ipynb documentation/source/notebooks/<name>.ipynb + one toctree entry + git add the symlink (mode 120000, tracked as symlink not copy)"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-04-23
---

# Phase 8 Plan 2: h11_3 Survey Notebook Wired Into Docs Toctree Summary

**h11_3_survey notebook now reachable from the Examples toctree via a three-level-up relative symlink; sphinx-build -W renders it from stored outputs and produces a 62,995-byte HTML page**

## Performance

- **Duration:** ~5 min active work (wall-clock included two `-W` sphinx rebuilds that dominated the timeline)
- **Started:** 2026-04-23T19:38:28Z
- **Completed:** 2026-04-23T20:32:41Z
- **Tasks:** 2 planned, 2 completed, 0 deviations
- **Files modified:** 1 created (symlink), 1 edited (index.rst)

## Accomplishments

- **Symlink created.** `documentation/source/notebooks/h11_3_survey.ipynb → ../../../notebooks/h11_3_survey.ipynb` — exact shape of the pre-existing h11_2_survey pattern. Tracked by git as mode `120000` (symlink, not copy).
- **Toctree entry added.** `documentation/source/index.rst` Examples toctree now lists four notebooks in the required order.
- **Smoke build green.** `rm -rf build && sphinx-build -b html -W source build/html` exits `0` with zero warnings. `build/html/notebooks/h11_3_survey.html` exists (62,995 bytes).
- **No user-change sweep.** Plan commits touched exactly the two plan files; all of the user's other uncommitted edits (phase 7 plans, cybir core edits, notebooks, tests) remain in the working tree untouched.

## readlink output

```
$ readlink documentation/source/notebooks/h11_3_survey.ipynb
../../../notebooks/h11_3_survey.ipynb
```

Matches the `^\.\./\.\./\.\./notebooks/h11_3_survey\.ipynb$` must-have pattern verbatim.

Resolved target file size check:

```
$ stat -L -f%z documentation/source/notebooks/h11_3_survey.ipynb
72677
$ stat -f%z notebooks/h11_3_survey.ipynb
72677
```

Symlink resolves to the real 72,677-byte notebook — not dangling.

## Final Examples toctree block (verbatim)

```rst
.. toctree::
   :maxdepth: 1
   :caption: Examples

   notebooks/h11_2_survey
   notebooks/h11_2_walkthrough
   notebooks/h11_3_survey
   notebooks/h11_3_walkthrough
```

Three-space indentation matches the pre-existing entries. The API Documentation toctree above it is untouched.

## Smoke-build result

`conda run -n cytools bash -c "cd documentation && rm -rf build && sphinx-build -b html -W source build/html"` → `EXIT_CODE=0`.

Last 10 lines of the `-W` build:

```
writing output... [ 94%] notebooks/h11_3_survey
writing output... [100%] notebooks/h11_3_walkthrough

generating indices... genindex py-modindex done
writing additional pages... search done
copying images... [ 50%] ../build/jupyter_execute/aa89b4250bbbe6e3e35450fe410123a9ea9920086cd1a531ab055fe4c9064ef1.png
copying images... [100%] ../build/jupyter_execute/4dc7fbee1e98034a38796b02bf732fba446a4d2469b54b587575abdfc9b9f786.png

dumping search index in English (code: en)... done
dumping object inventory... done
build succeeded.
```

`h11_3_survey` is rendered at 94% of the write-output pass, alongside the existing three notebooks. Copy-images reports embedded PNG outputs from the stored notebook cells — consistent with `nb_execution_mode = "off"` simply transcoding whatever the `.ipynb` already contains (D-17).

Output artifact checks:

```
$ test -f documentation/build/html/notebooks/h11_3_survey.html && echo OK
OK
$ stat -f%z documentation/build/html/notebooks/h11_3_survey.html
62995
```

Non-empty HTML page, well above the "anything non-trivial" threshold.

## Task Commits

Atomic per task:

1. **Task 1: Create h11_3_survey symlink in documentation/source/notebooks/** — `2811e56` (feat)
2. **Task 2: Add h11_3_survey to Examples toctree in index.rst** — `0b54288` (docs)

Both commits passed files explicitly via `git add <path>` — never `git add .` / `git add -A`. `git log --stat` shows each commit touches exactly one file.

## Files Created/Modified

- `documentation/source/notebooks/h11_3_survey.ipynb` — **created**, symlink pointing to `../../../notebooks/h11_3_survey.ipynb` (mode 120000, commit `2811e56`).
- `documentation/source/index.rst` — **modified**, one-line insertion `   notebooks/h11_3_survey` into Examples toctree between `h11_2_walkthrough` and `h11_3_walkthrough` (commit `0b54288`).

## Decisions Made

- **Exercised the full `-W` smoke build in this plan, not just the file-level criteria.** Plan 01 had already merged (commits `1151617`, `d5f2028`, `3835180`, `d3ec413` in `git log`), so the "depends-on-Plan-01 smoke check" was live rather than deferred. Build passed green end-to-end.
- **Did not modify `notebooks/h11_3_survey.ipynb` itself.** The user has uncommitted edits to that file in the working tree; the plan only required linking to it, not re-executing or editing. myst-nb renders whatever outputs are currently stored in the `.ipynb` (D-17), so the user's in-progress edits flow through to docs the next time they commit.

## Deviations from Plan

None — plan executed exactly as written. Zero Rule 1/2/3 auto-fixes, zero Rule 4 architectural pauses, zero scope extensions.

## Issues Encountered

None. Both tasks passed their automated verifications on first try, and the `-W` smoke build exited clean on first run.

## Threat Flags

No new security-relevant surface introduced — the symlink target and toctree entry are inside the repo tree already covered by Phase 08's `<threat_model>` (T-08-04 symlink tampering accepted, T-08-05 notebook-output disclosure already registered as mitigate). Nothing new to flag.

## Known Stubs

None. No empty/placeholder data, no `TODO`/`FIXME`/"coming soon" strings introduced in this plan. The symlink points at a real 72,677-byte notebook with stored outputs.

## User Setup Required

None — no external service configuration needed for this plan. GitHub Pages "Settings → Pages" one-time toggle (per D-05) is still flagged for Plan 03's GitHub Actions workflow, not this plan.

## Next Phase Readiness

- **Docs source tree is now complete** for the deploy: all four notebook pages reachable from the toctree, mock imports in place, `_static/` present, `|W|` docstrings RST-safe.
- **`pip install -e .[docs]` + `sphinx-build -b html -W source build/html`** is a single, self-contained incantation that reproduces exit-code 0 locally. Plan 03's GitHub Actions workflow can copy this verbatim.
- **Ready to proceed to Plan 03** (GitHub Actions `docs.yml` → peaceiris/actions-gh-pages → `gh-pages` branch → https://sheride.github.io/cybir).

## Self-Check: PASSED

- `documentation/source/notebooks/h11_3_survey.ipynb` exists and is a symlink (mode 120000) — verified via `git ls-files --stage` and `test -L`.
- `readlink` returns exactly `../../../notebooks/h11_3_survey.ipynb` — verified.
- Resolved target size (72,677 bytes) matches real `notebooks/h11_3_survey.ipynb` — verified via `stat -L -f%z` vs `stat -f%z`.
- `documentation/source/index.rst` Examples toctree contains exactly four entries in the required order — verified via Python regex check.
- Commits `2811e56` and `0b54288` both present in `git log --oneline -5` — verified.
- `sphinx-build -b html -W source build/html` exit code `0` captured in `/tmp/sphinx_08_02.log` — verified.
- `documentation/build/html/notebooks/h11_3_survey.html` exists and is 62,995 bytes (non-empty) — verified.
- No unrelated user changes swept into either task commit — verified via per-commit `git show --stat`.

---
*Phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s*
*Completed: 2026-04-23*

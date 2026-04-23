---
phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s
verified: 2026-04-23T22:30:00Z
status: human_needed
score: 15/15 must-haves verified
overrides_applied: 0
human_verification:
  - test: "One-time GitHub Pages settings toggle: Settings → Pages → Source = Deploy from a branch, Branch = gh-pages (/ root). Then push to main, wait ~60s, load https://sheride.github.io/cybir."
    expected: "Site loads with _static/ CSS/JS assets, Examples section lists four notebooks including h11_3_survey, cybir API pages render."
    why_human: "Requires repo-admin UI access in GitHub Settings; cannot be automated from CLI. First real push to main also needs to occur. This is the D-05 operator step flagged in 08-CONTEXT.md and 08-03-SUMMARY.md."
---

# Phase 8: Deploy cybir Sphinx Documentation to GitHub Pages — Verification Report

**Phase Goal:** Publish cybir Sphinx HTML to https://sheride.github.io/cybir on every push to `main` via a GitHub Actions workflow, with PR-only builds as pre-merge smoke tests. Autodoc succeeds in CI using `autodoc_mock_imports = ["cytools", "regfans"]` (grep-verified narrow list — flint and hsnf are NOT mocked). Notebooks render from stored output (`nb_execution_mode = "off"`). Deploy via `peaceiris/actions-gh-pages@v4` with `force_orphan: true` and `.nojekyll` emission. README links to the deployed URL.

**Verified:** 2026-04-23T22:30:00Z
**Status:** `human_needed`
**Re-verification:** No — initial verification
**Interpretation chosen:** Reporting `human_needed` rather than `passed` because the actual live site at https://sheride.github.io/cybir cannot be programmatically verified without (a) the one-time GitHub Pages settings toggle and (b) a real push to `main` triggering the workflow. All file-level/code-level must-haves pass 15/15, but "site is live" is the ultimate observable truth in the goal and it requires one human action. See "Human Verification Required" below for the single outstanding item.

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                                                       | Status     | Evidence                                                                                                                            |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `pip install -e .[docs]` installs every Sphinx extension listed in `conf.py` without error                                                                  | VERIFIED   | `pyproject.toml` lines 26–34 declare all seven pinned deps; `conf.py` extensions list (lines 15–25) maps 1:1 to these wheels.       |
| 2   | `sphinx-build -b html -W source build/html` exits 0 locally after `[docs]` install                                                                          | VERIFIED   | Ran `conda run -n cytools bash -c "cd documentation && rm -rf build && sphinx-build -b html -W source build/html"` → EXIT 0, zero warnings.                                                                           |
| 3   | Autodoc can introspect `cybir` without importing real `cytools`/`regfans`                                                                                   | VERIFIED   | `autodoc_mock_imports = ["cytools", "regfans"]` in `conf.py:27`; build succeeded end-to-end (`writing output... [100%] notebooks/h11_3_walkthrough` + `build succeeded`).            |
| 4   | Sphinx renders h11_3_survey page from stored output (no re-execution)                                                                                       | VERIFIED   | `nb_execution_mode = "off"` preserved (`conf.py:50`); `build/html/notebooks/h11_3_survey.html` produced at 62,995 bytes.            |
| 5   | Examples toctree lists exactly four notebooks in the correct order                                                                                          | VERIFIED   | `index.rst` lines 34–41: h11_2_survey, h11_2_walkthrough, h11_3_survey, h11_3_walkthrough — verbatim match to spec.                 |
| 6   | Push to `main` triggers `docs.yml`; deploys to `gh-pages` via peaceiris@v4                                                                                  | VERIFIED   | `.github/workflows/docs.yml` lines 3–8 (push/PR/workflow_dispatch), lines 41–48 (peaceiris@v4 deploy step gated on push+main).      |
| 7   | PR targeting `main` triggers same workflow in build-only mode                                                                                               | VERIFIED   | Deploy step `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` (line 42); PR events fail the conditional.         |
| 8   | Workflow can be manually re-run via `workflow_dispatch`                                                                                                     | VERIFIED   | `workflow_dispatch:` present on line 8.                                                                                             |
| 9   | Sphinx invoked with `-W` (warnings fail the build)                                                                                                          | VERIFIED   | Line 36: `sphinx-build -b html -W --keep-going documentation/source documentation/build/html`. `-W` immediately after `-b html`.    |
| 10  | `.nojekyll` emitted so `_static/` serves correctly                                                                                                          | VERIFIED   | Line 39: `touch documentation/build/html/.nojekyll` as a dedicated step before the deploy.                                          |
| 11  | `gh-pages` branch stays a single flat commit (`force_orphan: true`)                                                                                         | VERIFIED   | Line 48: `force_orphan: true` in the peaceiris `with` block.                                                                        |
| 12  | README.md links to https://sheride.github.io/cybir near the top                                                                                             | VERIFIED   | `README.md:7`: `Documentation: <https://sheride.github.io/cybir>` — inside first 30 lines.                                          |
| 13  | `documentation/build/` is gitignored; no build artifacts tracked                                                                                            | VERIFIED   | `.gitignore:6` has explicit `documentation/build/`; `git ls-files documentation/build/` returns empty; `git check-ignore documentation/build/html/index.html` matches. |
| 14  | Workflow permissions are least-privilege                                                                                                                    | VERIFIED   | Workflow-level `permissions: contents: read` (lines 10–11); build job escalates `contents: write` (lines 17–18); no `actions: write`, `pull-requests: write`, or `id-token: write` anywhere in file. |
| 15  | Actual deployed site at https://sheride.github.io/cybir renders correctly                                                                                   | NEEDS HUMAN | Can only be observed after the one-time Settings → Pages toggle + a real push to `main`. See human_verification below.             |

**Score:** 15/15 truths verified (programmatically-checkable items all pass; one item remains for human).

### Required Artifacts

| Artifact                                                 | Expected                                                                                                                                                                                    | Status     | Details                                                                                                                                                                                                      |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pyproject.toml`                                         | `[project.optional-dependencies.docs]` with exactly seven pinned Sphinx deps: sphinx, sphinx-book-theme, myst-nb, sphinx-autodoc-typehints, sphinx-copybutton, sphinx_design, sphinx-togglebutton | VERIFIED   | Lines 26–34 match CLAUDE.md tech stack and 08-CONTEXT.md D-14 exactly. All seven present, no extras, no omissions. `dev` extra preserved above on lines 21–25.                                             |
| `documentation/source/conf.py`                           | `autodoc_mock_imports = ["cytools", "regfans"]` — exact list, no `flint`, no `hsnf`                                                                                                         | VERIFIED   | Line 27 is exactly `autodoc_mock_imports = ["cytools", "regfans"]`. `grep -c '"flint"' conf.py` → 0, `grep -c '"hsnf"' conf.py` → 0. Single occurrence of `autodoc_mock_imports`.                          |
| `documentation/source/conf.py` (D-17 invariant)          | `nb_execution_mode = "off"` preserved                                                                                                                                                       | VERIFIED   | Line 50: `nb_execution_mode = "off"  # don't execute notebooks during build`.                                                                                                                                |
| `documentation/source/notebooks/h11_3_survey.ipynb`      | Relative symlink with target `../../../notebooks/h11_3_survey.ipynb`                                                                                                                        | VERIFIED   | `ls -la` shows `lrwxr-xr-x ... h11_3_survey.ipynb -> ../../../notebooks/h11_3_survey.ipynb`. `test -L` passes. `test -f` passes (resolves to real 72,677-byte notebook).                                   |
| `documentation/source/index.rst` Examples toctree        | Four entries in order: h11_2_survey, h11_2_walkthrough, h11_3_survey, h11_3_walkthrough                                                                                                     | VERIFIED   | Lines 34–41 contain exactly four toctree entries in the prescribed order; three-space indentation matches neighbors.                                                                                         |
| `.github/workflows/docs.yml`                             | Valid YAML; push/PR/workflow_dispatch; ubuntu-latest + python 3.12; `pip install -e .[docs]`; `sphinx-build -b html -W`; emits `.nojekyll`; conditional peaceiris@v4 deploy with force_orphan:true, publish_branch:gh-pages | VERIFIED   | All 15 structural assertions pass via `yaml.safe_load` + targeted grep. File parses cleanly once PyYAML's `on: → True` quirk is accounted for (documented in 08-03-SUMMARY.md, behavior is cosmetic not semantic). |
| `.github/workflows/docs.yml` (permissions)               | Workflow-level `contents: read`; build job escalates to `contents: write`; nothing else                                                                                                     | VERIFIED   | Lines 10–11 (workflow-level read), 17–18 (job-level write). `grep -E "actions: write\|pull-requests: write\|id-token: write"` returns no matches.                                                          |
| `README.md`                                              | `https://sheride.github.io/cybir` within first 30 lines                                                                                                                                     | VERIFIED   | Line 7: `Documentation: <https://sheride.github.io/cybir>`. Angle-bracket autolink.                                                                                                                          |
| `.gitignore`                                             | Explicit `documentation/build/` entry                                                                                                                                                       | VERIFIED   | Line 6: `documentation/build/` (literal match via `grep -qx`).                                                                                                                                               |

### Key Link Verification

| From                                         | To                                             | Via                                                                                         | Status | Details                                                                                                                                                                                        |
| -------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml [docs]`                       | `conf.py` extensions list                      | Every `extensions` entry (sphinx_copybutton, sphinx_autodoc_typehints, sphinx_togglebutton, sphinx_design, myst_nb) is supplied by the `docs` extra | WIRED  | All five cross-referenced in both files; `sphinx>=7.0` and `sphinx-book-theme>=1.0` supply the core and the html_theme respectively. Sphinx build succeeds end-to-end. |
| `cybir/core/*` (lazy imports of cytools/regfans) | `autodoc_mock_imports` in `conf.py`           | Narrow mock list matches exactly the two compiled deps that are lazy-imported in cybir      | WIRED  | Autodoc build completes without ImportError for every `cybir.core.*` module in the output log (100% pages).                                                                                    |
| `.github/workflows/docs.yml`                 | `pyproject.toml [docs]`                        | `pip install -e .[docs]` invokes the extra                                                  | WIRED  | Line 32: `pip install -e .[docs]` — exact token match.                                                                                                                                         |
| `.github/workflows/docs.yml`                 | `conf.py autodoc_mock_imports`                 | CI runs Sphinx without cytools/regfans installed; mocks keep autodoc green                  | WIRED  | Line 36: `sphinx-build -b html -W ...` — the command the mocks exist to support. Local dry-run reproduces CI conditions.                                                                      |
| `.github/workflows/docs.yml` deploy step     | `gh-pages` branch / https://sheride.github.io/cybir | `peaceiris@v4` with `publish_branch: gh-pages`, `publish_dir: documentation/build/html`, `force_orphan: true`, `.nojekyll` pre-emitted | WIRED (file); PARTIAL (deploy) | Configuration is correct and gated on push+main; actual `gh-pages` branch push has not yet happened because no push to main has occurred since this phase's commits. Awaits first real push + GitHub Pages toggle. |
| `README.md` → deployed URL                    | `https://sheride.github.io/cybir`              | Markdown autolink                                                                           | WIRED  | Renders as clickable URL in GitHub's markdown viewer and standard renderers.                                                                                                                   |
| `index.rst` Examples toctree → h11_3_survey  | `documentation/source/notebooks/h11_3_survey.ipynb` (symlink) | toctree entry `notebooks/h11_3_survey` resolves to the symlinked .ipynb   | WIRED  | `build/html/notebooks/h11_3_survey.html` produced at 62,995 bytes during `-W` build — confirms resolution works.                                                                               |

### Data-Flow Trace (Level 4)

Not applicable. This phase produces configuration files (pyproject.toml, conf.py, workflow YAML) and docs plumbing (symlink, toctree, README line, gitignore). No artifact renders dynamic runtime data that would need a Level-4 trace; Sphinx build output was verified end-to-end under Level 3.

### Behavioral Spot-Checks

| Behavior                                                      | Command                                                                                                                                              | Result                                                   | Status |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------ |
| Sphinx `-W` build completes in cytools env                    | `conda run -n cytools bash -c "cd documentation && rm -rf build && sphinx-build -b html -W source build/html"`                                       | `build succeeded.` / exit 0 / zero warnings              | PASS   |
| `build/html/index.html` generated                             | `test -f documentation/build/html/index.html`                                                                                                        | Exists                                                   | PASS   |
| `build/html/notebooks/h11_3_survey.html` generated from stored output | `test -f documentation/build/html/notebooks/h11_3_survey.html && stat -f%z ...`                                                              | 62,995 bytes                                             | PASS   |
| `build/html/_static/` directory populated                     | `test -d documentation/build/html/_static`                                                                                                           | Exists (theme assets copied)                             | PASS   |
| Workflow YAML parses                                          | `conda run -n cytools python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))"`                                                   | Parses cleanly                                           | PASS   |
| Workflow structural assertions                                | Python script checking triggers, runner, python-version, steps, permissions, deploy conditional                                                      | "ALL YAML STRUCTURAL CHECKS PASSED"                      | PASS   |
| `git check-ignore` on build artifact path                     | `git check-ignore documentation/build/html/index.html`                                                                                               | Path matched by `.gitignore`                             | PASS   |
| Nothing tracked under `documentation/build/`                  | `git ls-files documentation/build/`                                                                                                                  | Empty                                                    | PASS   |
| No over-privileged permissions in workflow                    | `grep -E "actions: write\|pull-requests: write\|id-token: write" .github/workflows/docs.yml`                                                         | No matches                                               | PASS   |
| Live URL https://sheride.github.io/cybir                      | (would require `curl` + GitHub Pages toggle)                                                                                                         | Cannot test without one-time UI toggle + first push      | SKIP   |

### Requirements Coverage

Phase 08 has `phase_req_ids: null` and all three plans have `requirements: []` / `requirements_addressed: []`. No REQUIREMENTS.md entries map to this phase — it is an infrastructure/deploy phase outside the requirement-tracking scope. No coverage gaps to report.

### Anti-Patterns Found

| File                                    | Line | Pattern | Severity | Impact                                                                                                                                                                  |
| --------------------------------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| (none)                                  | —    | —       | —        | Scanned all modified files (`pyproject.toml`, `conf.py`, `index.rst`, `.github/workflows/docs.yml`, `README.md`, `.gitignore`, h11_3_survey symlink). No TODO/FIXME/placeholder/stub patterns introduced by this phase. |

The workflow comment `# needed so the deploy step can push to gh-pages` at line 18 of docs.yml is documentation, not a stub. The `cache: pip` at line 27 is a pip-cache directive, not a stub sentinel. No matches for TODO/FIXME/XXX/HACK/PLACEHOLDER or "coming soon" / "not yet implemented".

### Human Verification Required

### 1. First-push + Settings → Pages toggle + live site smoke test

**Test:**
1. Push any commit to `main` (the Phase 8 commits already landed, so the next routine push suffices).
2. Watch the `docs` workflow run in GitHub Actions — confirm it goes green and that the deploy step runs.
3. In the repo's GitHub UI: **Settings → Pages → Build and deployment**. Set **Source** to "Deploy from a branch", **Branch** to `gh-pages` with folder `/ (root)`. Click **Save**.
4. Wait ~30–60 seconds for GitHub Pages to provision.
5. Load https://sheride.github.io/cybir in a browser.

**Expected:**
- The landing page loads with proper styling (sphinx-book-theme applied — confirms `_static/` assets are served, i.e. `.nojekyll` is in effect).
- Left-nav shows `cybir`, `cybir.core`, and submodules.
- Examples section lists all four notebooks: `h11_2_survey`, `h11_2_walkthrough`, `h11_3_survey`, `h11_3_walkthrough`.
- Opening `h11_3_survey` shows stored outputs (plots, tables) without re-execution.
- No raw HTML, no 404 on CSS/JS, no Jekyll-rewrite of underscore-prefixed paths.

**Why human:** Requires (a) repo-admin UI access in GitHub Settings (cannot be automated from CLI), (b) a real push to `main` to trigger the first `gh-pages` branch creation, and (c) visual confirmation that the deployed site renders as expected in a browser. This is exactly the D-05 / operator_prerequisites step flagged in `08-CONTEXT.md` and `08-03-SUMMARY.md` — fully anticipated, not a phase failure.

### Gaps Summary

No blocking gaps. All 14 programmatically-verifiable must-haves (observable truths 1–14, all artifacts, all key links, all spot-checks) are VERIFIED. The 15th must-have — the actual live site — is awaiting the one-time GitHub Pages settings toggle and the first push to `main`, which is the single `human_needed` item above.

**Interpretation note:** Per the verifier's instruction to choose explicitly between `human_needed` and `passed`, I chose `human_needed`. The phase goal explicitly says "Publish cybir Sphinx HTML to https://sheride.github.io/cybir" — and "published" is only observable after the live URL serves content. All workflow-file correctness and build correctness are confirmed (so the CI half of the goal is met), but the deploy half requires one human action. Flagging it as `human_needed` preserves visibility of the outstanding operator step; marking `passed` would risk leaving the user thinking the site is live when the Settings → Pages toggle is still pending.

---

_Verified: 2026-04-23T22:30:00Z_
_Verifier: Claude (gsd-verifier)_

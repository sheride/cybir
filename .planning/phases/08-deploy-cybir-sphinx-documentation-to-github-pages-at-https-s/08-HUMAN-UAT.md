---
status: partial
phase: 08-deploy-cybir-sphinx-documentation-to-github-pages-at-https-s
source: [08-VERIFICATION.md]
started: 2026-04-23T23:00:00Z
updated: 2026-04-23T23:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. First-push + Settings → Pages toggle + live site smoke test

**Test steps:**
1. Push any commit to `main` (the Phase 8 commits already landed, so the next routine push suffices).
2. Watch the `docs` workflow run in GitHub Actions — confirm it goes green and that the deploy step runs.
3. In the repo's GitHub UI: **Settings → Pages → Build and deployment**. Set **Source** to "Deploy from a branch", **Branch** to `gh-pages` with folder `/ (root)`. Click **Save**.
4. Wait ~30–60 seconds for GitHub Pages to provision.
5. Load https://sheride.github.io/cybir in a browser.

**expected:**
- Landing page loads with proper styling (sphinx-book-theme applied — confirms `_static/` assets are served, i.e. `.nojekyll` is in effect).
- Examples section in the sidebar lists four notebooks including `h11_3_survey`, and opening `h11_3_survey` shows the rendered notebook with stored outputs.
- `cybir` API pages (Core, etc.) render — confirms `autodoc_mock_imports` keeps autodoc green without the compiled cytools/regfans stack on the runner.

**result:** [pending]

**why_human:** Requires repo-admin UI access in GitHub Settings; cannot be automated from CLI. First real push to `main` also needs to occur. This is the D-05 operator step flagged in 08-CONTEXT.md and 08-03-SUMMARY.md.

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

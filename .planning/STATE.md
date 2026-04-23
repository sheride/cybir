---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
stopped_at: Completed 08-03-PLAN.md
last_updated: "2026-04-23T21:52:13.176Z"
last_activity: 2026-04-23
progress:
  total_phases: 8
  completed_phases: 8
  total_plans: 28
  completed_plans: 28
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-11)

**Core value:** A clean, well-documented, modular implementation of GV-based EKC construction that is easy to use, extend, and understand
**Current focus:** Phase 08 — deploy-cybir-sphinx-documentation-to-github-pages-at-https-s

## Current Position

Phase: 08 (deploy-cybir-sphinx-documentation-to-github-pages-at-https-s) — EXECUTING
Plan: 3 of 3
Status: Phase complete — ready for verification
Last activity: 2026-04-23

Progress: [█████████░] 96%

## Performance Metrics

**Velocity:**

- Total plans completed: 21
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 2 | - | - |
| 02 | 4 | - | - |
| 04 | 4 | - | - |
| 05 | 3 | - | - |
| 06 | 6 | - | - |
| 07 | 2 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 191 | 2 tasks | 9 files |
| Phase 01 P02 | 259 | 2 tasks | 6 files |
| Phase 02 P01 | 321 | 2 tasks | 4 files |
| Phase 02 P02 | 5min | 2 tasks | 4 files |
| Phase 02 P03 | 17min | 2 tasks | 2 files |
| Phase 02 P04 | 6min | 2 tasks | 6 files |
| Phase 03 P01 | 4min | 2 tasks | 5 files |
| Phase 03 P02 | 6min | 2 tasks | 3 files |
| Phase 03 P03 | 3min | 2 tasks | 4 files |
| Phase 03 P04 | 2min | 2 tasks | 17 files |
| Phase 04 P01 | 6min | 1 tasks | 5 files |
| Phase 04 P02 | 7min | 2 tasks | 3 files |
| Phase 04 P03 | 6min | 2 tasks | 8 files |
| Phase 04-coxeter-weyl P04 | 6min | 2 tasks | 5 files |
| Phase 05 P01 | 3min | 2 tasks | 5 files |
| Phase 05 P02 | 4min | 2 tasks | 5 files |
| Phase 06 P01 | 15min | 2 tasks | 6 files |
| Phase 06 P03 | 8min | 2 tasks | 2 files |
| Phase 06 P04 | 8min | 2 tasks | 4 files |
| Phase 06 P05 | 4min | 2 tasks | 4 files |
| Phase 07 P01 | 3min | 2 tasks | 8 files |
| Phase 07 P02 | 2min | 2 tasks | 8 files |
| Phase 08 P01 | 20min | 2 tasks | 5 files |
| Phase 08 P02 | 5min | 2 tasks | 2 files |
| Phase 08 P03 | 15min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Foundation-first approach -- data types and test infrastructure before porting math (prior refactors failed without this)
- [Roadmap]: 3-phase coarse structure: Foundation -> Core Math -> Pipeline & Integration
- [Phase 01]: Used __setattr__ + _frozen flag for immutability (not frozen dataclass) to support numpy arrays
- [Phase 01]: PhaseGraph uses string labels as node keys; ExtremalContraction start/end store labels not objects
- [Phase 02]: projected_int_nums uses explicit einsum subscripts per n_projected value to avoid index collision
- [Phase 02]: gv.py compute_gv_eff implemented as stub during Task 1 for flop.py import, then fully implemented in Task 2
- [Phase 02]: Sign convention for zero-vol divisor uses kappa_{ijk} D_i D_j C_k (volume-based) instead of D.C (always zero for projection-lifted divisors)
- [Phase 02]: Numpy 2.x einsum requires unique subscript letters across operands (ax,by,xyz not ia,jb,ijk)
- [Phase 02]: Lazy import in CalabiYauLite.flop() to prevent circular imports between types.py and flop.py
- [Phase 02]: No classify convenience method on ExtremalContraction -- inputs spread across objects, standalone function is clearer
- [Phase 03]: Graph owns topology: add_contraction takes (contraction, phase_a_label, phase_b_label) with curve signs on edge
- [Phase 03]: CYBirationalClass uses lazy imports for build_gv/weyl to avoid circular dependencies
- [Phase 03]: Used toric_kahler_cone() and mori_cone_cap(in_basis=True) as CYTools cone API
- [Phase 03]: Terminal walls and symmetric flops stored as self-loop edges in graph
- [Phase 03]: Mori cone deduplication uses frozenset of integer-cast ray tuples for order-invariant comparison
- [Phase 03]: Reflected phases get SYMMETRIC_FLOP contraction edges; terminal walls inherited as self-loops
- [Phase 03]: Mirrored dbrane-tools conf.py exactly for consistent documentation pattern
- [Phase 04]: Positive definiteness tolerance 1e-10 (strict) to catch affine/semi-definite Coxeter groups
- [Phase 04]: B_2 fixtures derived from Cartan matrix; coxeter_matrix kept as deprecated alias for coxeter_element
- [Phase 04]: Reflected contraction curves use g @ curve (Mori space), Kahler rays use ray @ inv(g)
- [Phase 04]: No deduplication of reflected phases -- each (g, fund_phase) pair is unique (D-11)
- [Phase 04]: _sym_flop_curves stored during BFS for chamber walk; to_fundamental_domain returns (point, g); weyl.py deleted
- [Phase 04-coxeter-weyl]: Root phase curve_signs keys used as canonical curve set for reflected phases
- [Phase 04-coxeter-weyl]: Kept _sym_flop_refs set for O(1) dedup alongside _sym_flop_pairs authoritative list
- [Phase 05]: CalabiYauLite repr threshold at h11<=3 (detailed) vs h11>3 (short)
- [Phase 05]: validate_stability does full BFS restart for clean comparison
- [Phase 05]: SU2_NONGENERIC_CS treated as terminal wall; adds coxeter refs and eff cone gens but NOT sym_flop_refs/pairs
- [Phase 05]: compare_orbit.py skips polytopes without symmetric flops (nothing to validate)
- [Phase 06]: is_symmetric_flop returns (bool, bool) tuple for backward-compatible gross flop detection
- [Phase 06]: GrossFlop post-check in _run_bfs (not inside classify_contraction) for minimal disruption
- [Phase 06]: GROSS_FLOP excluded from _coxeter_refs and _sym_flop_refs/pairs
- [Phase 06]: classify_phase_type returns non_inherited when regfans raises for non-triangulations (graceful fallback)
- [Phase 06]: toric_origin matching uses curve tuple lookup in gv_dict (heuristic, accepts T-06-08)
- [Phase 06]: Mori bounds use Cone.contains() with warnings on failure, not hard errors (per T-06-14)
- [Phase 06]: _verify_mori_bounds cross-checks toric GVs against root_invariants.gv_series_cybir
- [Phase 06]: hyperextended_kahler_cone delegates to extended_kahler_cone for API clarity
- [Phase 06]: diagnose_curve is standalone function (not method) since it needs cy, curve, and optionally ekc
- [Phase 07]: Pickle for transient GV cache (pragmatic exception); Coxeter type/order from cybir; subprocess per polytope for multiprocessing safety
- [Phase 07]: Content-based phase matching (int_nums + c2) for ground truth comparison; Coxeter refs excluded; type mapping for SU2_NONGENERIC_CS and GROSS_FLOP
- [Phase 08]: autodoc_mock_imports scoped narrowly to [cytools, regfans] — flint not imported by cybir, hsnf is pure-Python pip-installable
- [Phase 08]: docs build deps live in [project.optional-dependencies.docs] extra (single source of truth for local + CI)
- [Phase 08]: Prose |W| in docstrings must be wrapped as :math:`|W|` — RST reads |...| as substitution reference and Sphinx -W fails otherwise
- [Phase 08]: Notebook-to-docs recipe: ln -s ../../../notebooks/<name>.ipynb into documentation/source/notebooks/ + toctree entry in index.rst; git tracks mode 120000 symlink (not copy); myst-nb renders from stored outputs
- [Phase 08]: CI deploy pattern: checkout → setup-python → pip install -e .[docs] → sphinx-build -W --keep-going → .nojekyll → peaceiris/actions-gh-pages@v4 with force_orphan, gated on push+refs/heads/main
- [Phase 08]: Least-privilege token scope: workflow-level contents: read, build-job escalates to contents: write for the deploy step only; no actions/pull-requests/id-token writes
- [Phase 08]: Actions pinned to major tags (@v4/@v5) not full SHAs — T-08-08 accept disposition (floats on upstream security patches)

### Roadmap Evolution

- Phase 4 added: Coxeter Group & Weyl Expansion — proper group construction, streaming BFS, full orbit expansion with correct index conventions
- Phase 6 added: Classification Correctness, Toric Curves & Cone Construction
- Phase 8 added: Deploy cybir Sphinx documentation to GitHub Pages at https://sheride.github.io/cybir with autodoc_mock_imports + GitHub Actions

### Pending Todos

None yet.

### Blockers/Concerns

- ENH-02 (tuned complex structure mode) deferred to v2 -- user wants to discuss during implementation, not now

## Session Continuity

Last session: 2026-04-23T21:52:04.321Z
Stopped at: Completed 08-03-PLAN.md
Resume file: None

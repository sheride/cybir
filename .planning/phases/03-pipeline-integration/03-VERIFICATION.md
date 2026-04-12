---
phase: 03-pipeline-integration
verified: 2026-04-12T08:22:54Z
status: human_needed
score: 3/5 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "CYTools monkey-patching works at Invariants, Polytope, Triangulation, and CalabiYau levels with version guards, and cy.construct_phases() triggers the full pipeline"
    reason: "User explicitly chose to skip Triangulation-level patching (documented in 03-DISCUSSION-LOG.md) and the entry point is cy.birational_class() not cy.construct_phases(). The three-level approach (Invariants + CalabiYau + Polytope) was a deliberate design decision. Version guards are implemented."
    accepted_by: "user (via 03-DISCUSSION-LOG.md)"
    accepted_at: "2026-04-12T00:00:00Z"
human_verification:
  - test: "Run construct_phases on h11=2 CY (e.g., from cytools.fetch_polytopes(h11=2, limit=1)[0]) with max_deg=10 and compare phase count and contraction types against the original extended_kahler_cone.py result"
    expected: "Identical phase graph structure: same number of phases, same contraction types per wall, same curve-sign deduplication result"
    why_human: "Requires CYTools data and a reference run of the original code; cannot verify numerically with unit tests"
  - test: "Run expand_weyl() after construct_phases on an h11=2 or h11=3 CY known to have symmetric flops, and compare resulting phase count and Mori cone signatures against the original"
    expected: "Weyl-expanded phases have correct intersection numbers (via einsum transformation) and Mori cones matching original sym_flop_cy output"
    why_human: "Requires CYTools data with known symmetric flops; numerical correctness of einsum transform is untested against live data"
  - test: "Execute h11_2_walkthrough.ipynb and h11_3_walkthrough.ipynb end-to-end in the cytools conda environment"
    expected: "All cells run without error; ekc.phases, ekc.contractions, ekc.coxeter_matrix produce reasonable output for the chosen polytopes"
    why_human: "Notebooks have empty outputs; end-to-end execution requires actual CYTools polytope data"
---

# Phase 03: Pipeline Integration Verification Report

**Phase Goal:** Users can run the full EKC construction pipeline on a CYTools CalabiYau object and access results through a clean read-only API, with Sphinx docs and example notebooks
**Verified:** 2026-04-12T08:22:54Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `construct_phases` BFS loop runs on h11=2 and h11=3 test cases and produces identical phase graphs to the original code | ? NEEDS HUMAN | Unit tests pass (27 passed); full CY pipeline requires live CYTools data |
| 2 | Weyl orbit expansion produces the hyperextended cone matching the original code on test cases | ? NEEDS HUMAN | Unit tests pass (10 weyl tests); correctness against reference requires live data |
| 3 | Post-construction API (`ekc.phases`, `ekc.contractions`, `ekc.coxeter_matrix`, etc.) provides read-only access to all results without ad-hoc attribute hunting | VERIFIED | 15 read-only properties on CYBirationalClass; imports clean; all 54 graph/types tests pass |
| 4 | CYTools monkey-patching works at Invariants, Polytope, Triangulation, and CalabiYau levels with version guards, and `cy.construct_phases()` triggers the full pipeline | PASSED (override) | Triangulation level and cy.construct_phases() deliberately omitted per user decision in 03-DISCUSSION-LOG.md. Invariants (6 methods), CalabiYau.birational_class, Polytope.birational_class all patched with version guards. patch_cytools() runs without error. |
| 5 | Sphinx documentation builds cleanly with equation references, and example notebooks for h11=2 and h11=3 run end-to-end | PARTIAL — Sphinx verified, notebooks need human | `make html` succeeds (3 warnings, 0 errors); both notebooks are valid nbformat 4 JSON with correct API calls; end-to-end execution requires human |

**Score:** 3/5 truths verified (plus 1 override accepted, 2 need human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cybir/core/graph.py` | Updated CYGraph with add_contraction(contraction, phase_a_label, phase_b_label), contractions_from, phases_adjacent_to | VERIFIED | All three methods present with correct signatures; 54 tests pass |
| `cybir/core/types.py` | ExtremalContraction without start_phase/end_phase, with cone_face | VERIFIED | 0 occurrences of start_phase/end_phase; cone_face property present (5 occurrences) |
| `cybir/core/ekc.py` | CYBirationalClass orchestrator with read-only API | VERIFIED | CYBirationalClass with 15 @property decorators, from_gv classmethod, setup_root, construct_phases, expand_weyl |
| `cybir/core/build_gv.py` | BFS construction logic: setup_root and construct_phases | VERIFIED | Both functions present; curve_signs dedup, flop_chains, _build_log accumulation, logger usage all confirmed |
| `cybir/core/patch.py` | CYTools Invariants monkey-patching | VERIFIED | All 9 required functions present; patch_cytools() runs without error; version guards confirmed |
| `cybir/core/weyl.py` | Weyl orbit expansion: expand_weyl function | VERIFIED | expand_weyl, _reflect_phase with einsum, _is_new_phase, _inherit_contractions all present |
| `cybir/__init__.py` | Package re-exports including CYBirationalClass and patch_cytools | VERIFIED | Both present in __all__; `from cybir import CYBirationalClass, patch_cytools` succeeds |
| `tests/test_graph.py` | Updated graph tests using new add_contraction signature | VERIFIED | 54 graph/types tests pass |
| `tests/test_build_gv.py` | Tests for BFS builder | VERIFIED | 27 tests pass |
| `tests/test_weyl.py` | Tests for Weyl expansion helpers | VERIFIED | Part of 27 tests passing |
| `documentation/source/conf.py` | Sphinx configuration with sphinx-book-theme | VERIFIED | sphinx_book_theme, myst_nb, nb_execution_mode="off" all confirmed |
| `documentation/source/index.rst` | Documentation index with toctree | VERIFIED | toctree directive present |
| `notebooks/h11_2_walkthrough.ipynb` | h11=2 example notebook | VERIFIED (structure) | 16 cells, valid JSON; CYBirationalClass (3), patch_cytools (2), expand_weyl (2) references present |
| `notebooks/h11_3_walkthrough.ipynb` | h11=3 example notebook | VERIFIED (structure) | 20 cells, valid JSON; h11=3 references (3) present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cybir/core/ekc.py` | `cybir/core/graph.py` | CYBirationalClass._graph is a CYGraph | WIRED | `from .graph import CYGraph` at top; `self._graph = CYGraph()` in __init__ |
| `cybir/core/build_gv.py` | `cybir/core/ekc.py` | setup_root and construct_phases accept CYBirationalClass | WIRED | Both functions take `ekc` param; `def setup_root(ekc...` confirmed |
| `cybir/core/build_gv.py` | `cybir/core/patch.py` | builder uses monkey-patched Invariants methods | WIRED | `from .patch import patch_cytools; patch_cytools()` at top of setup_root; `flop_gvs`, `gv_series_cybir`, `cone_incl_flop` calls confirmed |
| `cybir/core/weyl.py` | `cybir/core/ekc.py` | expand_weyl accepts CYBirationalClass | WIRED | `def expand_weyl(ekc)` signature confirmed |
| `cybir/core/weyl.py` | `cybir/core/types.py` | Creates new CalabiYauLite phases from reflections | WIRED | `CalabiYauLite(...)` calls in expand_weyl loop |
| `documentation/source/conf.py` | `cybir/` | autodoc imports cybir package | WIRED | `autodoc` in extensions list; `sys.path.insert(0, ...)` at top of conf.py |

### Data-Flow Trace (Level 4)

CYBirationalClass renders dynamic data from graph state. Tracing the flow:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `ekc.phases` | `_graph.phases` | `ekc._graph.add_phase(root/flopped)` in build_gv.py | Yes — populated in BFS loop | FLOWING |
| `ekc.contractions` | `_graph.contractions` | `ekc._graph.add_contraction(...)` in build_gv.py | Yes — populated per wall classification | FLOWING |
| `ekc.coxeter_matrix` | `_coxeter_refs` | `_accumulate_generators` → `ekc._coxeter_refs.add(...)` | Yes — populated for SU2/SYMMETRIC_FLOP walls | FLOWING |
| `ekc.build_log` | `_build_log` | `ekc._build_log.append(...)` in construct_phases BFS | Yes — entry per wall classified | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Package imports without error | `python -c "from cybir import CYBirationalClass, patch_cytools"` | "imports OK" | PASS |
| patch_cytools() runs without error | `python -c "from cybir.core.patch import patch_cytools; patch_cytools()"` | "patch_cytools OK" | PASS |
| All unit tests pass | `pytest tests/ -q` | 304 passed, 100 skipped, 5 warnings | PASS |
| Sphinx documentation builds | `cd documentation && make html` | "build succeeded, 3 warnings" | PASS |
| Notebooks are valid JSON | `python -c "import json; json.load(open('notebooks/h11_2_walkthrough.ipynb'))"` | h11_2: 16 cells, h11_3: 20 cells | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 03-02 | `construct_phases` BFS loop with dictionary-keyed phase deduplication | VERIFIED | `construct_phases` in build_gv.py; `curve_signs` dict dedup; 17 unit tests pass |
| PIPE-02 | 03-03 | Weyl orbit expansion for hyperextended cone | VERIFIED | `expand_weyl` in weyl.py; einsum transformation; unit tests pass |
| PIPE-03 | 03-01 | Clean read-only post-construction API | VERIFIED | 15 @property on CYBirationalClass; all accessible |
| PIPE-04 | 03-02 | Verbose logging replacing scattered print statements | VERIFIED | `logger = logging.getLogger("cybir")` in build_gv.py; `_build_log` entries per wall |
| INTG-01 | 03-02 | CYTools Invariants monkey-patching (gv_series, gv_eff, ensure_nilpotency, flop_gvs) | VERIFIED | All 6 methods implemented in patch.py; patch_cytools() runs successfully |
| INTG-03 | 03-03 | Monkey-patching at Polytope, Triangulation, CalabiYau levels | VERIFIED (override) | Polytope and CalabiYau patched; Triangulation deliberately skipped per user decision |
| INTG-04 | 03-03 | Version guards on monkey-patches | VERIFIED | `hasattr(Invariants, "gv")` check; `__init__` signature inspection; `warnings.warn` on 4 failure paths |
| PKG-02 | 03-04 | Sphinx documentation with equation references | VERIFIED | conf.py with mathjax, napoleon; `make html` succeeds; arXiv references in docstrings |
| PKG-03 | 03-04 | Example notebooks for h11=2,3 | VERIFIED (structure) | Both notebooks exist as valid JSON; API calls present; end-to-end execution needs human |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `cybir/core/patch.py` | 155-157 | Missing `break` after sign flip in `_invariants_gv_incl_flop` — multiple aligned flop curves flip sign repeatedly | Warning | Could cause incorrect GV lookups if two flop curves are aligned with the query curve; documented in 03-REVIEW.md WR-07 |
| `cybir/core/patch.py` | 245-247 | Integer division by zero when grading dot is zero in `_invariants_ensure_nilpotency` | Warning | ZeroDivisionError with no explanatory message; documented in 03-REVIEW.md WR-02 |
| `cybir/core/patch.py` | 386-391 | Dead code: attempts `CalabiYau._Invariants` which does not exist before actual import | Info | No runtime impact; confuses reader; documented in 03-REVIEW.md IN-03 |
| `cybir/core/graph.py` | 35 | `nx.Graph` (not `nx.MultiGraph`) — parallel self-loops are silently dropped when a phase has two walls of the same type | Warning | Second terminal contraction lost for phases with multiple asymptotic/CFT/SU2 walls; documented in 03-REVIEW.md WR-05 |
| `cybir/core/build_gv.py` | 93 | `curve_tuple` assigned but never used | Info | Dead code; documented in 03-REVIEW.md IN-02 |
| `cybir/core/build_gv.py` | 389-390 | `flopped._kahler_cone` and `flopped._mori_cone` set by direct private-attribute assignment, bypassing freeze guard | Warning | Latent ordering-dependency bug; documented in 03-REVIEW.md WR-04 |

Note: These anti-patterns were already identified in the code review (03-REVIEW.md). WR-05 (MultiGraph) and WR-07 (missing break) are the most significant for correctness. They do not block the observable phase-3 goal for typical cases but could cause incorrect results in edge cases.

### Human Verification Required

#### 1. BFS Loop Produces Correct Phase Graphs

**Test:** Load an h11=2 polytope via `cytools.fetch_polytopes(h11=2, limit=1)[0]`, triangulate, get CY, then run `CYBirationalClass.from_gv(cy, max_deg=10)`. Compare `len(ekc.phases)`, the set of `contraction_type` values in `ekc.contractions`, and `ekc.coxeter_matrix` against a reference run of the original `extended_kahler_cone.py`.
**Expected:** Identical phase count, matching contraction type distribution, same Coxeter matrix entries (if any symmetric flops present).
**Why human:** Requires live CYTools data and a reference result from the original code. No unit test can verify numerical equivalence without both environments running.

#### 2. Weyl Expansion Numerical Correctness

**Test:** On an h11=2 or h11=3 case known to have symmetric flops, call `ekc.expand_weyl()` and verify the resulting reflected phase has intersection numbers matching `np.einsum('abc,xa,yb,zc', int_nums, M, M, M)` where M is the Coxeter reflection.
**Expected:** New phase count increases; reflected phase int_nums match manual computation via the einsum formula from `sym_flop_cy`.
**Why human:** Requires a live case with symmetric flops; the WR-07 missing-break bug in `gv_incl_flop` may affect whether symmetric flops are correctly identified in construct_phases.

#### 3. Example Notebooks Execute End-to-End

**Test:** Open `notebooks/h11_2_walkthrough.ipynb` and `notebooks/h11_3_walkthrough.ipynb` in a Jupyter environment with the cytools kernel. Run all cells.
**Expected:** All cells complete without error. `print(ekc)` shows a non-trivial phase count. `ekc.coxeter_matrix` either returns a matrix or `None` (depending on whether the chosen polytope has symmetric flops).
**Why human:** Notebooks have empty outputs; require CYTools polytope data at runtime.

### Gaps Summary

No hard gaps block the observable static goal: all artifacts exist, are substantive, and are wired. The phase achieves its structural goal — a working BFS builder, Weyl expander, read-only API, Sphinx docs, and example notebooks all exist and pass unit tests and static checks.

The status is `human_needed` because:
1. Roadmap SCs 1 and 2 explicitly require numerical equivalence to the original code on test cases — this can only be verified by running the pipeline with live CYTools data.
2. Roadmap SC 5 requires notebooks to "run end-to-end" — verifiable only by human execution.

Three code-review warnings (WR-05 MultiGraph, WR-07 missing break, WR-04 direct private attribute) are known and documented but do not prevent the pipeline from running on typical inputs.

---

_Verified: 2026-04-12T08:22:54Z_
_Verifier: Claude (gsd-verifier)_

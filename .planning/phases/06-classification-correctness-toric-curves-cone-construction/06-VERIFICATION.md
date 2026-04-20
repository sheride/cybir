---
phase: 06-classification-correctness-toric-curves-cone-construction
verified: 2026-04-19T23:59:00Z
status: human_needed
score: 18/19 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run compare_orbit.py on all 243 polytopes and confirm the 3 remaining data mismatches (#88, #168, #174) are pre-existing bugs unrelated to Phase 6 work"
    expected: "28 Coxeter-limit failures and 3 data mismatches are acknowledged pre-existing issues; no regressions introduced by Phase 6 work"
    why_human: "Plan 06-06 acceptance criteria stated all 7 previously mismatched polytopes should now pass, but only 4/7 were reclassified. The SUMMARY documents this as a deviation with explanation, but human judgment is required to accept the partial resolution as sufficient for phase completion."
---

# Phase 6: Classification Correctness, Toric Curves & Cone Construction — Verification Report

**Phase Goal:** Fix GrossFlop misclassification (Kahler cone check for symmetric flop candidates), add toric curve computation with FRST detection and Mori cone bounds, CoxeterGroup dataclass with flexible orbit expansion (EKC/HEKC/all), cone construction (movable, EKC, HEKC), diagnose_curve convenience API, and re-validate h11=3 survey
**Verified:** 2026-04-19T23:59:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | GROSS_FLOP enum member exists in ContractionType with correct display names | VERIFIED | `types.py` line 56: `GROSS_FLOP = "gross_flop"`; notation dicts at lines 21/31 |
| 2  | is_symmetric_flop returns a tuple (is_symmetric, is_gross_flop) | VERIFIED | `classify.py` lines 280/286/288: returns `(False, False)`, `(False, True)`, `(True, False)` |
| 3  | classify_contraction produces GROSS_FLOP when condition (a) passes but (b) fails | VERIFIED | `classify.py` line 398: `ctype = ContractionType.GROSS_FLOP` after `is_gross` check |
| 4  | CoxeterGroup frozen dataclass provides order, rank, and repr with subscript notation | VERIFIED | `types.py` line 484+: `@dataclass(frozen=True) class CoxeterGroup` with `order`, `rank`, `__repr__` |
| 5  | Re-classifying a curve from a different phase logs a warning if category differs | VERIFIED | `build_gv.py` lines 380/505-514: `classified_curves = {}` dict initialized, warning logged on mismatch |
| 6  | apply_coxeter_orbit accepts reflections parameter selecting ekc/hekc/all/custom | VERIFIED | `coxeter.py` line 724: `def apply_coxeter_orbit(ekc, reflections='ekc', phases=True)` |
| 7  | EKC expansion uses only symmetric flop reflections; HEKC adds SU2_NONGENERIC_CS | VERIFIED | `coxeter.py` lines 769-796: mode selection logic with 'ekc'/'hekc'/'all' branches |
| 8  | CYBirationalClass stores CoxeterGroup object after orbit expansion | VERIFIED | `coxeter.py` line 834: `ekc._coxeter_group = coxeter_group`; `ekc.py` line 364: `coxeter_group` property |
| 9  | induced_2face_triangulations computes 2-face triangulations from FRST Triangulation objects | VERIFIED | `toric_curves.py` line 97: `def induced_2face_triangulations(polytope, triangulations)` — exists and importable |
| 10 | Toric curve enumeration finds edges in 2-face triangulations and classifies them | VERIFIED | `toric_curves.py` line 293: `def compute_toric_curves(cy, face_triangulations, tip=None)` with `in_basis=False` at line 352 |
| 11 | FRST detection trichotomy correctly identifies FRST, vex, and non-inherited phases | VERIFIED | `toric_curves.py` line 185: `def classify_phase_type(...)` returns ('frst',fan), ('vex',fan), or ('non_inherited', None) |
| 12 | BFS accumulates toric curves incrementally when check_toric=True | VERIFIED | `build_gv.py` line 355: `def _run_bfs(ekc, verbose, limit, check_toric=False)`; incremental merge at line 652 |
| 13 | SU2_NONGENERIC_CS and SU2 pairs tracked for HEKC/all orbit expansion | VERIFIED | `build_gv.py` lines 182-203: `ekc._su2_pairs.append(...)` and `ekc._nongeneric_cs_pairs.append(...)` |
| 14 | Mori cone inner/outer bounds accessible per phase | VERIFIED | `ekc.py` lines 521/500: `def mori_cone_inner(...)` and `def mori_cone_outer(...)` |
| 15 | Phase classification (FRST/vex/non-inherited) exposed via API | VERIFIED | `ekc.py` lines 449/468/478/488: `phase_type`, `frst_phases`, `vex_phases`, `non_inherited_phases` |
| 16 | movable_cone, effective_cone, extended_kahler_cone, hyperextended_kahler_cone all exist | VERIFIED | `ekc.py` lines 697/718/739/757/791: all five cone construction methods present |
| 17 | diagnose_curve accepts CYTools Invariants or plain GV list; performs toric cross-check | VERIFIED | `ekc.py` line 859: standalone `diagnose_curve(cy, curve, max_deg=10, gvs=None, ekc=None)` with `isinstance(gvs, list)` branch |
| 18 | All new public API exported from cybir.core and cybir | VERIFIED | `cybir/core/__init__.py` lines 18/23-29: CoxeterGroup, ToricCurveData, toric functions, diagnose_curve; `cybir/__init__.py` lines 20/24-25 |
| 19 | h11=3 survey GrossFlop fix resolves misclassifications; compare_orbit re-validated | PARTIAL | 4/6 known mismatches reclassified as GROSS_FLOP (#22, #38, #89, #156); #39 now passes; #88/#168/#174 remain as pre-existing data mismatches; 28 Coxeter-limit failures (pre-existing). Plan 06-06 acceptance criteria called for all 7 mismatches resolved; only 5/7 resolved. |

**Score:** 18/19 truths verified (truth 19 is partial, triggering human verification)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cybir/core/types.py` | GROSS_FLOP enum, CoxeterGroup dataclass, toric_origin on ExtremalContraction | VERIFIED | All three present; GROSS_FLOP at line 56, CoxeterGroup at line 484, toric_origin at lines 382/393/478 |
| `cybir/core/classify.py` | GrossFlop detection via _kahler_cones_match | VERIFIED | `_kahler_cones_match` at line 175, `is_symmetric_flop` returns tuple |
| `cybir/core/build_gv.py` | GROSS_FLOP accumulation, check_toric, classification invariance | VERIFIED | `GROSS_FLOP` at line 489, `check_toric=False` at line 355, `classified_curves` at line 380 |
| `cybir/core/coxeter.py` | Flexible apply_coxeter_orbit with reflections parameter | VERIFIED | `reflections='ekc'` at line 724, all three mode branches present, CoxeterGroup construction at line 829 |
| `cybir/core/ekc.py` | CoxeterGroup integration, cone methods, Mori bounds, diagnose_curve | VERIFIED | All methods present; `_coxeter_group` at line 71, all 5 cone methods, `mori_cone_inner`/`outer`, `_verify_mori_bounds`, `diagnose_curve` |
| `cybir/core/toric_curves.py` | ToricCurveData, induced_2face_triangulations, classify_phase_type, compute_toric_curves, orient_curves_for_phase | VERIFIED | All 5 functions present; `in_basis=False` at line 352; `VectorConfiguration(Q.T)` at line 246 |
| `cybir/core/__init__.py` | CoxeterGroup, ToricCurveData, toric functions, diagnose_curve exports | VERIFIED | All exports present in `__all__` |
| `cybir/__init__.py` | CoxeterGroup, ToricCurveData, diagnose_curve top-level exports | VERIFIED | Lines 20/24-25/49/53-54 |
| `tests/test_types.py` | GROSS_FLOP, CoxeterGroup, toric_origin, Phase 6 import tests | VERIFIED | Lines 360/473/481/492: all test classes/methods present |
| `tests/test_classify.py` | _kahler_cones_match, is_symmetric_flop tuple, GROSS_FLOP accumulation | VERIFIED | TestKahlerConesMatch (line 425), tuple tests (lines 230/259), TestGrossFlopAccumulation (line 474) |
| `tests/test_coxeter.py` | reflections parameter, CoxeterGroup property, coxeter_group type tests | VERIFIED | Lines 1225/1232/1241/1272/1283/1292 — all present |
| `tests/test_toric_curves.py` | TestToricCurveData, TestOrientCurves, TestClassifyPhaseType, TestSharedEdgeConsistency | VERIFIED | All four test classes present; 9 passed, 1 skipped |
| `tests/test_build_gv.py` | Paired storage tests, check_toric tests, phase classification API tests | VERIFIED | Lines 294/361/379/406 — all present |
| `tests/survey_h11_3.py` | gross_flop_count tracking in JSONL output | VERIFIED | Lines 68-70/85: GROSS_FLOP counting and output field |
| `tests/compare_orbit_results.jsonl` | Full 243-polytope validation results | VERIFIED | File exists with 243 records; 112 pass, 31 fail (28 Coxeter-limit + 3 data), 100 skip |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cybir/core/classify.py` | `cybir/core/build_gv.py` | `classify_contraction` called; GROSS_FLOP override in `_run_bfs` | VERIFIED | `build_gv.py` line 489: `result["contraction_type"] = ContractionType.GROSS_FLOP` |
| `cybir/core/coxeter.py` | `cybir/core/ekc.py` | `apply_coxeter_orbit(self, reflections='ekc', phases=True)` | VERIFIED | `ekc.py` line 131; delegates to `coxeter.py` line 724 |
| `cybir/core/build_gv.py` | `cybir/core/toric_curves.py` | `classify_phase_type` and `compute_toric_curves` called during BFS | VERIFIED | `build_gv.py` line 383: `from .toric_curves import classify_phase_type, ...` |
| `cybir/core/build_gv.py` | `cybir/core/ekc.py` | `_verify_mori_bounds` called after toric compilation | VERIFIED | `build_gv.py` lines 439/691 |
| `cybir/core/ekc.py` | `cybir/core/toric_curves.py:ToricCurveData` | `ekc._toric_curve_data.gv_dict` lookup in `diagnose_curve` | VERIFIED | `ekc.py` `diagnose_curve`: `tcd = getattr(ekc, '_toric_curve_data', None)` |
| `tests/survey_h11_3.py` | `cybir.core.types.ContractionType.GROSS_FLOP` | contraction type counting | VERIFIED | `survey_h11_3.py` lines 68-70 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `cybir/core/toric_curves.py` `compute_toric_curves` | `intnums_raw` | `cy.intersection_numbers(in_basis=False)` | Yes — CYTools DB query | FLOWING |
| `cybir/core/ekc.py` `mori_cone_inner` | `tcd.all_curves()` | `ekc._toric_curve_data` populated by BFS | Yes — incremental merge from real curve computation | FLOWING |
| `cybir/core/ekc.py` `effective_cone` | `_eff_cone_gens` | BFS accumulation in `_accumulate_generators` | Yes — accumulated from real phase walls | FLOWING |
| `cybir/core/ekc.py` `extended_kahler_cone` | `phase.kahler_cone.rays()` | CYTools Cone objects from each phase | Yes — real cone geometry | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| GROSS_FLOP importable | `from cybir.core.types import ContractionType; assert hasattr(ContractionType, 'GROSS_FLOP')` | Passes (verified via grep) | PASS |
| CoxeterGroup importable | `from cybir import CoxeterGroup, ToricCurveData, diagnose_curve` (per test_phase6_imports) | 441 passed, 101 skipped (full suite) | PASS |
| All 441 tests pass | `conda run -n cytools pytest tests/ -x -q` | 441 passed, 101 skipped, 6 warnings in 17.12s | PASS |
| VectorConfiguration uses Q.T | grep for `VectorConfiguration(Q.T)` in toric_curves.py | Found at line 246 | PASS |
| in_basis=False in compute_toric_curves | grep for `in_basis=False` | Found at line 352 | PASS |

### Requirements Coverage

No requirement IDs were declared in any of the 6 plan frontmatters (all `requirements: []`). REQUIREMENTS.md does not map any requirements to Phase 6. No orphaned requirements identified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `cybir/core/ekc.py` | `hyperextended_kahler_cone` | Delegates identically to `extended_kahler_cone()` with no added behavior | INFO | By design — documented in SUMMARY that it is equivalent when orbit expanded with 'hekc'; exists for API clarity |
| `cybir/core/toric_curves.py` | `TestSharedEdgeConsistency` | Test skips — no shared edges found in h11=2 sample | INFO | D-07 empirical check deferred to integration; the skip is documented |
| `tests/compare_orbit_results.jsonl` | 28 entries | Coxeter limit failures ("Matrix does not return to identity within 200 multiplications") | WARNING | Pre-existing failures in Coxeter enumeration, unrelated to Phase 6 scope |
| `tests/compare_orbit_results.jsonl` | 3 entries (#88, #168, #174) | Data mismatches: phase counts or generator counts differ vs original code | WARNING | Pre-existing bugs acknowledged in SUMMARY; #88 has 4 vs 8 phases, root cause unclear |

No blockers found in core source files. Anti-patterns are documented pre-existing issues.

### Human Verification Required

#### 1. h11=3 Re-validation Acceptance

**Test:** Review compare_orbit_results.jsonl and confirm that the 3 remaining data mismatches (#88, #168, #174) and 28 Coxeter-limit failures are genuinely pre-existing issues not introduced or worsened by Phase 6 changes.

**Expected:** The 4 polytopes reclassified as GROSS_FLOP (#22, #38, #89, #156) no longer appear in the failure list (they skip as "no_symmetric_flops"). Polytope #39 now passes. Polytopes #88, #168, #174 fail for the same reasons they did in Phase 5 (the Phase 5 baseline should show the same pattern). The 28 Coxeter-limit failures also pre-date Phase 6.

**Why human:** Plan 06-06's acceptance criteria explicitly stated "all 7 previously mismatched polytopes now match." The SUMMARY documents that only 5/7 were resolved (#22, #38, #39, #89, #156 resolved; #88 still fails with a different root cause; the 7th was unclear). Whether the partial resolution is sufficient for phase acceptance requires a human judgment call, as the SUMMARY characterizes the 3 remaining failures as "pre-existing issues unrelated to the GrossFlop fix" — but this needs developer verification.

To verify, compare `tests/compare_orbit_results.jsonl` against any Phase 5 baseline results. If #88, #168, #174 showed the same failure pattern before Phase 6 work began, the phase goal is substantively achieved for the GrossFlop fix.

### Gaps Summary

No structural gaps were found. All must-have artifacts exist, are substantive, and are wired correctly. The full test suite passes (441 passed, 101 skipped). The only item requiring human verification is whether the partial h11=3 re-validation result (5/7 previously-mismatched polytopes now resolved, 3 pre-existing data mismatches remain) constitutes acceptable phase completion.

The core GrossFlop fix works correctly: 4 polytopes are correctly reclassified as GROSS_FLOP, 1 polytope (#39) passes cleanly, and the remaining failures are either documented pre-existing issues or the Coxeter enumeration limit (200 multiplications) which is a known constraint.

---

_Verified: 2026-04-19T23:59:00Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 04-coxeter-weyl
verified: 2026-04-12T19:30:00Z
status: gaps_found
score: 5/6 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Reflected phases carry properly oriented GV Invariants objects (reflected flop curve images)"
    status: partial
    reason: >
      The _invariants_for_impl function and the ekc.invariants_for() API exist and work correctly
      for fundamental-domain phases (those with curve_signs set during construct_phases BFS).
      However, reflected phases created by reflect_phase_data are constructed WITHOUT curve_signs
      (the reflect_phase_data CalabiYauLite constructor call does not set curve_signs or gv_invariants).
      When invariants_for() is called on a Weyl-expanded phase, target_signs is None, so
      _invariants_for_impl silently returns root_invariants unchanged. This is incorrect for phases
      not in the same GV orientation as the root. Noted as IN-06 in the code review.
    artifacts:
      - path: "cybir/core/coxeter.py"
        issue: >
          reflect_phase_data (line 710-717) constructs CalabiYauLite without curve_signs.
          _invariants_for_impl (line 1020-1022) silently returns root_invariants when
          target_signs is None, with no warning.
    missing:
      - >
        reflect_phase_data should either: (a) compute and attach curve_signs to reflected phases
        by evaluating tip @ g(curve) for each flop curve; or (b) _invariants_for_impl should
        warn when called on a Weyl-expanded phase with no curve_signs (as suggested in IN-06
        of code review), so failures are not silent.
      - >
        Add a test that calls ekc.invariants_for() on a Weyl-expanded phase label and verifies
        either correct reorientation or a meaningful error/warning.

---

# Phase 4: Coxeter Group & Weyl Expansion Verification Report

**Phase Goal:** Proper Coxeter group construction from symmetric-flop reflections with finite-type
detection and memory-safe enumeration, full Weyl orbit expansion acting on all phase data with
correct index conventions (g on Mori, (g^-1)^T on Kahler), and generator accumulation from
reflected phases
**Verified:** 2026-04-12T19:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| SC-1 | `coxeter.py` constructs the Coxeter group from symmetric-flop reflection matrices using streaming BFS with memory estimation | VERIFIED | `enumerate_coxeter_group` in coxeter.py (line 567) does BFS on Cayley graph with int64 arithmetic, memory estimation at lines 610-618, yields identity first, all 370 tests pass |
| SC-2 | Finite type detection via positive definiteness of the bilinear form; infinite type stops and reports fundamental domain only | VERIFIED | `is_finite_type` (line 237) checks `eigvalsh > 1e-10`; `apply_coxeter_orbit` (line 766-773) returns early with logger.warning when infinite type detected; test `test_infinite_type_logs_warning` covers this |
| SC-3 | Weyl expansion applies every group element to every fundamental-domain phase with correct index conventions (g on Mori/kappa/c2, (g^-1)^T on Kahler) | VERIFIED | `reflect_phase_data` (line 642): einsum on int_nums with g (Mori), g @ c2, `old_rays @ g_inv_int` for Kahler; integrality assertion on g_inv; `apply_coxeter_orbit` streams over all g from enumerate_coxeter_group |
| SC-4 | Reflected phases carry properly oriented GV Invariants objects (reflected flop curve images) | PARTIAL | `invariants_for()` API exists and works for fundamental-domain phases via curve_signs comparison + `flop_gvs`. BUT reflected phases created by `reflect_phase_data` have `curve_signs=None`, so calling `invariants_for` on a Weyl-expanded phase silently returns root invariants unchanged. No warning is emitted (IN-06). |
| SC-5 | Infinity cone gens and effective cone gens are accumulated from all reflected phases (Kahler rays, zero-vol divisors, terminal wall curves) | VERIFIED | `apply_coxeter_orbit` lines 820-899: Kahler rays -> `_eff_cone_gens`, ASYMPTOTIC/CFT curves -> `_infinity_cone_gens`, CFT/SU2 zero-vol divisors -> `_eff_cone_gens`; `phases=False` mode also accumulates; tests cover all three accumulation paths |
| SC-6 | Only symmetric-flop Coxeter matrices are used (not su(2)); the birational geometry is the correct object | VERIFIED | `build_gv.py` lines 115-128: `_sym_flop_refs` populated ONLY for `ContractionType.SYMMETRIC_FLOP`; `apply_coxeter_orbit` extracts from `_sym_flop_refs` only; SU2 reflections go to `_coxeter_refs` (separate set, unused by orbit expansion) |

**Score:** 5/6 truths verified (SC-4 partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cybir/core/coxeter.py` | Coxeter group construction, type classification, BFS enumeration | VERIFIED | 1037 lines, 14 functions (matrix_period, coxeter_reflection, coxeter_element, coxeter_order_matrix, coxeter_bilinear_form, is_finite_type, _decompose_irreducible, _classify_irreducible, classify_coxeter_type, coxeter_group_order, enumerate_coxeter_group, reflect_phase_data, apply_coxeter_orbit, to_fundamental_domain, _invariants_for_impl) |
| `cybir/core/types.py` | CalabiYauLite with curve_signs and tip fields | VERIFIED | curve_signs (line 212) and tip (line 224) properties present, backed by _curve_signs and _tip set in constructor |
| `cybir/core/build_gv.py` | BFS persists curve_signs and tip on each CalabiYauLite | VERIFIED | `root._curve_signs` set at line 292; `flopped._curve_signs` set at line 424; `_sym_flop_curves` populated at line 128 |
| `cybir/core/ekc.py` | apply_coxeter_orbit, invariants_for, to_fundamental_domain methods | VERIFIED | All three methods present (lines 108, 129, 154); coxeter_type/coxeter_order properties present (lines 325, 339) |
| `cybir/__init__.py` | coxeter functions re-exported | VERIFIED | `from cybir.core.coxeter import (classify_coxeter_type, coxeter_element, coxeter_matrix, coxeter_order_matrix, coxeter_reflection, ...)` at line 23 |
| `cybir/core/weyl.py` | DELETED | VERIFIED | File does not exist; test_weyl.py also deleted |
| `tests/test_coxeter.py` | 76 tests covering full Coxeter pipeline | VERIFIED | 76 tests, all passing in 3.69s |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `coxeter.py:apply_coxeter_orbit` | `coxeter.py:enumerate_coxeter_group` | `for g in enumerate_coxeter_group(reflections, expected_order)` (line 800) | WIRED | Confirmed in source |
| `ekc.py:apply_coxeter_orbit` | `coxeter.py:apply_coxeter_orbit` | `from .coxeter import apply_coxeter_orbit` (lazy import) (line 108-126) | WIRED | Confirmed |
| `ekc.py:invariants_for` | `coxeter.py:_invariants_for_impl` | `from .coxeter import _invariants_for_impl` at line 169 | WIRED | Confirmed |
| `ekc.py:to_fundamental_domain` | `coxeter.py:to_fundamental_domain` | `from .coxeter import to_fundamental_domain` at line 173 | WIRED | Confirmed |
| `build_gv.py:_accumulate_generators` | `ekc._sym_flop_refs` | SYMMETRIC_FLOP gate at line 115 | WIRED | Confirmed; SU2 explicitly excluded |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `apply_coxeter_orbit` | reflections list | `ekc._sym_flop_refs` (set, from BFS) | Yes — populated by build_gv SYMMETRIC_FLOP contractions | FLOWING |
| `_invariants_for_impl` | target_signs | `target_phase.curve_signs` | Yes for fundamental-domain phases; None for Weyl-expanded phases | STATIC for reflected phases |
| `to_fundamental_domain` | reflections, curves | `_sym_flop_refs` (set) + `_sym_flop_curves` (list) | Yes | POTENTIAL MISMATCH — see WR-04 below |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All coxeter imports work | `conda run -n cytools python -c "from cybir.core.coxeter import coxeter_order_matrix, classify_coxeter_type, enumerate_coxeter_group, is_finite_type; print('OK')"` | OK | PASS |
| 76 coxeter tests pass | `conda run -n cytools python -m pytest tests/test_coxeter.py -q` | 76 passed in 3.69s | PASS |
| Full suite passes | `conda run -n cytools python -m pytest tests/ -q` | 370 passed, 100 skipped, 52 warnings | PASS |
| weyl.py deleted | `test ! -f cybir/core/weyl.py` | weyl.py DELETED | PASS |
| SU2 excluded from _sym_flop_refs | grep in build_gv.py | `_sym_flop_refs` only populated at `ctype == SYMMETRIC_FLOP` branch (line 115) | PASS |

### Requirements Coverage

The plans claim SC-1 through SC-6 (roadmap success criteria numbering for Phase 4).
REQUIREMENTS.md uses a different ID scheme (MATH-*, PIPE-*, etc.) and does not assign SC-1..SC-6
labels — those are internal to the phase roadmap. The REQUIREMENTS.md traceability table maps
PIPE-02 ("Weyl orbit expansion for hyperextended cone") to Phase 3 as complete; Phase 4 refines
and corrects that implementation.

| Requirement (Roadmap SC) | Plans | Status | Evidence |
|--------------------------|-------|--------|---------|
| SC-1: coxeter.py streaming BFS with memory estimation | 04-01 | SATISFIED | enumerate_coxeter_group exists with memory cap, int64 BFS |
| SC-2: Finite-type detection stops infinite groups | 04-01, 04-02 | SATISFIED | is_finite_type + early return in apply_coxeter_orbit |
| SC-3: Correct index conventions | 04-02 | SATISFIED | g on Mori (einsum), g_inv on Kahler, tested |
| SC-4: Reflected phases carry properly oriented GV Invariants | 04-03 | PARTIAL | On-demand API exists but silent failure for Weyl-expanded phases |
| SC-5: Generator accumulation complete | 04-02 | SATISFIED | All three generator types accumulated |
| SC-6: Only symmetric-flop used | 04-01, 04-02 | SATISFIED | _sym_flop_refs gated on SYMMETRIC_FLOP only |

### Anti-Patterns Found

| File | Issue | Severity | Impact |
|------|-------|----------|--------|
| `cybir/core/coxeter.py:_invariants_for_impl` (line 1020-1022) | Silent return of root_invariants when target_signs is None, with no warning; occurs for all Weyl-expanded phases | Warning (IN-06 from review) | SC-4 partial — on-demand GV reconstruction returns wrong result silently |
| `cybir/core/ekc.py:to_fundamental_domain` (lines 177-178) | `_sym_flop_refs` is a `set` (unordered); `_sym_flop_curves` is a parallel `list`; iteration order of set is nondeterministic, causing (reflection[i], curve[i]) mismatch for geometries with more than one symmetric-flop wall | Warning (WR-04 from review) | to_fundamental_domain produces wrong results when >1 sym-flop wall present |
| `cybir/core/coxeter.py:to_fundamental_domain` (line 944-976) | Off-by-one in loop guard: `while iters <= max_iter` allows one extra iteration; outer `raise RuntimeError` at line 976 is dead code | Info (WR-01 from review) | Safety property preserved by coincidence; confusing logic |
| `cybir/core/coxeter.py:apply_coxeter_orbit` (line 831) | `sign_a = data.get("curve_sign_a", 1)` assigned but never used | Info (IN-01 from review) | Unused variable, no functional impact |
| `cybir/core/build_gv.py:_accumulate_generators` (line 93) | `curve_tuple = tuple(result.get("gv_series", []))` computed but never used | Info (IN-02 from review) | Unused variable, no functional impact |

### Gaps Summary

**1 gap blocking SC-4 (partial):** The `invariants_for()` API is correctly implemented for
fundamental-domain phases. However, reflected phases created by `reflect_phase_data` have
`curve_signs=None` because the constructor call at lines 710-717 of coxeter.py does not populate
this field. When `invariants_for()` is called on such a phase, `_invariants_for_impl` hits the
`if root_signs is None or target_signs is None: return root_invariants` guard and silently returns
the root invariants — which may have incorrect flop curve orientations for the reflected phase.

The code review (IN-06) identified this issue and proposed adding a warning. The proper fix is
either to (a) propagate curve_signs onto reflected phases by computing `tip @ g(curve)` signs
during reflect_phase_data, or (b) add a warning so the failure is not silent.

**1 additional warning-severity bug (WR-04):** `_sym_flop_refs` is a Python `set` and
`_sym_flop_curves` is a parallel `list`. In `CYBirationalClass.to_fundamental_domain`, the set is
iterated in arbitrary order while curves are taken positionally from the list. For any geometry
with more than one symmetric-flop wall, the reflection/curve pairing will be wrong. This renders
`to_fundamental_domain` (SC-3 chamber walk) unreliable in the multi-wall case. The fix from the
code review (WR-04) is to store reflection-curve pairs together as `_sym_flop_ref_curve_pairs`.

**Note on REQUIREMENTS.md coverage:** The REQUIREMENTS.md SC-1..SC-6 identifiers referenced in
the plan frontmatter are internal roadmap success criteria for Phase 4, not the global requirement
IDs in REQUIREMENTS.md (which uses DATA-*, MATH-*, PIPE-* naming). No orphaned REQUIREMENTS.md
IDs were found for Phase 4.

---

_Verified: 2026-04-12T19:30:00Z_
_Verifier: Claude (gsd-verifier)_

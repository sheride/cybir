---
phase: 04-coxeter-weyl
verified: 2026-04-12T20:10:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 5/6
  gaps_closed:
    - "Reflected phases carry properly oriented GV Invariants objects (reflected flop curve images)"
    - "WR-04: _sym_flop_refs + _sym_flop_curves order mismatch in to_fundamental_domain"
  gaps_remaining: []
  regressions: []
---

# Phase 4: Coxeter Group & Weyl Expansion Verification Report

**Phase Goal:** Proper Coxeter group construction from symmetric-flop reflections with finite-type
detection and memory-safe enumeration, full Weyl orbit expansion acting on all phase data with
correct index conventions (g on Mori, (g^-1)^T on Kahler), and generator accumulation from
reflected phases
**Verified:** 2026-04-12T20:10:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 04-04)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| SC-1 | `coxeter.py` constructs the Coxeter group from symmetric-flop reflection matrices using streaming BFS with memory estimation | VERIFIED | `enumerate_coxeter_group` in coxeter.py line 800: `for g in enumerate_coxeter_group(reflections, expected_order)`. int64 arithmetic, memory estimation, identity-first. 374 tests pass. |
| SC-2 | Finite type detection via positive definiteness of the bilinear form; infinite type stops and reports fundamental domain only | VERIFIED | `is_finite_type` checks `eigvalsh > 1e-10`. `apply_coxeter_orbit` lines 766-773 return early with logger.warning when infinite type. |
| SC-3 | Weyl expansion applies every group element to every fundamental-domain phase with correct index conventions (g on Mori/kappa/c2, (g^-1)^T on Kahler) | VERIFIED | `reflect_phase_data`: einsum on int_nums with g (Mori), `g @ c2`, `old_rays @ g_inv_int` for Kahler. `to_fundamental_domain` now reads from `_sym_flop_pairs` (ordered list), pairing is order-safe. |
| SC-4 | Reflected phases carry properly oriented GV Invariants objects (reflected flop curve images) | VERIFIED | `apply_coxeter_orbit` lines 815-827: after creating each reflected phase, computes `reflected_tip = g_inv_int.T @ fund_phase.tip` and sets `new_phase._curve_signs` from root phase keys. `_invariants_for_impl` emits warning if called on Weyl-expanded phase with no curve_signs (IN-06 safety net). Tests `test_reflected_phase_has_curve_signs`, `test_reflected_phase_has_tip`, `test_reflected_phase_curve_signs_differ_from_root` all pass. |
| SC-5 | Infinity cone gens and effective cone gens are accumulated from all reflected phases (Kahler rays, zero-vol divisors, terminal wall curves) | VERIFIED | `apply_coxeter_orbit` lines 834-895: Kahler rays -> `_eff_cone_gens`, ASYMPTOTIC/CFT curves -> `_infinity_cone_gens`, CFT/SU2 zero-vol divisors -> `_eff_cone_gens`. phases=False mode also accumulates. |
| SC-6 | Only symmetric-flop Coxeter matrices are used (not su(2)); the birational geometry is the correct object | VERIFIED | `build_gv.py` lines 115-128: `_sym_flop_refs` populated only for `ContractionType.SYMMETRIC_FLOP`. `apply_coxeter_orbit` reads `reflections = [np.array(r) for r, _ in ekc._sym_flop_pairs]` from the authoritative paired list. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cybir/core/coxeter.py` | curve_signs computed for reflected phases | VERIFIED | Lines 815-827: `new_phase._curve_signs` set after each reflected phase creation; warning added in `_invariants_for_impl` at line 1037-1042 |
| `cybir/core/ekc.py` | `_sym_flop_pairs` replaces `_sym_flop_refs + _sym_flop_curves` | VERIFIED | `__init__` line 70: `self._sym_flop_pairs = []`; `to_fundamental_domain` lines 177-178: `reflections = [np.array(r) for r, _ in self._sym_flop_pairs]`, `curves = [np.array(c) for _, c in self._sym_flop_pairs]` |
| `cybir/core/build_gv.py` | Populates `_sym_flop_pairs` instead of separate collections | VERIFIED | Lines 120-128: dedup guard on `_sym_flop_refs`, then appends `(ref_key, curve_tuple)` to `_sym_flop_pairs` |
| `tests/test_coxeter.py` | Tests for curve_signs on reflected phases and warning emission | VERIFIED | 4 new tests: `test_reflected_phase_has_curve_signs`, `test_reflected_phase_has_tip`, `test_reflected_phase_curve_signs_differ_from_root`, `test_invariants_for_weyl_phase_warns_on_missing_signs` — all pass |
| `tests/test_build_gv.py` | MockEKC uses `_sym_flop_pairs` | VERIFIED | Line 120: `self._sym_flop_pairs = []`; no `_sym_flop_curves` reference |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `coxeter.py:apply_coxeter_orbit` | `CalabiYauLite._curve_signs` | `new_phase._curve_signs = {c: sign(reflected_tip @ c) for c in root_phase.curve_signs}` (line 824) | WIRED | Confirmed — uses root phase keys as canonical set |
| `ekc.py:to_fundamental_domain` | `ekc._sym_flop_pairs` | `[np.array(r) for r, _ in self._sym_flop_pairs]` (line 177) | WIRED | Confirmed — ordered list, no more set/list mismatch |
| `coxeter.py:apply_coxeter_orbit` | `ekc._sym_flop_pairs` | `reflections = [np.array(r) for r, _ in ekc._sym_flop_pairs]` (line 759) | WIRED | Confirmed |
| `build_gv.py:_accumulate_generators` | `ekc._sym_flop_pairs` | `ekc._sym_flop_pairs.append((ref_key, curve_tuple))` after dedup guard (line 128) | WIRED | Confirmed — `_sym_flop_curves` fully removed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `apply_coxeter_orbit` | `reflections` | `ekc._sym_flop_pairs` (ordered list) | Yes — populated by build_gv SYMMETRIC_FLOP contractions with dedup | FLOWING |
| `apply_coxeter_orbit` | `new_phase._curve_signs` | `root_phase.curve_signs` keys + `reflected_tip` | Yes — computed from g_inv_int.T @ fund_phase.tip for each reflected phase | FLOWING |
| `_invariants_for_impl` | `target_signs` | `target_phase.curve_signs` | Yes for all phases (fundamental and Weyl-expanded) — no more silent None | FLOWING |
| `to_fundamental_domain` | `reflections, curves` | `_sym_flop_pairs` (ordered list of tuples) | Yes — order-safe pairing | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 374 tests pass | `conda run -n cytools python -m pytest tests/ -q` | 374 passed, 100 skipped, 52 warnings | PASS |
| Gap-closure tests pass | `conda run -n cytools python -m pytest tests/test_coxeter.py tests/test_build_gv.py -x -q` | 97 passed | PASS |
| No `_sym_flop_curves` in source | `grep -r "_sym_flop_curves" cybir/ tests/` | No matches | PASS |
| `_sym_flop_pairs` present in ekc.py | `grep "_sym_flop_pairs" cybir/core/ekc.py` | Line 70, 177, 178 | PASS |
| curve_signs computed for reflected phases | `grep -n "curve_signs" cybir/core/coxeter.py` | Lines 815-827 set `new_phase._curve_signs` in apply_coxeter_orbit | PASS |

### Requirements Coverage

| Requirement (Roadmap SC) | Plans | Status | Evidence |
|--------------------------|-------|--------|---------|
| SC-1: coxeter.py streaming BFS with memory estimation | 04-01 | SATISFIED | enumerate_coxeter_group with memory cap and int64 arithmetic |
| SC-2: Finite-type detection stops infinite groups | 04-01, 04-02 | SATISFIED | is_finite_type + early return in apply_coxeter_orbit |
| SC-3: Correct index conventions + order-safe chamber walk | 04-02, 04-04 | SATISFIED | g on Mori, g_inv on Kahler; _sym_flop_pairs fixes pairing mismatch |
| SC-4: Reflected phases carry properly oriented GV Invariants | 04-03, 04-04 | SATISFIED | curve_signs computed for all reflected phases in apply_coxeter_orbit |
| SC-5: Generator accumulation complete | 04-02 | SATISFIED | All three generator types accumulated |
| SC-6: Only symmetric-flop used | 04-01, 04-02 | SATISFIED | _sym_flop_pairs gated on SYMMETRIC_FLOP only |

### Anti-Patterns Found

| File | Issue | Severity | Impact |
|------|-------|----------|--------|
| `cybir/core/coxeter.py:apply_coxeter_orbit` (line 845) | `sign_a = data.get("curve_sign_a", 1)` assigned but never used | Info (IN-01) | No functional impact; pre-existing |
| `cybir/core/build_gv.py:_accumulate_generators` (line 93) | `curve_tuple = tuple(result.get("gv_series", []))` computed but never used | Info (IN-02) | No functional impact; pre-existing |
| `cybir/core/coxeter.py:to_fundamental_domain` | Off-by-one in loop guard (`while iters <= max_iter` allows one extra iteration; outer raise is dead code) | Info (WR-01) | Safety property preserved by coincidence; confusing logic |

No blockers. The two gap items from the previous verification are fully resolved:

- **SC-4 (CLOSED):** `apply_coxeter_orbit` now computes `curve_signs` and `tip` for every reflected phase using `root_phase.curve_signs` keys as the canonical set. `_invariants_for_impl` now correctly differentiates reflected phases and emits a warning if a Weyl-expanded phase somehow has no `curve_signs`.
- **WR-04 (CLOSED):** `_sym_flop_curves` (unordered list, parallel to set) fully removed from all source and test files. Replaced by `_sym_flop_pairs` (ordered list of `(ref_tuple, curve_tuple)` pairs) everywhere.

### Human Verification Required

None. All must-haves are verified programmatically.

---

_Verified: 2026-04-12T20:10:00Z_
_Verifier: Claude (gsd-verifier)_

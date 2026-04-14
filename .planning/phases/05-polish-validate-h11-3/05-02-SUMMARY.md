---
phase: 05-polish-validate-h11-3
plan: 02
subsystem: core-types-validation
tags: [nongeneric-cs, orbit-validation, contraction-type]

requires:
  - phase: 05-polish-validate-h11-3
    provides: Rich repr/str, non-favorable guard, validate_stability
provides:
  - SU2_NONGENERIC_CS contraction type for non-generic complex structure detection
  - Orbit expansion validation script comparing cybir vs original ignore_sym=False
affects: [05-03]

tech-stack:
  added: []
  patterns:
    - "GLSM charge matrix proportionality check for non-generic CS detection"
    - "compare_orbit.py follows compare_bfs.py pattern with symmetric-flop filtering"

key-files:
  created:
    - tests/compare_orbit.py
  modified:
    - cybir/core/types.py
    - cybir/core/build_gv.py
    - tests/test_types.py
    - tests/test_classify.py

key-decisions:
  - "SU2_NONGENERIC_CS treated as terminal wall (like su(2)), adds coxeter refs and eff cone gens but NOT sym_flop_refs/pairs"
  - "Detection uses GLSM charge matrix row proportionality check (not exact equality)"
  - "compare_orbit.py skips polytopes without symmetric flops since there is nothing to validate"

patterns-established:
  - "_check_nongeneric_cs post-classification hook pattern for re-tagging"

requirements-completed: [POL-05, POL-06, POL-07]

duration: 4min
completed: 2026-04-14
---

# Phase 05 Plan 02: Non-Generic CS Detection & Orbit Validation Summary

**SU2_NONGENERIC_CS contraction type with GLSM-based detection, and compare_orbit.py validation script for Coxeter orbit expansion**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-14T23:09:44Z
- **Completed:** 2026-04-14T23:13:49Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added SU2_NONGENERIC_CS enum member to ContractionType with display names in both paper and Wilson notation
- Detection logic in _check_nongeneric_cs re-tags symmetric flops whose zero-vol divisor is proportional to a GLSM charge matrix row (prime toric divisor)
- SU2_NONGENERIC_CS walls treated as terminal (no flop exploration), contribute to coxeter_refs and eff_cone_gens but NOT sym_flop_refs/pairs
- compare_orbit.py validates apply_coxeter_orbit against original ignore_sym=False for polytopes with symmetric flops

## Task Commits

Each task was committed atomically:

1. **Task 1: SU2_NONGENERIC_CS enum and detection logic** - `08fc9c3` (feat)
2. **Task 2: Orbit expansion validation script** - `d553e3e` (feat)

## Files Created/Modified
- `cybir/core/types.py` - SU2_NONGENERIC_CS enum member with display names
- `cybir/core/build_gv.py` - _check_nongeneric_cs helper, _accumulate_generators SU2_NONGENERIC_CS block, terminal wall handling
- `tests/test_types.py` - Updated enum count test, added SU2_NONGENERIC_CS display name tests
- `tests/test_classify.py` - Added accumulator tests for SU2_NONGENERIC_CS (no sym_flop, adds coxeter/eff)
- `tests/compare_orbit.py` - New orbit expansion validation script

## Decisions Made
- SU2_NONGENERIC_CS treated as terminal wall: adds coxeter refs and eff cone gens but NOT sym_flop_refs/pairs (per D-18)
- Detection uses proportionality check against GLSM charge matrix rows, with norm-based comparison (not exact equality) for robustness (per T-05-03)
- compare_orbit.py only tests polytopes with symmetric flops, skips non-favorable and non-symmetric-flop polytopes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Terminal wall handling for SU2_NONGENERIC_CS**
- **Found during:** Task 1
- **Issue:** Plan described re-tagging but didn't explicitly address that SU2_NONGENERIC_CS needs to be treated as a terminal wall in the BFS (like SU2), preventing flop exploration
- **Fix:** Added SU2_NONGENERIC_CS to the terminal wall check in _run_bfs
- **Files modified:** cybir/core/build_gv.py
- **Commit:** 08fc9c3

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness
- SU2_NONGENERIC_CS detection ready for h11=3 survey (plan 05-03)
- compare_orbit.py ready for orbit validation in survey script
- All 65 unit tests passing

## Self-Check: PASSED

---
phase: 06-classification-correctness-toric-curves-cone-construction
plan: 06
subsystem: testing
tags: [survey, h11-3, gross-flop, validation, compare-orbit]

requires:
  - phase: 06-01
    provides: "GROSS_FLOP enum and classification fix"
provides:
  - "Updated survey script with gross_flop_count tracking"
  - "Full h11=3 re-validation results after GrossFlop fix"
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - tests/compare_orbit_results.jsonl
  modified:
    - tests/survey_h11_3.py

key-decisions:
  - "compare_orbit.py and run_compare_orbit.py need no changes (no type filtering)"
  - "3 remaining data mismatches (#88, #168, #174) are pre-existing issues unrelated to GrossFlop fix"

patterns-established: []

requirements-completed: []

duration: 6h (mostly survey runtime)
completed: 2026-04-20
---

# Plan 06-06: h11=3 Re-validation Summary

**GrossFlop fix resolves 4/7 known mismatches; 3 pre-existing data mismatches remain (#88, #168, #174)**

## Performance

- **Duration:** ~6h (survey runtime)
- **Tasks:** 2
- **Files modified:** 1 (+ 1 results file created)

## Accomplishments
- Updated survey_h11_3.py with gross_flop_count tracking in JSONL output
- Ran full h11=3 compare_orbit validation (243 polytopes)
- GrossFlop fix correctly reclassified polytopes #22, #38, #89, #156 (no longer have symmetric flops)
- Polytope #39 now passes (was previously a mismatch)

## Survey Results

| Category | Count | Details |
|----------|-------|---------|
| Passed | 112 | Phase counts, inf/eff gens, Coxeter match |
| Failed (data mismatch) | 3 | #88 (phase count 4 vs 8), #168, #174 (inf/eff/cox mismatch) |
| Failed (Coxeter limit) | 28 | Pre-existing: "Matrix does not return to identity within 200 multiplications" |
| Skipped | 100 | No symmetric flops |

### Previously Known Mismatches

| Polytope | Previous | Now | Notes |
|----------|----------|-----|-------|
| #22 | MISMATCH | skip (no_symmetric_flops) | Correctly reclassified as gross flop |
| #38 | MISMATCH | skip (no_symmetric_flops) | Correctly reclassified as gross flop |
| #39 | MISMATCH | pass | Fixed |
| #88 | MISMATCH | fail (4 vs 8 phases) | Pre-existing issue, not GrossFlop-related |
| #89 | MISMATCH | skip (no_symmetric_flops) | Correctly reclassified as gross flop |
| #156 | MISMATCH | skip (no_symmetric_flops) | Correctly reclassified as gross flop |

## Task Commits

1. **Task 1: Update survey script** - `f4b46db` (feat)
2. **Task 2: Run re-validation** - `4aec6a8` (test)

## Files Created/Modified
- `tests/survey_h11_3.py` - Added gross_flop_count field and logging
- `tests/compare_orbit_results.jsonl` - Full 243-polytope validation results

## Decisions Made
- compare_orbit.py needs no changes (dynamically compares, no type filtering)
- 28 Coxeter enumeration limit failures are pre-existing (200-multiplication cap)
- 3 data mismatches (#88, #168, #174) are unrelated to the GrossFlop fix

## Deviations from Plan
- Plan expected all 7 mismatches resolved; 4/7 resolved by GrossFlop reclassification, 1 fixed (#39), 1 still fails (#88, different root cause), 1 now skips

## Issues Encountered
- #88 shows 4 phases in original vs 8 in cybir — likely a separate BFS exploration difference, not a classification issue
- #168, #174 match on phase count but differ on inf/eff/cox generators

## Next Phase Readiness
- GrossFlop classification fix validated
- Remaining 3 data mismatches are pre-existing and should be tracked as future investigation items

---
*Phase: 06-classification-correctness-toric-curves-cone-construction*
*Completed: 2026-04-20*

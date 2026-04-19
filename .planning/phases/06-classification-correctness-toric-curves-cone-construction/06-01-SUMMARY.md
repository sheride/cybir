---
phase: 06-classification-correctness-toric-curves-cone-construction
plan: 01
subsystem: classification
tags: [gross-flop, coxeter-group, kahler-cone, classification-invariance]

# Dependency graph
requires:
  - phase: 05-pipeline-integration
    provides: BFS pipeline, symmetric flop detection, _accumulate_generators
provides:
  - GROSS_FLOP enum member with display names
  - CoxeterGroup frozen dataclass with order/rank/repr
  - toric_origin field on ExtremalContraction
  - _kahler_cones_match helper for condition (b) checking
  - GrossFlop post-check in BFS pipeline
  - Classification invariance warning system
affects: [06-02, 06-03, 06-04, 06-05, 06-06]

# Tech tracking
tech-stack:
  added: []
  patterns: [tuple-return for multi-condition classification checks]

key-files:
  created: []
  modified:
    - cybir/core/types.py
    - cybir/core/classify.py
    - cybir/core/build_gv.py
    - cybir/core/__init__.py
    - tests/test_types.py
    - tests/test_classify.py

key-decisions:
  - "is_symmetric_flop returns (bool, bool) tuple instead of bool for backward-compatible gross flop detection"
  - "GrossFlop post-check done in _run_bfs after classify_contraction, not inside classify_contraction itself, for minimal disruption"
  - "GROSS_FLOP excluded from _coxeter_refs and _sym_flop_refs/pairs -- treated like generic FLOP for accumulation"

patterns-established:
  - "Tuple return for multi-condition classification: (primary_result, secondary_flag)"
  - "Post-check pattern in BFS: classify first, then override based on cone geometry"

requirements-completed: []

# Metrics
duration: 15min
completed: 2026-04-19
---

# Phase 06 Plan 01: GROSS_FLOP Classification Fix and CoxeterGroup Dataclass

**GROSS_FLOP enum with Kahler cone condition (b) check, CoxeterGroup frozen dataclass, classification invariance warnings**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-19T22:00:16Z
- **Completed:** 2026-04-19T22:15:16Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added GROSS_FLOP classification that detects when condition (a) passes but Kahler cone check (b) fails (fixes 7/243 h11=3 misclassifications)
- CoxeterGroup frozen dataclass with order/rank properties and Unicode subscript repr
- toric_origin optional field on ExtremalContraction for future toric curve integration
- Classification invariance sanity check warns when curves get different types from different phases
- 80 tests passing across test_types.py and test_classify.py

## Task Commits

Each task was committed atomically:

1. **Task 1: GROSS_FLOP enum, CoxeterGroup dataclass, toric_origin field** - `8e75f71` (feat)
2. **Task 2: GrossFlop Kahler cone check + classification invariance** - `95a9e99` (feat)

## Files Created/Modified
- `cybir/core/types.py` - GROSS_FLOP enum, CoxeterGroup dataclass, toric_origin on ExtremalContraction
- `cybir/core/classify.py` - _kahler_cones_match helper, is_symmetric_flop returns tuple, GROSS_FLOP handling
- `cybir/core/build_gv.py` - GrossFlop post-check in BFS, classification invariance tracking, GROSS_FLOP accumulation
- `cybir/core/__init__.py` - CoxeterGroup export
- `tests/test_types.py` - Tests for GROSS_FLOP, CoxeterGroup, toric_origin (50 tests)
- `tests/test_classify.py` - Tests for _kahler_cones_match, tuple return, GROSS_FLOP accumulation (30 tests)

## Decisions Made
- is_symmetric_flop returns (bool, bool) tuple for backward compatibility -- callers that only checked truthiness now need to unpack
- GrossFlop post-check in _run_bfs rather than inside classify_contraction to minimize disruption to the classification pipeline
- GROSS_FLOP treated like generic FLOP for generator accumulation (no coxeter refs, no sym flop refs)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- GROSS_FLOP classification ready for use in toric curve integration (Plan 02+)
- CoxeterGroup dataclass ready for orbit expansion refactoring
- toric_origin field ready for toric curve provenance tracking

---
*Phase: 06-classification-correctness-toric-curves-cone-construction*
*Completed: 2026-04-19*

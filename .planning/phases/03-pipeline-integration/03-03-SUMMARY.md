---
phase: 03-pipeline-integration
plan: 03
subsystem: core
tags: [weyl-expansion, coxeter-reflection, einsum, symmetric-flop, re-exports]

# Dependency graph
requires:
  - phase: 03-pipeline-integration
    plan: 01
    provides: CYBirationalClass orchestrator, CYGraph API
  - phase: 03-pipeline-integration
    plan: 02
    provides: BFS builder (build_gv.py), patch.py
provides:
  - Weyl orbit expansion via expand_weyl(ekc)
  - Phase reflection with correct einsum transformation of intersection numbers
  - Mori cone deduplication for reflected phases
  - Package re-exports for CYBirationalClass and patch_cytools
affects: [03-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [mori-cone-signature-dedup, einsum-reflection-transform, inherited-contractions]

key-files:
  created: [cybir/core/weyl.py, tests/test_weyl.py]
  modified: [cybir/__init__.py, cybir/core/__init__.py]

key-decisions:
  - "Mori cone deduplication uses frozenset of integer-cast ray tuples for order-invariant comparison"
  - "Reflected phases get SYMMETRIC_FLOP contraction edges with zero flopping curve (placeholder)"
  - "Terminal wall contractions (asymptotic, CFT, su2) inherited as self-loops on reflected phases"

patterns-established:
  - "Mori signature dedup: frozenset of tuple-cast rays for O(1) membership testing"
  - "Reflection transform: einsum 'abc,xa,yb,zc' for int_nums, 'a,xa' for c2"

requirements-completed: [PIPE-02, INTG-03, INTG-04]

# Metrics
duration: 3min
completed: 2026-04-12
---

# Phase 03 Plan 03: Weyl Expansion and Package Re-exports Summary

**Weyl orbit expansion via symmetric-flop Coxeter reflections with einsum-transformed intersection numbers and full package re-exports**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-12T08:07:23Z
- **Completed:** 2026-04-12T08:10:28Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `cybir/core/weyl.py` with `expand_weyl` function that applies symmetric-flop reflections to fundamental-domain phases
- Reflection transforms intersection numbers via `np.einsum('abc,xa,yb,zc', ...)` and c2 via `np.einsum('a,xa', ...)`, matching the original `sym_flop_cy`
- Phase deduplication by Mori cone signature (frozenset of ray tuples) with defensive checks for degenerate cones
- Updated `cybir/__init__.py` and `cybir/core/__init__.py` to re-export `CYBirationalClass` and `patch_cytools`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Weyl expansion module with tests** - `174c850` (feat)
2. **Task 2: Update package re-exports** - `d736cc1` (feat)

## Files Created/Modified

- `cybir/core/weyl.py` - Weyl orbit expansion: expand_weyl, _reflect_phase, _is_new_phase, _inherit_contractions
- `tests/test_weyl.py` - 10 unit tests for _reflect_phase and _is_new_phase helpers
- `cybir/__init__.py` - Added CYBirationalClass and patch_cytools re-exports
- `cybir/core/__init__.py` - Added CYBirationalClass and patch_cytools re-exports

## Decisions Made

- Mori cone deduplication uses frozenset of integer-cast ray tuples for order-invariant comparison
- Reflected phases get SYMMETRIC_FLOP contraction edges linking them to the original fundamental-domain phase
- Terminal wall contractions (asymptotic, CFT, su2) are inherited as self-loops on reflected phases
- Reflection matrix dimension validated against h11 before applying (T-03-06 mitigation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full pipeline ready for end-to-end integration testing (03-04)
- `from cybir import CYBirationalClass, patch_cytools` available as public API
- All construction steps (setup_root -> construct_phases -> expand_weyl) wired through CYBirationalClass

---
*Phase: 03-pipeline-integration*
*Completed: 2026-04-12*

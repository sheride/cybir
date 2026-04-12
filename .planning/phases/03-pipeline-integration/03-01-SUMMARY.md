---
phase: 03-pipeline-integration
plan: 01
subsystem: core
tags: [graph, types, orchestrator, ekc, networkx]

# Dependency graph
requires:
  - phase: 02-core-math
    provides: CalabiYauLite, ExtremalContraction, CYGraph, util.coxeter_matrix
provides:
  - Graph-owned topology API (add_contraction with phase labels and curve signs)
  - contractions_from(label) returning (contraction, sign) tuples
  - phases_adjacent_to(contraction) returning phase pair
  - ExtremalContraction without start/end phase, with cone_face
  - CYBirationalClass orchestrator with read-only post-construction API
affects: [03-02, 03-03, 03-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [graph-owned-topology, builder-separation, lazy-imports, frozen-set-generators]

key-files:
  created: [cybir/core/ekc.py]
  modified: [cybir/core/graph.py, cybir/core/types.py, tests/test_graph.py, tests/test_types.py]

key-decisions:
  - "Graph owns topology: add_contraction takes (contraction, phase_a_label, phase_b_label) with curve signs stored on edge"
  - "ExtremalContraction is phase-agnostic: no start_phase/end_phase, only flopping curve and classification data"
  - "CYBirationalClass uses lazy imports for build_gv/weyl to avoid circular dependencies"
  - "Cone generators stored as sets of tuples for hashability"

patterns-established:
  - "Graph-owned topology: phase connectivity stored on graph edges, not contraction objects"
  - "Builder separation: CYBirationalClass delegates construction to external builder functions"
  - "Lazy builder imports: construction methods import builder modules at call time"

requirements-completed: [PIPE-03]

# Metrics
duration: 4min
completed: 2026-04-12
---

# Phase 03 Plan 01: Graph API and CYBirationalClass Summary

**Graph-owned topology API with signed curve orientations and CYBirationalClass orchestrator with 15 read-only properties**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-12T07:53:35Z
- **Completed:** 2026-04-12T07:57:20Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Moved topology ownership from ExtremalContraction to CYGraph: add_contraction now takes phase labels and curve signs as edge metadata
- Added contractions_from(label) and phases_adjacent_to(contraction) query methods to CYGraph
- Created CYBirationalClass orchestrator with step-by-step construction API (setup_root, construct_phases, expand_weyl) and from_gv classmethod
- 15 read-only properties on CYBirationalClass for post-construction querying

## Task Commits

Each task was committed atomically:

1. **Task 1: Update CYGraph API and ExtremalContraction** - `f8b2de1` (feat)
2. **Task 2: Create CYBirationalClass orchestrator** - `7d9b363` (feat)

## Files Created/Modified
- `cybir/core/ekc.py` - CYBirationalClass orchestrator with construction API and read-only properties
- `cybir/core/graph.py` - Updated CYGraph with graph-owned topology, contractions_from, phases_adjacent_to
- `cybir/core/types.py` - ExtremalContraction without start/end phase, with cone_face property
- `tests/test_graph.py` - Updated tests for new API, added tests for contractions_from and phases_adjacent_to
- `tests/test_types.py` - Updated to reflect removed start/end_phase and added cone_face

## Decisions Made
- Graph owns topology: curve signs stored as edge metadata (curve_sign_a, curve_sign_b) alongside a phase_a marker to distinguish orientations
- ExtremalContraction is now phase-agnostic: only holds intrinsic contraction data (curve, classification, GV data, cone_face)
- CYBirationalClass uses lazy imports for builder modules to prevent circular import chains
- Cone generators stored as sets of tuples (hashable) with frozenset properties for immutable external access

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CYGraph API ready for BFS builder (03-02) to use add_contraction with phase labels
- CYBirationalClass ready to receive setup_root and construct_phases implementations
- contractions_from method ready for wall iteration in BFS loop

---
*Phase: 03-pipeline-integration*
*Completed: 2026-04-12*

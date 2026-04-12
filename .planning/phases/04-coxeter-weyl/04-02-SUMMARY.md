---
phase: 04-coxeter-weyl
plan: 02
subsystem: math
tags: [coxeter, weyl, orbit-expansion, reflection, kahler-cone, index-conventions]

# Dependency graph
requires:
  - phase: 04-coxeter-weyl
    provides: coxeter.py with enumerate_coxeter_group, classify_coxeter_type, is_finite_type
  - phase: 03-pipeline
    provides: CYGraph, CalabiYauLite, ExtremalContraction, build_gv BFS pipeline
provides:
  - "reflect_phase_data: apply group element to phase with correct index conventions"
  - "apply_coxeter_orbit: full streaming BFS orbit expansion with phases=True/False modes"
  - "CYBirationalClass.apply_coxeter_orbit method with lazy import"
  - "coxeter_type and coxeter_order read-only properties on CYBirationalClass"
  - "expand_weyl deprecated, delegates to apply_coxeter_orbit"
affects: [04-03, invariants-for, to-fundamental-domain, ekc-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [streaming-orbit-expansion, proper-inverse-for-kahler, full-graph-orbit]

key-files:
  created: []
  modified: [cybir/core/coxeter.py, cybir/core/ekc.py, tests/test_coxeter.py]

key-decisions:
  - "Reflected contraction curves use g @ curve (Mori space), Kahler rays use ray @ inv(g)"
  - "No deduplication of reflected phases (D-11) -- each (g, fund_phase) pair is unique"
  - "Affine A_2 test uses permutation-matrix reflections in R^3 for proper infinite-type detection"

patterns-established:
  - "Index convention: g on Mori, inv(g) on Kahler, with integrality assertion (T-04-04)"
  - "Graph orbit: snapshot fundamental edges, reflect all (flops between pairs, terminal walls as self-loops)"
  - "Generator accumulation: Kahler rays -> eff_cone_gens, terminal curves -> infinity_cone_gens, zvd -> eff_cone_gens"

requirements-completed: [SC-1, SC-3, SC-4, SC-5, SC-6]

# Metrics
duration: 7min
completed: 2026-04-12
---

# Phase 4 Plan 2: Coxeter Orbit Expansion Summary

**Streaming BFS orbit expansion with correct Mori/Kahler index conventions (g vs inv(g)), full graph orbit reflecting flop edges and terminal walls, and phases=False generator-only mode**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-12T19:06:25Z
- **Completed:** 2026-04-12T19:13:00Z
- **Tasks:** 2 (Task 1: TDD RED+GREEN, Task 2: wiring)
- **Files modified:** 3

## Accomplishments
- Implemented reflect_phase_data with correct index conventions: g on Mori (einsum), inv(g) on Kahler (D-08/D-09)
- Implemented apply_coxeter_orbit with streaming BFS, phases=True/False modes, full graph orbit (D-10 through D-14)
- Wired apply_coxeter_orbit into CYBirationalClass with coxeter_type/coxeter_order properties
- Deprecated expand_weyl to delegate with DeprecationWarning
- 23 new tests covering all orbit expansion behavior, 372 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `c875409` (test)
2. **Task 1 (GREEN): Implementation** - `26d638d` (feat)
3. **Task 2: Wire into CYBirationalClass** - `ef53240` (feat)

## Files Created/Modified
- `cybir/core/coxeter.py` - Added reflect_phase_data, apply_coxeter_orbit, _edges_snapshot (3 new functions)
- `cybir/core/ekc.py` - Added apply_coxeter_orbit method, coxeter_type/coxeter_order properties, deprecated expand_weyl, updated __repr__
- `tests/test_coxeter.py` - Added TestReflectPhaseData (6 tests) and TestApplyCoxeterOrbit (12 tests)

## Decisions Made
- **Integrality assertion on g_inv:** Added `np.allclose` assertion after rounding inv(g) to integers, mitigating T-04-04 (float tampering risk)
- **Affine A_2 fixture:** Used permutation-matrix reflections in R^3 (swap pairs of basis vectors) to get proper infinite-type Coxeter group with all m_ij = 3
- **label_map for flop edges:** Used (g_key, fund_label) -> new_label mapping to efficiently connect reflected flop pairs during streaming BFS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed affine A_2 test reflections**
- **Found during:** Task 1 (TDD GREEN)
- **Issue:** Initial test reflections for infinite-type guard gave A_2 x A_1 (finite), not affine A_2 (infinite)
- **Fix:** Replaced with permutation-matrix reflections [[0,1,0],[1,0,0],[0,0,1]] etc. that have all pairwise orders = 3
- **Files modified:** tests/test_coxeter.py
- **Verification:** is_finite_type returns False, test passes
- **Committed in:** 26d638d

---

**Total deviations:** 1 auto-fixed (1 Rule 1 bug)
**Impact on plan:** Test fixture correction only. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- apply_coxeter_orbit complete, ready for Plan 03 (invariants_for, to_fundamental_domain, cleanup)
- All 372 tests passing
- Coxeter group construction + orbit expansion pipeline fully operational

---
*Phase: 04-coxeter-weyl*
*Completed: 2026-04-12*

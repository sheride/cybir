# Phase 2: Core Mathematics - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 02-core-mathematics
**Areas discussed:** Function organization, Correctness verification strategy, API surface, Equation citation depth

---

## Function Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Single `flop.py` | All math in one module (~500-800 lines) | |
| Split into submodules | `flop.py`, `classify.py`, `gv.py`, `coxeter.py` | |
| Two modules | `flop.py` + `gv.py` middle ground | |

**User's choice:** Split into submodules, but with modifications: rename `wall_crossing` to `flop`, rename `diagnosis` to `classify` (use "classify" terminology throughout instead of "diagnose"). Coxeter functions (only 2) go in `util.py` instead of a dedicated module.

**Notes:** User asked what was planned for `ekc.py` — confirmed it's the Phase 3 orchestrator (construct_phases BFS, Weyl expansion, post-construction API). Final split: `flop.py` (wall-crossing), `classify.py` (classification), `gv.py` (GV series/potent/nilpotent/nop), Coxeter in `util.py`.

---

## Correctness Verification Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| End-to-end only | Final outputs on a few polytopes | |
| Intermediate snapshots | Capture values at each stage | ✓ |
| Function-level gold files | Input/output pairs per function | |

**User's choice:** Intermediate snapshots for all 36 h11=2 polytopes.

**Notes:** None — straightforward decision.

---

## API Surface

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone functions | Pure functions, types as data | |
| Methods on types | Math as class methods | |
| Hybrid | Standalone + thin convenience methods | ✓ |

**User's choice:** Hybrid — standalone functions as real implementation, thin convenience methods on types that delegate. User confirmed this matches the original code's pattern and wants all math functions individually callable.

**Notes:** None.

---

## Equation Citation Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Equation number only | "Eq. 2.3 of arXiv:2212.10573" | |
| Equation + brief context | Number + 1-2 sentences physical context | |
| Equation + LaTeX | Number + context + actual LaTeX equation | ✓ |

**User's choice:** Full LaTeX equations in docstrings so they render in Sphinx docs.

**Notes:** None.

---

## Additional Discussion: Data Organization

User raised an important point not in the original gray areas: the original code has many implicit data organization choices (e.g., `start_cy`/`end_cy` on walls, `coxeter_refs` as set of tuples on EKC, phase keying by intersection number tuples). User wants ALL information preserved but is open to reorganization into better data structures.

**Decision:** Researcher should sweep the original EKC code, catalog all data storage patterns, and propose reorganizations before planning. Nothing silently dropped.

## Claude's Discretion

- Exact function signatures
- Test fixture format
- Specific data structure reorganization proposals (subject to: nothing dropped)

## Deferred Ideas

None — discussion stayed within phase scope.

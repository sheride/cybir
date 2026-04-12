# Phase 3: Pipeline & Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 03-pipeline-integration
**Areas discussed:** Data Organization, Pipeline Orchestrator Design, Weyl Expansion, CYTools Monkey-Patching, Documentation & Notebooks

---

## Data Organization

| Option | Description | Selected |
|--------|-------------|----------|
| start_cy/end_cy on contraction | Original pattern — Wall stores references to both adjacent CYs | |
| Graph encodes topology | Contraction drops phase refs, graph stores adjacency | ✓ |

**User's choice:** Graph encodes topology. ExtremalContraction drops start_phase/end_phase. CYGraph provides `phases_adjacent_to` and `contractions_from`.

**Additional decisions from discussion:**
- Monkey-patch Cone objects for geometric face data (user suggested)
- Drop Circuit/start_circuit/end_circuit entirely (toric is v2)
- Keep BFS tracking data on orchestrator (no harm, useful for debugging)
- Cone generators live on orchestrator, not graph
- Curves stored in canonical form; oriented per-phase via graph edge metadata
- User confirmed: `contractions_from(phase)` returns curves oriented inward to that phase's Kahler cone

---

## Pipeline Orchestrator Design

| Option | Description | Selected |
|--------|-------------|----------|
| Single class does everything | ExtendedKahlerCone owns graph, build state, and construction logic | |
| Result container + builder pattern | CYBirationalClass holds results; build_gv.py has construction logic | ✓ |

**User's choice:** Result container + builder pattern. Renamed to CYBirationalClass.

**Additional decisions:**
- User requested step-by-step API (init → setup_root → construct_phases → expand_weyl) to match original workflow where you inspect intermediate state
- Convenience classmethod `from_gv` wraps all steps
- Future `from_toric` classmethod for toric pipeline
- CYBirationalClass holds reference to CYTools CalabiYau (not pure data — needs it for on-demand GV computation)

---

## Weyl Expansion

| Option | Description | Selected |
|--------|-------------|----------|
| Interleaved with BFS | Expand as walls are discovered | |
| Separate step after BFS | construct_phases collects reflections, expand_weyl applies them | ✓ |

**User's choice:** Separate step. Independently testable. Can be called lazily.

---

## CYTools Monkey-Patching

| Option | Description | Selected |
|--------|-------------|----------|
| All four levels | Patch Invariants, Polytope, Triangulation, CalabiYau | |
| Three levels (skip Triangulation) | CalabiYau + Invariants + Polytope | ✓ |

**User's choice:** Three levels. Polytope convenience is simple (`self.triangulate().get_cy().birational_class()`). Skip Triangulation — no value. Explicit `cybir.patch_cytools()` activation.

---

## Documentation & Notebooks

| Option | Description | Selected |
|--------|-------------|----------|
| Build-time notebook execution | Notebooks run during Sphinx build | |
| Pre-executed notebooks | Regenerated periodically | ✓ |

**User's choice:** Pre-executed notebooks, regenerated from time to time. Two notebooks (h11=2 walkthrough, h11=3 complex). API reference from docstrings. No narrative docs for now.

---

## Claude's Discretion

- Builder module naming and internal structure
- Specific Invariants methods to patch
- Sphinx conf.py details
- BFS implementation details
- CYGraph API additions for orientation support

## Deferred Ideas

- Toric pipeline (v2)
- Circuit class (v2)
- Triangulation-level monkey-patch
- Serialization/caching
- Narrative documentation page

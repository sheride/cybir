# Requirements: cybir

**Defined:** 2026-04-11
**Core Value:** A clean, well-documented, modular implementation of GV-based EKC construction that is easy to use, extend, and understand

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Model

- [x] **DATA-01**: `CalabiYauLite` class for phase data (intersection numbers, c2, cones, charges) — own version, interface-compatible with dbrane-tools for future unification
- [x] **DATA-02**: `Contraction` class representing a birational contraction, holding a reference to the underlying cone face plus diagnosis metadata (type, flopping curve, linked phases, GV data)
- [x] **DATA-03**: `ContractionType` enum replacing string-based categories, with configurable display notation (Wilson vs 2212.10573 conventions)
- [x] **DATA-04**: `InsufficientGVError` exception for when GV series hasn't been computed to high enough degree
- [x] **DATA-05**: Phase adjacency graph as first-class object (phases as nodes, contractions as edges)
- [x] **DATA-06**: Immutable/frozen phase objects after construction

### Core Mathematics

- [ ] **MATH-01**: Wall-crossing formula for intersection numbers and second Chern class (Eq. from 2212.10573)
- [ ] **MATH-02**: Contraction diagnosis — all 5 types (asymptotic, CFT, su(2), symmetric flop, generic flop)
- [ ] **MATH-03**: GV series computation and effective GV
- [ ] **MATH-04**: Potent/nilpotent curve classification and nop identification
- [ ] **MATH-05**: Coxeter reflection computation
- [ ] **MATH-06**: Equation citations in every math function docstring

### Pipeline

- [ ] **PIPE-01**: `construct_phases` BFS loop with dictionary-keyed phase deduplication
- [ ] **PIPE-02**: Weyl orbit expansion for hyperextended cone
- [ ] **PIPE-03**: Clean read-only post-construction API (`ekc.phases`, `ekc.contractions`, `ekc.coxeter_matrix`, etc.)
- [ ] **PIPE-04**: Verbose logging replacing scattered print statements

### Integration

- [ ] **INTG-01**: CYTools Invariants monkey-patching (gv_series, gv_eff, ensure_nilpotency, flop_gvs)
- [x] **INTG-02**: Decouple from cornell-dev — copy/refactor `misc` and `lib.util.lattice` into cybir
- [ ] **INTG-03**: Monkey-patching at Polytope, Triangulation, CalabiYau levels
- [ ] **INTG-04**: Version guards on monkey-patches

### Package & Documentation

- [x] **PKG-01**: Proper Python package structure (`cybir/core/`, `cybir/phases/`, pyproject.toml with hatchling)
- [ ] **PKG-02**: Sphinx documentation with equation references to arXiv:2212.10573 and arXiv:2303.00757
- [ ] **PKG-03**: Example notebooks for h11=2,3

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Toric Pipeline

- **TORIC-01**: Toric EKC construction (`construct_phases_toric` pipeline) — needs qualitative rethinking
- **TORIC-02**: Toric GV computation methods

### Enhancements

- **ENH-01**: Serialization/caching of EKC results
- **ENH-02**: Tuned complex structure mode — use polytope data to perform GV computations at the tuned complex structure rather than assuming generic complex structure

## Out of Scope

| Feature | Reason |
|---------|--------|
| Toric pipeline | Needs qualitative rethinking, not just refactoring |
| Genus > 0 GV invariants | Beyond current algorithm scope |
| Non-toric-hypersurface CY3s | Beyond current algorithm scope |
| GUI / visualization | Not needed for research tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| DATA-05 | Phase 1 | Complete |
| DATA-06 | Phase 1 | Complete |
| MATH-01 | Phase 2 | Pending |
| MATH-02 | Phase 2 | Pending |
| MATH-03 | Phase 2 | Pending |
| MATH-04 | Phase 2 | Pending |
| MATH-05 | Phase 2 | Pending |
| MATH-06 | Phase 2 | Pending |
| PIPE-01 | Phase 3 | Pending |
| PIPE-02 | Phase 3 | Pending |
| PIPE-03 | Phase 3 | Pending |
| PIPE-04 | Phase 3 | Pending |
| INTG-01 | Phase 3 | Pending |
| INTG-02 | Phase 1 | Complete |
| INTG-03 | Phase 3 | Pending |
| INTG-04 | Phase 3 | Pending |
| PKG-01 | Phase 1 | Complete |
| PKG-02 | Phase 3 | Pending |
| PKG-03 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-04-11*
*Last updated: 2026-04-11 after roadmap creation*

# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-11
**Phase:** 01-foundation
**Areas discussed:** Package layout, Data type design, Cornell-dev audit, Test strategy

---

## Package Layout

| Option | Description | Selected |
|--------|-------------|----------|
| core/ + phases/ + patching/ | Three subdirectories, patches isolated | |
| Everything in core/ | All code in cybir/core/ for this milestone | ✓ |

**User's choice:** Everything in core/. User said "everything we're doing right now is core" and "I kind of like monkey patching functions near where the functions are defined" — no separate patching/ directory.

**Follow-up — module split:**

| Option | Description | Selected |
|--------|-------------|----------|
| types.py, flop.py, util.py, ekc.py | Four modules in core/ | ✓ |

**User's choice:** Approved. Also renamed wall_crossing.py → flop.py ("wall_crossing is a bit of an overloaded term — it all has to do with flopping").

---

## Data Type Design

**Phase class naming:** User wanted to match dbrane-tools CalabiYauLite pattern. Discussed through multiple iterations: Phase → CalabiYauLite (own version, interface-compatible with dbrane-tools).

**Wall/Contraction naming evolution:**
1. Started as "Wall" (from original code)
2. User flagged higher-codim faces as future concern
3. Considered monkeypatching Cone — decided against (too much domain-specific state)
4. User suggested "Contraction" + "ContractionType" following Wilson 1992
5. Briefly considered "FacetType" for the enum
6. Settled on ContractionType for enum
7. Class became ExtremalContraction (user's choice) to leave room for general Contraction later

**ContractionType notation:**

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed names | Single set of enum value names | |
| Configurable display | User chooses Wilson vs 2212.10573 convention | ✓ |

**User's choice:** Configurable display notation. User noted "different papers label the types differently."

**Immutability:**

| Option | Description | Selected |
|--------|-------------|----------|
| Always immutable | CalabiYauLite frozen after creation | |
| Mutable, EKC freezes | Mutable by default, orchestrator freezes after construction | ✓ |

**User's choice:** Mutable by default, frozen by EKC after construction. Confirmed this is EKC-specific, not a general CalabiYauLite property.

---

## Cornell-dev Audit

**GLSM charge matrix:**

| Option | Description | Selected |
|--------|-------------|----------|
| charge_matrix (flint) | From dbrane-tools, uses flint nullspace | |
| charge_matrix_hsnf | From dbrane-tools, uses Smith Normal Form | ✓ |

**User's choice:** hsnf version. Reason: "the flint version can sometimes generate linear relations which span linear relations over R but not Z, and we'd really like it to be over Z."

**lazy_cached:** User caught that this isn't used by EKC code ("why do we need lazy_cached? where is that ever used in EKC tech?"). Removed from the plan.

**Other dependencies:** moving_cone (port 5-line function), sympy_number_clean (rewrite one-liner), tuplify (rewrite), lib.util.lattice (drop).

---

## Test Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| h11=2 and h11=3 | Two test polytope families | |
| Just h11=2 | Minimal, fast iteration | ✓ |
| Specific polytopes | User-chosen | |

**User's choice:** Just h11=2 for now. Generate fixtures from original code.

---

## Claude's Discretion

- pyproject.toml configuration details
- Adjacency graph implementation choice
- Immutability mechanism
- Test fixture serialization format

## Deferred Ideas

- Tuned complex structure mode (ENH-02) — discuss during later implementation
- Higher-codimension contractions — future generalization
- Symbolic prepotential on CalabiYauLite — monkey-patch later if needed

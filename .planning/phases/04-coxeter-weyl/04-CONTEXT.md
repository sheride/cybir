# Phase 4: Coxeter Group & Weyl Expansion - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Rewrite the Weyl/orbit expansion machinery. Create `coxeter.py` combining Coxeter group construction (type classification, finite-type detection, streaming BFS enumeration) with the orbit expansion that replaces `weyl.py`. The expansion acts on all phase data with correct index conventions and accumulates generators from reflected phases. Only symmetric-flop reflections are used (not su(2)) — the result is the birational geometry, not the gauge-redundant SUSY moduli space.

</domain>

<decisions>
## Implementation Decisions

### Module Structure
- **D-01:** Delete `weyl.py`. Create `coxeter.py` that combines Coxeter group construction and orbit expansion in one module.
- **D-02:** Move `coxeter_reflection`, `coxeter_matrix` (the order-matrix version), and `matrix_period` from `util.py` into `coxeter.py`. Keep other util functions in place.

### Coxeter Group Construction
- **D-03:** Only symmetric-flop Coxeter matrices are used as generators. su(2) enhancement reflections are excluded — they give a gauge-redundant description of the SUSY moduli space, not the birational geometry.
- **D-04:** Compute the Coxeter order matrix m_ij = order(M_i M_j) from the concrete reflection matrices using `matrix_period`.
- **D-05:** Implement full finite-type classification from the Coxeter order matrix (A_n, B_n, D_n, E_6/7/8, F_4, G_2, H_3/4, I_2(m)). Compute |W| from closed-form formulas per type. This is wanted for the long term even though BFS dry-run would be simpler.
- **D-06:** Finite type detection via positive definiteness of the bilinear form B_ij = -cos(π/m_ij). Infinite type → stop and report fundamental domain only, do not attempt expansion.
- **D-07:** Memory estimation before enumeration: |W| × 8 × h11² bytes for the seen-set. Warn if estimate exceeds ~500MB. Use streaming BFS — act on phases as group elements are discovered, don't materialize the full group.

### Index Conventions
- **D-08:** The reflection matrices act on Mori-space objects (lowered indices). Explicitly: for a general group element g (product of reflections):
  - κ (intersection numbers): `einsum('abc,xa,yb,zc', κ, g, g, g)`
  - c2: `g @ c2`
  - Mori rays: `g @ ray` (column vector) or `ray @ g.T` (row vector)
  - Kahler rays: `ray @ np.linalg.inv(g)` or equivalently `(g^{-T}) @ ray` (column vector)
  - Zero-vol divisors: `g @ zvd` (same space as Mori/c2)
- **D-09:** For individual reflections M² = I so M⁻¹ = M, but for products g = M₁M₂⋯Mₖ, g⁻¹ = Mₖ⋯M₂M₁ ≠ g in general. Always use proper inverses.

### Orbit Expansion
- **D-10:** The method is called `apply_coxeter_orbit` (not `expand_weyl`).
- **D-11:** No deduplication of reflected phases — if the group is enumerated correctly, each (group element, fundamental phase) pair gives a unique reflected phase.
- **D-12:** The full graph is the Coxeter group orbit of the fundamental domain graph. All flop edges between fundamental-domain phases are reflected. Terminal walls become self-loops on reflected phases. Every phase connected by a flop in the fundamental domain has its reflected counterpart connected too.
- **D-13:** Support a `phases=False` mode that computes only eff/inf cone generators without creating phase objects. This applies group elements directly to the fundamental domain's generator sets:
  - `inf_cone_gens ∪= {g @ curve : g in W, curve in fund_inf_gens}`
  - `eff_cone_gens ∪= {Kahler rays of g-reflected phases} ∪ {g @ zvd : g in W, zvd in fund_eff_gens}`

### Generator Accumulation
- **D-14:** After orbit expansion, infinity cone gens and effective cone gens include contributions from ALL phases (fundamental + reflected). Reflected Kahler cone rays → eff_cone_gens. Reflected terminal wall curves → infinity_cone_gens. Reflected zero-vol divisors → eff_cone_gens.

### Per-Phase GV Invariants
- **D-15:** Don't store a separate Invariants object per phase. On-demand reconstruction: pick a point in the phase's Kahler cone, take the root GV object, re-orient all flop curves that pair negatively with that point. Expose as `ekc.invariants_for(phase_label)`.

### Fundamental Domain Mapping
- **D-16:** Implement `to_fundamental_domain(point)` — given a point in Kahler or Mori space, walk it back to the fundamental domain by repeatedly reflecting through walls that pair negatively. The symmetric-flop contraction curves define the walls of the fundamental domain.

### Claude's Discretion
- Internal BFS data structures (queue, seen-set representation)
- Hashing strategy for integer matrices in the seen-set
- How to decompose the Coxeter order matrix into irreducible components for type classification
- Test strategy for the Coxeter group enumeration (small known groups as fixtures)
- Whether `to_fundamental_domain` returns just the mapped point or also the group element that maps it

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Original Code
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah/extended_kahler_cone.py` — Original `sym_flop_cy` (line 268), `coxeter_matrix` (line 321), `matrix_period` (line 43), `get_coxeter_reflection` (line 203), Weyl orbit loop (lines 977-1035), post-BFS generator accumulation (lines 1038-1070)
- `/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/Elijah/misc.py` — `moving_cone` and other utilities

### cybir Code to Modify
- `cybir/core/weyl.py` — Current Weyl expansion (to be deleted, logic moves to coxeter.py)
- `cybir/core/util.py` — `coxeter_reflection`, `coxeter_matrix`, `matrix_period` (to move to coxeter.py)
- `cybir/core/ekc.py` — `CYBirationalClass` orchestrator (add `apply_coxeter_orbit`, `invariants_for`, `to_fundamental_domain`)
- `cybir/core/build_gv.py` — BFS builder (generator accumulation patterns to match in orbit expansion)

### Knowledge Base
- `/Users/elijahsheridan/Research/string/cytools_code/knowledge-base/protocols/execution.md` — Follow for any long computations (timing estimates, background execution, incremental saves)

### Mathematical References
- arXiv:2212.10573 Section 4.3 — Weyl orbit expansion algorithm, Coxeter group structure
- arXiv:2303.00757 Section 2 — EKC construction pipeline

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `util.coxeter_reflection(divisor, curve)` — Reflection matrix formula M_ab = δ_ab - 2 C_a D_b / (C·D). Moving to coxeter.py.
- `util.coxeter_matrix(reflections)` — Currently computes the Coxeter ELEMENT (product), needs renaming. The order-matrix version exists in the original code.
- `util.matrix_period(M)` — Exists in original (line 43). Computes order by repeated multiplication.
- `CYBirationalClass._sym_flop_refs` — Already stores only symmetric-flop reflections (not su(2)), so the correct subselection is in place.
- `tests/compare_bfs.py` — Integration test framework for comparing against original. Can be extended for orbit expansion.

### Established Patterns
- Generator accumulation via `_accumulate_generators` in build_gv.py — same pattern applies for reflected phases
- Raw (unnormalized) curve directions for generators
- `cone_incl_flop().extremal_rays()` for wall generation
- Streaming/on-the-fly processing (compare_bfs uses incremental JSONL saves)

### Integration Points
- `cybir/core/coxeter.py` — New module (replaces weyl.py)
- `cybir/core/ekc.py` — New methods: `apply_coxeter_orbit`, `invariants_for`, `to_fundamental_domain`
- `cybir/__init__.py` and `cybir/core/__init__.py` — Update re-exports (remove weyl, add coxeter)
- `tests/test_weyl.py` → `tests/test_coxeter.py` — Rename and expand

</code_context>

<specifics>
## Specific Ideas

- The Coxeter reflection M acts on Mori space (lowered indices); Mᵀ acts on Kahler space (raised indices). For products, use proper inverses: (g⁻¹)ᵀ on Kahler, g on Mori.
- `to_fundamental_domain` uses the classic chamber walk: repeatedly reflect through walls that pair negatively until point is in the fundamental chamber.
- `invariants_for(label)` reconstructs GVs on demand by checking which flop curves pair negatively with a tip point in the phase's Kahler cone, then flipping those.
- The `phases=False` mode for `apply_coxeter_orbit` is important: often the user wants the full cone structure without materializing hundreds of phase objects.

</specifics>

<deferred>
## Deferred Ideas

- Toric pipeline (`from_toric`, `build_toric.py`) — v2
- Infinite Coxeter group handling beyond "bail and report" — future work if needed
- Serialization/caching of full birational class results (ENH-01)
- Per-phase GV Invariants as stored objects (current design is on-demand reconstruction)
- `contraction_curve` rename was already done in Phase 3 bugfix commit

</deferred>

---

*Phase: 04-coxeter-weyl*
*Context gathered: 2026-04-12*

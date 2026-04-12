---
phase: 04-coxeter-weyl
reviewed: 2026-04-12T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - cybir/core/coxeter.py
  - cybir/core/ekc.py
  - cybir/core/types.py
  - cybir/core/build_gv.py
  - cybir/core/util.py
  - cybir/__init__.py
  - cybir/core/__init__.py
  - tests/test_coxeter.py
  - tests/test_build_gv.py
findings:
  critical: 0
  warning: 5
  info: 6
  total: 11
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

The phase 04 implementation adds Coxeter group enumeration, finite-type classification, orbit expansion (`apply_coxeter_orbit`), chamber walk (`to_fundamental_domain`), and on-demand GV reconstruction to the `cybir` package. The mathematical logic is well-structured and the docstrings are thorough. No security vulnerabilities or data-loss bugs were found. The findings below are logic errors, off-by-one conditions, and code quality issues that could cause incorrect results or silent failures in edge cases.

---

## Warnings

### WR-01: `to_fundamental_domain` has an off-by-one in the loop guard, making the `max_iter` check unreachable in the last iteration

**File:** `cybir/core/coxeter.py:944`

**Issue:** The outer `while` condition is `iters <= max_iter`, and the inner check at line 969 raises when `iters > max_iter`. This means the loop can execute one extra iteration past the intended limit before the inner check fires. The outer `while` guard is `<= max_iter`, so when `iters` reaches `max_iter` exactly the loop body runs again; the `if iters > max_iter` at line 969 never triggers inside that iteration because `iters` is incremented to `max_iter + 1` at line 968 and then checked at 969. The final `raise` at line 976 is also unreachable because the `while` exits when `iters == max_iter + 1` (false by `<=`), but by then the function has already returned from the `if not reflected` path if no reflection was needed. The actual safety property is intact only by coincidence; the bounds are confusingly written and the outer `raise` at line 976 is dead code.

**Fix:** Use a clean `for` loop with a single raise point:
```python
for _ in range(max_iter):
    reflected = False
    for i, c in enumerate(curves_arr):
        if point @ c < 0:
            M = reflections_int[i]
            g = (g @ M).astype(np.int64)
            point = M.astype(float) @ point
            reflected = True
            break
    if not reflected:
        return point, g
raise RuntimeError(
    f"to_fundamental_domain exceeded max_iter={max_iter}"
)
```
This removes the dead outer `raise` and makes the intent unambiguous.

---

### WR-02: `apply_coxeter_orbit` computes `g_inv_int` but never uses it when `phases=False`

**File:** `cybir/core/coxeter.py:805-825`

**Issue:** `g_inv_float` and `g_inv_int` are computed unconditionally at lines 805-806 for every non-identity group element, but `g_inv_int` is only consumed in the `if phases: ... if fund_phase.kahler_cone ...` branch at line 822. When `phases=False`, the Kahler ray reflection at line 822 is inside the same `if phases:` indentation—wait, it is NOT gated on `phases`; it is outside the `if phases:` block (line 810 closes at line 817, and line 820 starts a new `if fund_phase.kahler_cone` that is at the same level). So `g_inv_int` IS used for Kahler ray accumulation even in `phases=False` mode.

The real issue is that the `g_inv_int` integrality is NOT asserted here (unlike in `reflect_phase_data`). If a reflected group element has a non-integer inverse (which cannot happen for valid Coxeter groups, but could happen with corrupted input), the Kahler ray accumulation silently produces fractional cone generators that get silently truncated by `int(x)`.

**Fix:** Add a debug-level assertion consistent with `reflect_phase_data`:
```python
g_inv_float = np.linalg.inv(g.astype(float))
g_inv_int = np.round(g_inv_float).astype(int)
if not np.allclose(g_inv_float, g_inv_int):
    logger.warning("Non-integer g_inv encountered for group element; skipping")
    continue
```

---

### WR-03: `_classify_irreducible` misclassifies `B_n` when the weight-4 edge is NOT at the end of the chain

**File:** `cybir/core/coxeter.py:405-411`

**Issue:** The code checks for `B_n` (line 406-408) by testing `chain_weights[0] == 4 or chain_weights[-1] == 4`. For `F_4` the weight-4 edge is in the middle (position 1 of [3, 4, 3]), which is handled at lines 409-411. However, the condition `count_4 == 1 and count_3 == n - 2` at line 405 is evaluated before the end-position check. For `n=4` with chain weights `[3, 4, 3]`, `count_4 == 1` and `count_3 == 2`, so the condition at line 405 passes. The end-position test at line 407 fails (position 1 is not an end), so `F_4` falls through to line 409 correctly. The logic is therefore correct for `F_4`.

But for `n > 4` with a single weight-4 edge NOT at an end (a non-standard Coxeter graph that is not a named type), the code reaches line 409 and checks `n == 4`, which fails, so neither B nor F is returned—falling through to the `raise ValueError` at line 469. This is acceptable behavior (raise on unrecognized type) but the flow is non-obvious. The structural risk is: for `n=3` with a mid-chain weight-4 edge (pattern `[3, 4]` vs `[4, 3]`), both orderings are equivalent so `B_3` is handled correctly regardless. No actual misclassification, but the code relies on non-obvious path logic.

More concretely: for rank-2 groups, `n == 2` is caught first (line 357), so `_classify_irreducible` is never called with `n=2` from the chain code. However, there is one genuine bug: when `n == 2` and `m == 2` (the submatrix is `[[1,2],[2,1]]`), `_classify_irreducible` is called with `n=2`. The chain has no edges (both entries `m < 3`), so `n_edges == 0`, `is_chain` is `True`, and `len(endpoints)` is 0 (all degree-0 nodes). The `if len(endpoints) == 2` check at line 378 fails, so the chain-walk is skipped, and execution falls through to the branch-node check. No branch node exists, so `len(branch_nodes) != 1`. The function falls through to `raise ValueError`. But `A_1 x A_1` has `n=2`, and `_decompose_irreducible` will split it into two components of size 1 each (since the edge weight is 2, which is `< 3`). Each component is classified as `A_1` via the `n == 1` case at line 352. So `_classify_irreducible` is never actually called with the `[[1,2],[2,1]]` submatrix—the decomposition step handles it correctly. No actual bug, but worth confirming via a test.

**Fix:** Add an explicit guard for the `n == 2, m == 2` case even though it should not be reached, to make the code robust:
```python
if n == 2:
    m = int(submatrix[0, 1])
    if m <= 2:
        # Should not reach here if decomposition is correct
        raise ValueError(f"n=2 component with m={m} should have been split")
    ...
```

---

### WR-04: `_accumulate_generators` in `build_gv.py` tracks `ekc._sym_flop_curves` as an unordered parallel list to `ekc._sym_flop_refs` (a set), creating a potential index mismatch

**File:** `cybir/core/build_gv.py:115-128`

**Issue:** `ekc._sym_flop_refs` is a Python `set` (unordered). `ekc._sym_flop_curves` is a `list` appended to in the same function. The intention is that `_sym_flop_refs[i]` corresponds to `_sym_flop_curves[i]` for the chamber walk in `to_fundamental_domain` (see `ekc.py:177-178`). But because `_sym_flop_refs` is a `set`, iterating it gives an arbitrary order. When `CYBirationalClass.to_fundamental_domain` converts the set back to a list via `[np.array(r) for r in self._sym_flop_refs]`, the order will generally differ from the order curves were appended to `_sym_flop_curves`. This means the `(reflections[i], curves[i])` pairing in `to_fundamental_domain` is semantically wrong for any geometry with more than one symmetric-flop wall.

**Fix:** Store reflections and curves together as a list of pairs instead of separate collections:
```python
# In __init__:
self._sym_flop_ref_curve_pairs = []  # list of (ref_tuple, curve_tuple)

# In _accumulate_generators:
if ctype == ContractionType.SYMMETRIC_FLOP:
    ref_key = tuplify(np.round(cox_ref).astype(int))
    pair = (ref_key, tuple(int(x) for x in curve_arr))
    if pair not in self._sym_flop_ref_curve_pairs:
        self._sym_flop_ref_curve_pairs.append(pair)

# In to_fundamental_domain:
reflections = [np.array(r) for r, _ in self._sym_flop_ref_curve_pairs]
curves = [np.array(c) for _, c in self._sym_flop_ref_curve_pairs]
```

---

### WR-05: `coxeter_reflection` uses `float` arithmetic for the output matrix, which is then stored in `ekc._coxeter_refs` as rounded integers — but the rounding may be wrong for divisors with large entries

**File:** `cybir/core/coxeter.py:116-122`

**Issue:** The reflection formula `np.eye(h11) - 2.0 * np.outer(curve, divisor) / dot` is computed in float64. For integer inputs, the result is always rational. When the caller in `build_gv.py` stores the result via `tuplify(np.round(cox_ref).astype(int))`, a float64 rounding step is introduced. For entries of the form `2 * curve[i] * divisor[j] / dot`, float64 has 15-16 significant digits, which is sufficient for small values. However, if `dot` does not divide `2 * curve[i] * divisor[j]` exactly, the rounded integer may be wrong. The classify module is responsible for computing `cox_ref`, and if it uses the same float path, this is a latent precision issue. The `matrix_period` function correctly uses int64, but it receives matrices that may have been rounded from float.

This is a lower-severity precision issue that would only manifest for unusual inputs, but given the project's stated requirement for "bit-for-bit equivalence" and the use of int64 in `matrix_period`, the reflection construction should also be done in exact integer arithmetic.

**Fix:** Verify that `dot` exactly divides `2 * outer(curve, divisor)` before rounding, or refactor to use exact integer arithmetic:
```python
def coxeter_reflection(divisor, curve):
    divisor = np.asarray(divisor, dtype=int)
    curve = np.asarray(curve, dtype=int)
    h11 = len(curve)
    dot = int(curve @ divisor)
    if dot == 0:
        return np.eye(h11, dtype=int)
    outer = np.outer(curve, divisor)
    # 2 * outer must be divisible by dot for exact integer result
    numerator = 2 * outer
    assert np.all(numerator % dot == 0), (
        f"Reflection matrix has non-integer entries: dot={dot}"
    )
    return np.eye(h11, dtype=int) - numerator // dot
```

---

## Info

### IN-01: Unused variable `sign_a` in `apply_coxeter_orbit`

**File:** `cybir/core/coxeter.py:831`

**Issue:** `sign_a = data.get("curve_sign_a", 1)` is assigned but never referenced thereafter. The actual `curve_sign_a` values are retrieved again inline from `data.get(...)` at lines 858 and 870.

**Fix:** Remove the assignment at line 831.

---

### IN-02: `curve_tuple` variable in `_accumulate_generators` is computed but never used

**File:** `cybir/core/build_gv.py:93`

**Issue:** `curve_tuple = tuple(result.get("gv_series", []))` is assigned at line 93 with the comment `# not used for gens`. The variable is never referenced again in the function.

**Fix:** Remove line 93.

---

### IN-03: `construct_phases` calls `logging.basicConfig` unconditionally when `verbose=True`

**File:** `cybir/core/build_gv.py:262`

**Issue:** `logging.basicConfig(level=logging.INFO, format="%(message)s")` configures the root logger globally. In a library, calling `basicConfig` is an anti-pattern: it silently overwrites any logging configuration the caller has already set up (because `basicConfig` is a no-op if handlers are already configured, but this is a footgun if the user hasn't configured logging yet). The project uses a named `cybir` logger throughout, so `basicConfig` is irrelevant to that logger. The docstring says `verbose=True` enables "info-level logging" but does not mention reconfiguring the root logger.

**Fix:** Remove the `basicConfig` call. Users who want to see logs should configure the `cybir` logger themselves. Optionally, document this in the module docstring.

---

### IN-04: `_edges_snapshot` in `coxeter.py` accesses the private `_graph` attribute of `CYGraph` directly

**File:** `cybir/core/coxeter.py:564`

**Issue:** `return list(graph._graph.edges(data=True))` accesses `CYGraph._graph` directly, bypassing any public API. This creates a coupling to the internal implementation of `CYGraph`. If `CYGraph`'s internal representation changes, `_edges_snapshot` silently breaks.

**Fix:** Add a public method to `CYGraph` (e.g., `edges_with_data()`) and call that instead, or verify the existing public API covers this use case.

---

### IN-05: `util.py` deprecated re-export of `coxeter_matrix` has a misleading warning message

**File:** `cybir/core/util.py:310`

**Issue:** The deprecation warning says "coxeter_matrix moved to cybir.core.coxeter, renamed to coxeter_element", but the deprecated wrapper in `util.py` calls `coxeter_element` internally (line 313). The message is accurate. However, `cybir/__init__.py` and `cybir/core/__init__.py` both export `coxeter_matrix` from `cybir.core.coxeter` (which is itself a deprecated alias for `coxeter_element`). So there are now two deprecated layers: `util.coxeter_matrix -> coxeter.coxeter_matrix -> coxeter_element`. A user calling `from cybir import coxeter_matrix` gets `coxeter.coxeter_matrix`, which emits one deprecation warning. A user calling `from cybir.core.util import coxeter_matrix` gets two warning hops with slightly different messages.

**Fix:** Either remove `coxeter_matrix` from `__init__.py` exports (breaking API), or ensure both deprecated wrappers point to the same target and emit the same message.

---

### IN-06: `_invariants_for_impl` silently returns root invariants when `curve_signs` is `None` for Weyl-expanded phases

**File:** `cybir/core/coxeter.py:1021-1022`

**Issue:** Weyl-expanded phases (created by `reflect_phase_data`) are constructed without `curve_signs` or `tip` fields (lines 711-717 of `coxeter.py` do not pass them). When `invariants_for` is called for a Weyl-expanded phase, `target_phase.curve_signs` will be `None`, and the function returns root invariants unchanged. This is silently wrong for phases that are not in the same GV orientation as the root. The function has no warning or documentation that it does not support Weyl-expanded phases.

**Fix:** Add a logger warning when `target_signs` is `None` and the requested phase is a Weyl-expanded phase (i.e., its label is in `ekc._weyl_phases`):
```python
if target_signs is None:
    if phase_label in getattr(ekc, "_weyl_phases", []):
        logger.warning(
            "invariants_for: phase %s is Weyl-expanded and has no "
            "curve_signs; returning root invariants (may be incorrect)",
            phase_label,
        )
    return root_invariants
```

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

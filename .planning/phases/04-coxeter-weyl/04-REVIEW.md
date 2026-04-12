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
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 04: Code Review Report (Re-review after gap-closure plan 04-04)

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

This is a re-review after gap-closure plan 04-04 addressed WR-04 (sym_flop_pairs) and SC-4 (reflected phase curve_signs). Both fixes are correct: the reflection–curve pairing mismatch is eliminated and reflected-phase tips are computed with the right dual-space transformation. No new critical issues were introduced.

Three previous warnings remain open (WR-01, WR-02, WR-05). WR-03 remains open at info severity (no actual misclassification found, but non-obvious flow). A new warning (WR-05, renumbered below) was raised in the previous review and remains unaddressed. The previous info items IN-01 through IN-06 are unchanged.

---

## Resolved Issues

### RESOLVED: WR-04 — sym_flop_pairs pairing mismatch

**Status:** Fixed correctly.

`ekc._sym_flop_pairs` is now a `list` of `(ref_tuple, curve_tuple)` pairs appended in `_accumulate_generators` (`build_gv.py:128`). Deduplication is still performed via `ref_key not in ekc._sym_flop_refs` (line 120), which keeps the set as a guard but makes `_sym_flop_pairs` the authoritative ordered structure. Both `to_fundamental_domain` (`ekc.py:177-178`) and `apply_coxeter_orbit` (`coxeter.py:759`) unpack the list as `[np.array(r) for r, _ in ekc._sym_flop_pairs]` and `[np.array(c) for _, c in ekc._sym_flop_pairs]`, guaranteeing the correspondence is preserved.

### RESOLVED: SC-4 — reflected phase curve_signs missing

**Status:** Fixed correctly.

`apply_coxeter_orbit` now computes `reflected_tip = g_inv_int.T @ fund_phase.tip` (`coxeter.py:818`) and populates `new_phase._curve_signs` from that tip (`coxeter.py:824-827`). The transformation `g_inv^T @ tip` is correct: Mori-space vectors transform as `v -> g @ v`, so the Kahler dual transforms as `J -> g_inv^T @ J` (row-vector dual). This is consistent with D-08 and the Kahler-ray transformation `old_rays @ g_inv_int` on line 837.

One minor concern: the `curve_signs` dict is keyed on `root_phase.curve_signs` (line 823), which only contains curves known at the end of BFS. Weyl-expanded phases in more distant chambers may pair with curves not present in the root's curve_signs, so `_invariants_for_impl` may still return incomplete results for deeply reflected phases. This is an inherent limitation of using the root's curve set as the canonical key set, and it matches the documented limitation in IN-06 below. Not a regression; the previous behavior (no curve_signs at all) was strictly worse.

---

## Warnings

### WR-01: `to_fundamental_domain` — off-by-one in loop guard, outer `raise` is dead code

**File:** `cybir/core/coxeter.py:959-991`

**Issue:** The outer `while iters <= max_iter` condition allows up to `max_iter + 1` total reflections before the loop exits. Inside the loop body, `iters` is incremented to `max_iter + 1` at line 983, then checked by `if iters > max_iter` at line 984 — which fires correctly and raises. So the safety bound is actually enforced. However, the final `raise RuntimeError` at lines 991-992 is unreachable: the `while` condition is `False` when `iters == max_iter + 1`, so execution never falls through to line 991 from a non-reflected iteration (which would have returned at line 990). The outer `raise` was the intended final safety net, but the `while` condition makes it dead code. This is not a correctness bug but is a maintenance hazard: a reader may remove the `if iters > max_iter` inner check thinking the outer `raise` covers it, which would allow one extra reflection beyond the limit.

**Fix:** Replace with a `for`-loop pattern that has a single, unambiguous exit:
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

---

### WR-02: `apply_coxeter_orbit` does not validate integrality of `g_inv_int`

**File:** `cybir/core/coxeter.py:805-806`

**Issue:** `g_inv_int = np.round(g_inv_float).astype(int)` is computed at line 806 but there is no assertion that `g_inv_float` is close to `g_inv_int`. By contrast, `reflect_phase_data` at line 687 does assert this. For valid finite Coxeter groups the inverse is always integral, but corrupt or non-integer reflection matrices passed from `_sym_flop_pairs` would silently produce fractional ray accumulation, where the `int(x)` cast at line 839 would silently truncate to wrong integers.

**Fix:** Add a guard consistent with `reflect_phase_data`:
```python
g_inv_float = np.linalg.inv(g.astype(float))
g_inv_int = np.round(g_inv_float).astype(int)
if not np.allclose(g_inv_float, g_inv_int, atol=1e-9):
    logger.warning(
        "Non-integer g_inv for group element; skipping this element"
    )
    continue
```

---

### WR-03: `_classify_irreducible` — non-obvious flow for rank-2 `m=2` component

**File:** `cybir/core/coxeter.py:356-368`

**Issue:** When `_classify_irreducible` is called with a rank-2 submatrix where `m_01 == 2`, the code enters the `n == 2` branch at line 357, reads `m = int(submatrix[0, 1])` as `2`, and falls through the `if m == 3 / 4 / 6 / 5` ladder to `return ("I", 2, 2 * m)` at line 367, which returns `("I", 2, 4)`. This is incorrect: `I_2(2)` is not a standard finite Coxeter group — it is the degenerate case where the two generators commute, which should have been split into two `A_1` components by `_decompose_irreducible`. In practice, `_decompose_irreducible` does split components correctly (edges only added when `m >= 3`, line 299), so a rank-2 component with `m == 2` will never reach `_classify_irreducible`. However, if `_classify_irreducible` is called directly with such a matrix (e.g., in tests or future code), it silently returns `("I", 2, 4)` instead of raising. This is a latent incorrect-result path.

**Fix:** Add an explicit guard at the top of the `n == 2` branch:
```python
if n == 2:
    m = int(submatrix[0, 1])
    if m <= 2:
        raise ValueError(
            f"Rank-2 Coxeter component with m={m} should have been "
            "split by _decompose_irreducible; call classify_coxeter_type "
            "instead of _classify_irreducible directly."
        )
    ...
```

---

### WR-04 (previously WR-05): `coxeter_reflection` uses float arithmetic — potential rounding error for large divisor entries

**File:** `cybir/core/coxeter.py:116-122`

**Issue:** `np.eye(h11) - 2.0 * np.outer(curve, divisor) / dot` is computed in float64. For integer inputs the result is always rational with denominator `dot`. When `dot` does not exactly divide some entry of `2 * outer(curve, divisor)`, the float64 representation introduces rounding error that is then silently rounded again by `tuplify(np.round(cox_ref).astype(int))` in `build_gv.py:112`. For small `dot` values (typical for CY3 geometries) this is harmless, but for large-entry divisors the accumulated error in the reflection chain (used by `matrix_period` in int64) could give a wrong period and therefore a wrong Coxeter type. This is inconsistent with the stated int64 arithmetic policy in `matrix_period`.

**Fix:** Compute the reflection in exact integer arithmetic:
```python
def coxeter_reflection(divisor, curve):
    divisor = np.asarray(divisor, dtype=int)
    curve = np.asarray(curve, dtype=int)
    h11 = len(curve)
    dot = int(curve @ divisor)
    if dot == 0:
        return np.eye(h11, dtype=int)
    numerator = 2 * np.outer(curve, divisor)
    if np.any(numerator % dot != 0):
        raise ValueError(
            f"Reflection matrix has non-integer entries: dot={dot}, "
            f"2*outer not divisible by dot"
        )
    return np.eye(h11, dtype=int) - numerator // dot
```

---

## Info

### IN-01: Unused variable `sign_a` in `apply_coxeter_orbit`

**File:** `cybir/core/coxeter.py:845`

**Issue:** `sign_a = data.get("curve_sign_a", 1)` is assigned but `sign_a` is never referenced again. The actual value is retrieved inline from `data.get(...)` at lines 873 and 885.

**Fix:** Remove line 845.

---

### IN-02: Unused variable `curve_tuple` in `_accumulate_generators`

**File:** `cybir/core/build_gv.py:93`

**Issue:** `curve_tuple = tuple(result.get("gv_series", []))  # not used for gens` is assigned and never used. Line 126 re-uses the name `curve_tuple` in the inner scope for a different purpose.

**Fix:** Remove line 93.

---

### IN-03: `construct_phases` calls `logging.basicConfig` unconditionally

**File:** `cybir/core/build_gv.py:263`

**Issue:** `logging.basicConfig(level=logging.INFO, format="%(message)s")` reconfigures the root logger when `verbose=True`. As a library, cybir should not touch the root logger. The project uses the named `cybir` logger throughout; `basicConfig` is irrelevant to it and will silently interfere with the caller's logging configuration if no handlers have been attached yet.

**Fix:** Remove the `basicConfig` call. Users who want log output should configure the `cybir` logger directly.

---

### IN-04: `_edges_snapshot` accesses `CYGraph._graph` private attribute

**File:** `cybir/core/coxeter.py:564`

**Issue:** `return list(graph._graph.edges(data=True))` reaches into the private networkx graph inside `CYGraph`. If `CYGraph`'s internal storage changes, `_edges_snapshot` silently breaks.

**Fix:** Add a public `edges_with_data()` method to `CYGraph` and call it here.

---

### IN-05: Two-layer deprecated path for `coxeter_matrix`

**File:** `cybir/core/util.py:306-313`, `cybir/__init__.py:29`

**Issue:** `cybir/__init__.py` exports `coxeter_matrix` from `cybir.core.coxeter`, which is itself a deprecated alias for `coxeter_element`. `cybir.core.util.coxeter_matrix` is a separate deprecated wrapper that delegates to `coxeter_element` with a slightly different warning text. A user importing `from cybir import coxeter_matrix` gets one warning (from `coxeter.coxeter_matrix`); a user importing `from cybir.core.util import coxeter_matrix` gets two warnings with different messages.

**Fix:** Either remove `coxeter_matrix` from `__init__.py` exports or ensure both deprecated paths emit the same message and chain to the same target unambiguously.

---

### IN-06: `_invariants_for_impl` silently returns root invariants for phases with `curve_signs=None`

**File:** `cybir/core/coxeter.py:1036-1043`

**Issue:** The SC-4 fix populates `curve_signs` for reflected phases only when `fund_phase.tip is not None`. If the fundamental-domain phase has no tip (e.g., because it was created before D-15 tip persistence), Weyl-expanded phases will still have `curve_signs=None`. The function now logs a warning in this case (lines 1037-1043), which is correct. The warning path is now reachable and working. No additional fix needed; logging the warning is the right behavior.

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

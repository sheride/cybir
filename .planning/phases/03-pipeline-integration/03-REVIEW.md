---
phase: 03-pipeline-integration
reviewed: 2026-04-12T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - cybir/__init__.py
  - cybir/core/__init__.py
  - cybir/core/build_gv.py
  - cybir/core/classify.py
  - cybir/core/ekc.py
  - cybir/core/flop.py
  - cybir/core/graph.py
  - cybir/core/gv.py
  - cybir/core/patch.py
  - cybir/core/types.py
  - cybir/core/util.py
  - cybir/core/weyl.py
  - tests/test_build_gv.py
  - tests/test_classify.py
  - tests/test_graph.py
  - tests/test_gv.py
  - tests/test_integration.py
  - tests/test_types.py
  - tests/test_util.py
  - tests/test_weyl.py
findings:
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 18 (source) + 2 not in files list (tests/conftest.py read for context)
**Status:** issues_found

## Summary

Reviewed the full Phase 3 pipeline integration: BFS construction (`build_gv.py`), contraction classification (`classify.py`), flop machinery (`flop.py`), graph layer (`graph.py`), GV utilities (`gv.py`), CYTools monkey-patching (`patch.py`), core data types (`types.py`), utility functions (`util.py`), Weyl expansion (`weyl.py`), and the orchestrator (`ekc.py`). Test coverage is thorough for the pure-Python units; integration tests skip gracefully when fixtures are absent.

The code is mathematically careful and well-structured. No security vulnerabilities or data-loss risks were found. The issues below are correctness/logic bugs, fragile edge-case handling, and code-quality items that could cause silent wrong results or cryptic failures.

---

## Warnings

### WR-01: `setup_root` duplicates tip-computation logic instead of calling `_compute_tip`

**File:** `cybir/core/build_gv.py:210-218`
**Issue:** `setup_root` contains an inline retry loop that is almost identical to `_compute_tip` (defined at line 32). The inline copy uses `tip = tip / c` whereas `_compute_tip` uses `return tip / c` — functionally the same — but the inline version silently leaves `tip = None` if all 20 retries fail, rather than raising `RuntimeError`. The result is that `root.kahler_cone` tip can be `None` and `construct_phases` would later crash with an undiagnostic `AttributeError` or `TypeError` rather than the intended `RuntimeError`.
**Fix:**
```python
# In setup_root, replace the inline retry loop (lines 210-218) with:
root_tip = _compute_tip(root)  # raises RuntimeError on failure
```
Note that `root` must be created before this call, so the `CalabiYauLite` instantiation at line 221 should come first — or pass `kahler_cone` directly and call `_compute_tip` after creation. The simplest fix is to keep the `CalabiYauLite` creation, then call `_compute_tip(root)` if the result is needed, or accept that `setup_root` computes the tip only for logging and doesn't store it (since `construct_phases` recomputes it anyway at line 275).


### WR-02: `_invariants_ensure_nilpotency`: integer division by zero when grading dot is zero

**File:** `cybir/core/patch.py:245-247`
**Issue:** `n_orig` is computed as:
```python
n_orig = int(self.cutoff // (
    flop_sign_correction * (self.precompose @ curve) @ self.grading_vec
))
```
If `(self.precompose @ curve) @ self.grading_vec` equals zero (i.e., the curve has zero grading), this is integer division by zero — Python raises `ZeroDivisionError` at runtime with no explanatory message. The CYTools grading vector is normally chosen so this cannot be zero for Mori cone generators, but this is an implicit precondition with no guard.
**Fix:**
```python
denom = flop_sign_correction * float((self.precompose @ curve) @ self.grading_vec)
if denom == 0:
    raise ValueError(
        f"Curve {curve} has zero grading; cannot compute nilpotency degree"
    )
n_orig = int(self.cutoff // denom)
```


### WR-03: `_invariants_ensure_nilpotency`: loop bound checks `n <= quit_length` but loop runs while `n + n_orig <= quit_length`

**File:** `cybir/core/patch.py:262`
**Issue:** The while loop condition is `while last != 0 and (n + n_orig) <= quit_length`, meaning the loop exits when `n + n_orig > quit_length`. After the loop, the assertion at line 290 checks `if n <= quit_length`, which is the wrong variable — `n` counts increments above `n_orig`, not the absolute degree. If `n_orig` is large and the loop never entered (because `n_orig > quit_length` already), `last != 0` could still be true, and the assertion fires incorrectly or the function returns a potent `gvs` object without warning.

More concretely: if `n_orig > quit_length` from the start, `last != 0` (non-zero last entry), and the while-loop body never executes (`n` stays 0). The assertion `if n <= quit_length` is True (0 <= quit_length), asserts `last is not None`, then returns `gvs` — but `gvs = self` (line 113: `obj = self`) so the method returns `self` unmodified with a non-zero last entry. The caller in `gv_series_cybir` then silently uses a potent series.
**Fix:** Clarify the exit condition and add an explicit check:
```python
if last != 0:
    from .types import InsufficientGVError
    raise InsufficientGVError(
        f"GV series for curve {curve} did not terminate within "
        f"quit_length={quit_length} degree increments"
    )
return gvs
```


### WR-04: `construct_phases` sets `flopped._kahler_cone` and `flopped._mori_cone` directly on a `CalabiYauLite` — bypasses freeze guard silently

**File:** `cybir/core/build_gv.py:389-390`
**Issue:** `flop_phase` creates a `CalabiYauLite` with `kahler_cone=None` and `mori_cone=None`. `construct_phases` then sets `flopped._kahler_cone` and `flopped._mori_cone` by direct private-attribute assignment. This works because `CalabiYauLite` is not yet frozen at that point, but it bypasses the intended public interface: the correct pattern would be to pass cones at construction time (or add a `set_cones` method). If `freeze()` were called earlier in the pipeline (e.g., right after `flop_phase` returns), this assignment would silently be blocked and the phase would have `None` cones — a latent ordering-dependency bug.

Additionally, `flopped._kahler_cone = flopped_mori.dual()` assigns the Kahler cone as the *dual of the Mori cone*, which is correct, but the assignment order is reversed from what the names suggest: line 389 assigns to `_kahler_cone` the result of `flopped_mori.dual()`, and line 390 assigns `_mori_cone = flopped_mori`. This is correct, but it means the object is temporarily in an inconsistent state (kahler_cone set, mori_cone not yet) between lines 389 and 390.
**Fix:** Pass the cones at construction time or add a `set_cones(kahler_cone, mori_cone)` method to `CalabiYauLite` that raises if frozen. The cleaner approach:
```python
flopped = CalabiYauLite(
    int_nums=flopped.int_nums,
    c2=flopped.c2,
    kahler_cone=flopped_mori.dual(),
    mori_cone=flopped_mori,
    label=new_label,
)
```


### WR-05: `graph.py` uses an undirected `nx.Graph` — parallel self-loops are silently dropped

**File:** `cybir/core/graph.py:35`
**Issue:** `networkx.Graph` does not support multiple edges between the same pair of nodes. In `construct_phases`, terminal walls (asymptotic, CFT, su(2), symmetric flop) all call `ekc._graph.add_contraction(contraction, source_label, source_label)` — a self-loop. If a phase has two walls of the same type, the second call to `add_edge(source_label, source_label, ...)` silently overwrites the first edge's data. This means the second terminal contraction is lost from the graph.

For a CY3 with two asymptotic walls from the same phase, the graph would store only one, producing incorrect EKC structure. The `contractions` property and `contractions_from` would silently return fewer contractions than expected.
**Fix:** Replace `nx.Graph` with `nx.MultiGraph` (supports parallel edges and self-loops):
```python
self._graph = nx.MultiGraph()
```
Note: `nx.MultiGraph` returns edge keys from `add_edge`; `edges(data=True)` returns `(u, v, key, data)` tuples. Update `contractions`, `contractions_from`, and `phases_adjacent_to` accordingly.


### WR-06: `zero_vol_divisor` returns `result.astype(float)` but callers treat it as integer

**File:** `cybir/core/classify.py:169`
**Issue:** `zero_vol_divisor` ends with `return result.astype(float)` after asserting all entries are near-integer. Callers in `_accumulate_generators` (build_gv.py:104) do `np.round(zvd).astype(int).tolist()` before adding to a set, which works. But `classify_contraction` passes `zero_vol_div` (float dtype) to `coxeter_reflection` (util.py), and `coxeter_reflection` is documented to return a matrix for integer divisor/curve — this is fine mathematically but inconsistent with the function's contract. More importantly, if any downstream consumer stores `zero_vol_divisor` expecting an integer array (e.g., for lattice computations), the float dtype silently introduces numerical error when used as an integer key. The `assert np.allclose(result, np.round(result))` on line 160 confirms the values are integers, so they should be returned as `int`.
**Fix:**
```python
return result  # already int from line 161: result = np.round(result).astype(int)
# Delete the final .astype(float) cast on line 169
```


### WR-07: `_invariants_gv_incl_flop` mutates the `curve` local variable inside the for-loop, so multiple aligned flop curves each flip the sign

**File:** `cybir/core/patch.py:155-157`
**Issue:** The sign-flip loop:
```python
for flop_curve in self.flop_curves:
    if _is_aligned(curve, flop_curve):
        curve = -curve
```
If `self.flop_curves` contains two curves aligned with `curve` (which should not happen in practice, but could happen if the same curve is flopped twice), the sign would be flipped twice and the result would be wrong. More importantly, the mutation of `curve` inside the loop means the `_is_aligned` check for the *next* flop_curve uses the negated curve — in principle a flop curve that was not aligned with the original `curve` might be aligned with `-curve`, causing an extra flip. This is a subtle correctness issue that the original code apparently avoids by ensuring each curve appears at most once in `flop_curves`, but there is no guard.

The faithful translation of the original should flip at most once. The original code (lines 2675-2677) does `break` after the first flip — this implementation lacks that.
**Fix:**
```python
for flop_curve in self.flop_curves:
    if _is_aligned(curve, flop_curve):
        curve = -curve
        break  # flip at most once
```

---

## Info

### IN-01: `coxeter_matrix` docstring says "Returns a 0-d identity-like array if the list is empty" but raises `ValueError`

**File:** `cybir/core/util.py:376`
**Issue:** The docstring says "Returns a 0-d identity-like array if the list is empty" but the implementation raises `ValueError("Cannot compute Coxeter matrix from empty list of reflections")`. The docstring is incorrect. The test in `test_util.py:352` correctly asserts `ValueError`, so the implementation is right — only the docstring is wrong.
**Fix:** Remove the incorrect sentence from the docstring:
```python
"""Compute the Coxeter element from a list of reflection matrices.
...
Returns
-------
numpy.ndarray
    The Coxeter matrix (product of all reflections).

Raises
------
ValueError
    If *reflections* is empty.
"""
```


### IN-02: `_accumulate_generators` computes `curve_tuple` but never uses it

**File:** `cybir/core/build_gv.py:93`
**Issue:** `curve_tuple = tuple(result.get("gv_series", []))` is assigned but never referenced. This appears to be a leftover from an earlier draft.
**Fix:** Delete line 93.


### IN-03: `patch_cytools` has dead code before the real `Invariants` import

**File:** `cybir/core/patch.py:386-391`
**Issue:** Lines 386-391 attempt to get `Invariants` via `CalabiYau._Invariants`, which almost certainly does not exist in CYTools (it is not a nested class). The result is immediately overwritten by the `from cytools.calabiyau import Invariants` import on lines 394-401. The first block sets `Invariants = None` via `hasattr` check and then never uses that `None`. This dead code confuses the reader and masks the real import path.
**Fix:** Delete lines 386-391 (the `Invariants = CalabiYau._Invariants if hasattr(CalabiYau, "_Invariants") else None` block) and rely solely on the direct import.


### IN-04: `_invariants_ensure_nilpotency` uses bare `Exception` instead of a domain-specific error

**File:** `cybir/core/patch.py:255, 282`
**Issue:** Two `raise Exception(...)` calls with diagnostic messages would be clearer as `RuntimeError` or `InsufficientGVError`, consistent with the rest of the module.
**Fix:**
```python
raise RuntimeError(
    "This one was supposed to have been computed: ..."
)
```


### IN-05: `weyl.py` `_inherit_contractions` only creates self-loops for terminal walls — generic flops from parent are not connected to the flopped phase target

**File:** `cybir/core/weyl.py:296-308`
**Issue:** When inheriting contractions, the code adds a self-loop for terminal (asymptotic, CFT, su2) walls. But generic `FLOP` contractions from the parent are silently skipped — neither a self-loop nor an edge to the corresponding flopped phase is added. This means the reflected phase is missing its flop edges, which makes the graph topology of the Weyl-expanded region incomplete. Whether this is intentional (Weyl-expanded phases only carry terminal wall info) is not documented.
**Fix:** Add a comment explaining the intentional omission, or add handling for `FLOP` contractions if they should be propagated:
```python
# FLOP contractions are not inherited because the target flopped phases
# in the Weyl-expanded region have not been constructed.
# Asymptotic/CFT/SU2 walls are terminal and become self-loops.
```


### IN-06: `test_classify.py` `TestIsSymmetricFlop.test_symmetric_false` does not verify the actual `is_symmetric_flop` return value is `False` — it only checks it is not `True`

**File:** `tests/test_classify.py:239`
**Issue:** The assertion is `assert is_symmetric_flop(...) is False`, which is correct Python. However, `is_symmetric_flop` returns `bool(np.allclose(...) and np.allclose(...))`, which can return `numpy.bool_` rather than `bool`. In CPython, `numpy.bool_(False) is False` evaluates to `False` — the `is` check fails for numpy booleans. The existing `is True` / `is False` checks throughout `test_classify.py` rely on the `bool(...)` cast inside the implementation, which currently works, but is worth noting as a fragile assumption.

The related `is_asymptotic` and `is_cft` functions also use `bool(np.allclose(...))` which returns a Python `bool`, so those are fine. `is_symmetric_flop` also wraps in `bool(...)` at line 222, so the current tests pass. But if `is_symmetric_flop` is ever refactored to drop the cast, all `is True`/`is False` assertions in tests would silently fail.
**Fix:** Change test assertions to use `==` instead of `is`:
```python
assert is_symmetric_flop(...) == False
# or equivalently:
assert not is_symmetric_flop(...)
```

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

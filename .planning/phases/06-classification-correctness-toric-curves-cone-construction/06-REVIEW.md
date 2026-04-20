---
phase: 06-classification-correctness-toric-curves-cone-construction
reviewed: 2026-04-19T20:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - cybir/__init__.py
  - cybir/core/__init__.py
  - cybir/core/build_gv.py
  - cybir/core/classify.py
  - cybir/core/coxeter.py
  - cybir/core/ekc.py
  - cybir/core/toric_curves.py
  - cybir/core/types.py
  - tests/survey_h11_3.py
  - tests/test_build_gv.py
  - tests/test_classify.py
  - tests/test_coxeter.py
  - tests/test_toric_curves.py
  - tests/test_types.py
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-04-19T20:00:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Phase 6 adds GROSS_FLOP classification, CoxeterGroup dataclass, toric curves module, cone construction methods, and flexible orbit expansion. The code is well-structured, well-documented, and follows the project conventions. The mathematical algorithms are carefully implemented with exact integer arithmetic where it matters and proper pitfall-avoidance documented in comments.

Key concerns:

1. A potential division-by-zero in `zero_vol_divisor` when the null-space vector has all-zero entries (Critical).
2. The `toric_curves.py` module indexes `p.dual().faces()` in parallel with `p.faces(2)` without verifying that the face ordering correspondence holds -- this is a fragile assumption tied to CYTools internals.
3. Several places catch broad `Exception` and silently continue, which could mask bugs during development.

## Critical Issues

### CR-01: Division by zero in `zero_vol_divisor` when null-space vector is all near-zero

**File:** `cybir/core/classify.py:157`
**Issue:** The null-space normalization divides by `max(abs(result))`. If `null_space` returns a vector that is numerically all near-zero (e.g., due to a degenerate geometry or numerical noise), `max(abs(result))` could be zero or near-zero, producing `inf` or `nan` values that silently propagate through the rest of the pipeline. The subsequent `assert np.allclose(result, np.round(result))` would then fail with a cryptic assertion error rather than a meaningful message.

**Fix:**
```python
max_val = max(abs(result))
if max_val < 1e-12:
    return None  # degenerate null-space vector
result /= max_val
result *= minimal_N(result)
```

## Warnings

### WR-01: `_check_nongeneric_cs` compares zero-vol divisor against wrong matrix slice

**File:** `cybir/core/build_gv.py:78-88`
**Issue:** The comment says "Each row of charges is a point/divisor; columns are the h11+1 GLSM charges" and then takes `row[:h11]`. However, `cy.glsm_charge_matrix(include_origin=False)` returns a matrix of shape `(h11, n_points)` where rows are the h11 GLSM charges and columns are the points -- the transpose of what the comment describes. The code takes `row[:h11]` which would be the first `h11` columns (points), not the GLSM charges. This means the proportionality check compares the zero-vol divisor (in the h11 basis) against a vector of the first h11 point charges, which is the correct comparison only if the matrix orientation matches what the code expects. If the CYTools convention differs from the comment, the non-generic CS detection would silently mis-tag walls.

**Fix:** Verify the actual shape of `cy.glsm_charge_matrix(include_origin=False)` and adjust the comment and slicing accordingly. The GLSM charge matrix in CYTools is `(h11, n_points)`, so iterating `for row in charges` gives h11-dimensional rows, each of length `n_points`. Taking `row[:h11]` truncates the point-space vector, which is incorrect. The correct comparison should iterate over *columns* (each column is the charge of one point in the h11 basis):

```python
for col_idx in range(charges.shape[1]):
    row_basis = charges[:, col_idx].astype(float)
    # ... proportionality check
```

### WR-02: `toric_curves.compute_toric_curves` assumes dual-face ordering matches primal-face ordering

**File:** `cybir/core/toric_curves.py:364-368`
**Issue:** The code indexes `p.dual().faces(1)` and `p.dual().faces(2)` in parallel with `p.faces(2)` (line 379), assuming that the i-th 2-face of the polytope corresponds to the i-th 1-face of the dual polytope. This correspondence depends on CYTools maintaining a consistent face ordering between a polytope and its dual, which is not guaranteed by the CYTools API and could break silently with CYTools updates.

**Fix:** Add an assertion or documented verification that the face counts match and that the duality ordering is consistent. At minimum:
```python
assert len(twoface_genera) == len(twofaces), (
    f"Dual 1-face count {len(twoface_genera)} != primal 2-face count {len(twofaces)}"
)
```

### WR-03: `toric_curves.compute_toric_curves` uses `np.sign(...).astype(int)` on a float dot product

**File:** `cybir/core/toric_curves.py:600-605`
**Issue:** `np.sign(c @ tip)` returns a float (`-1.0`, `0.0`, or `1.0`). When `c @ tip` is very close to zero (a curve nearly orthogonal to the tip), floating-point noise can flip the sign, producing an inconsistent orientation. The `.astype(int)` conversion is correct but the upstream sign computation is fragile for near-zero dot products. This could lead to inconsistent curve orientation between different phases or between toric and BFS-computed curves.

**Fix:** Apply a tolerance threshold:
```python
dot = c @ tip
if abs(dot) < 1e-10:
    sign = 0
else:
    sign = int(np.sign(dot))
twoface_charges_reduced_birded[i] = sign * c if sign != 0 else c
```

### WR-04: `_kahler_cones_match` uses `np.round(np.linalg.inv(...))` without verifying integrality

**File:** `cybir/core/classify.py:195`
**Issue:** `M_inv = np.round(np.linalg.inv(reflection.astype(float))).astype(int)` assumes the inverse is integer-valued. For Coxeter reflections (involutions), `M^{-1} = M`, so this is true. However, the function signature accepts a generic `reflection` matrix, and if called with a non-involution (e.g., a Coxeter product element), the rounding would silently corrupt the inverse. While current callers only pass reflections, this is a latent bug if the function is reused.

**Fix:** Add an integrality check:
```python
M_inv_float = np.linalg.inv(reflection.astype(float))
M_inv = np.round(M_inv_float).astype(int)
assert np.allclose(M_inv_float, M_inv, atol=1e-8), (
    "Reflection inverse is not integer-valued"
)
```

### WR-05: `survey_h11_3.py` accesses private attributes of `CYBirationalClass`

**File:** `tests/survey_h11_3.py:59-91`
**Issue:** The survey script accesses `ekc._graph.num_phases`, `ekc._unresolved_walls`, and other private attributes directly. While this is a test/survey script, it couples tightly to the internal implementation. If the internal attribute names change, the survey silently breaks or produces incorrect results (e.g., `n_unresolved` would be `None` if `_unresolved_walls` is renamed).

**Fix:** Use public API where available (e.g., `len(ekc.phases)` instead of `ekc._graph.num_phases`). For `_unresolved_walls`, consider adding a public `unresolved_walls` property.

## Info

### IN-01: Export asymmetry between `cybir/__init__.py` and `cybir/core/__init__.py`

**File:** `cybir/__init__.py:24` vs `cybir/core/__init__.py:22-28`
**Issue:** `cybir/core/__init__.py` exports `classify_phase_type`, `compute_toric_curves`, `induced_2face_triangulations`, and `orient_curves_for_phase`, but the top-level `cybir/__init__.py` only exports `ToricCurveData` and `diagnose_curve` from the toric/classification namespace. This is intentional (core exposes more internals), but the asymmetry is not documented.

**Fix:** Add a comment in `cybir/__init__.py` noting which toric-curve functions are intentionally not re-exported at the top level.

### IN-02: Broad `except Exception` blocks suppress errors silently

**File:** `cybir/core/ekc.py:655`, `cybir/core/ekc.py:693`, `cybir/core/ekc.py:784-786`
**Issue:** Multiple `except Exception: pass` blocks in `_verify_mori_bounds` and `mori_cone_exact` silently swallow all exceptions. During development, this can mask bugs in CYTools API usage or data corruption. The `mori_cone_exact` catch at line 576 is particularly concerning as it swallows comparison failures.

**Fix:** At minimum, log the exception at DEBUG level:
```python
except Exception as exc:
    logger.debug("mori_cone_exact comparison failed: %s", exc)
```

### IN-03: `CalabiYauLite.__str__` computes unused `indices` variable

**File:** `cybir/core/types.py:307`
**Issue:** Line 307 computes `indices = np.triu_indices(h11, m=h11)` but this variable is never used -- the code immediately below iterates with explicit triple-nested loops. This is dead code.

**Fix:** Remove the unused line:
```python
# Remove this line:
indices = np.triu_indices(h11, m=h11)  # not quite right for rank-3 tensor
```

### IN-04: `toric_curves.induced_2face_triangulations` converts `three_simplices` between set and list multiple times

**File:** `cybir/core/toric_curves.py:140-163`
**Issue:** The code creates `three_simplices` as a list of lists, converts to a set of tuples for dedup, converts back to a list of sets, then converts to a numpy object array. This is functional but hard to follow. A comment explaining the data flow would help readability.

**Fix:** Add clarifying comments at each conversion step, or consolidate the conversions.

---

_Reviewed: 2026-04-19T20:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

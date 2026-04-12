---
phase: 02-core-mathematics
reviewed: 2026-04-12T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - cybir/__init__.py
  - cybir/core/__init__.py
  - cybir/core/flop.py
  - cybir/core/gv.py
  - cybir/core/types.py
  - cybir/core/util.py
  - tests/conftest.py
  - tests/generate_snapshots.py
  - tests/test_flop.py
  - tests/test_gv.py
  - tests/test_integration.py
  - tests/test_types.py
  - tests/test_util.py
findings:
  critical: 0
  warning: 5
  info: 2
  total: 7
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

The core mathematics module (types, gv, flop, util) is well-structured with clear docstrings referencing the relevant arXiv papers. The wall-crossing formulas and GV effective invariant computations are straightforward and appear mathematically correct. The test suite is thorough with good coverage of edge cases and snapshot-based integration tests.

Five warnings were found: an equality bug in CalabiYauLite where asymmetric c2 handling produces incorrect results, a StopIteration crash on all-zero curves in normalize_curve, a fragile hash implementation that will silently collide for unlabeled phases, a degenerate return from coxeter_matrix for empty input, and silent pass-through for invalid n_projected values. Two informational items were also noted.

## Warnings

### WR-01: CalabiYauLite.__eq__ is asymmetric when only one side has c2

**File:** `cybir/core/types.py:248-253`
**Issue:** The equality check only compares c2 when both objects have it. If one has c2 set and the other does not, they are considered equal (as long as int_nums match). This violates the expected semantics -- two phases with different c2 data should not be equal. Worse, the comparison is not symmetric in intent: a phase with c2=[24,44] would equal a phase with c2=None.
**Fix:**
```python
def __eq__(self, other):
    if not isinstance(other, CalabiYauLite):
        return NotImplemented
    if not np.allclose(self._int_nums, other._int_nums):
        return False
    if (self._c2 is None) != (other._c2 is None):
        return False
    if self._c2 is not None and other._c2 is not None:
        if not np.allclose(self._c2, other._c2):
            return False
    return True
```

### WR-02: normalize_curve crashes with StopIteration on all-zero input

**File:** `cybir/core/util.py:165`
**Issue:** `next(c for c in curve if c != 0)` raises `StopIteration` if every element of `curve` is zero. The zero curve is not a valid Mori cone generator, but the function does not guard against it. An uncaught `StopIteration` in a generator context can cause silent early termination in Python 3.7+ (PEP 479), and outside generators it surfaces as an unexpected exception type.
**Fix:**
```python
def normalize_curve(curve, return_sign=False):
    first_nonzero = next((c for c in curve if c != 0), None)
    if first_nonzero is None:
        raise ValueError("Cannot normalize the zero curve")
    if first_nonzero > 0:
        to_return = tuple(curve.tolist())
        sign = 1
    else:
        to_return = tuple((-curve).tolist())
        sign = -1
    return (to_return, sign) if return_sign else to_return
```

### WR-03: CalabiYauLite.__hash__ collides for all unlabeled instances

**File:** `cybir/core/types.py:256`
**Issue:** `hash(self._label)` returns `hash(None)` for every CalabiYauLite created without a label. This means all unlabeled instances hash to the same bucket, breaking set/dict usage patterns (e.g., if PhaseGraph stores phases in a set). Since `__eq__` compares int_nums, having hash collisions does not produce incorrect lookups, but it degrades O(1) dict/set operations to O(n) for unlabeled phases.
**Fix:** Either hash on the int_nums data (e.g., `hash(self._int_nums.tobytes())`) or document that a label must be set before using instances in sets/dicts. Given that the EKC orchestrator assigns labels, the simplest fix is:
```python
def __hash__(self):
    if self._label is not None:
        return hash(self._label)
    return hash(self._int_nums.tobytes())
```

### WR-04: coxeter_matrix returns 0-d scalar for empty reflections list

**File:** `cybir/core/util.py:375-376`
**Issue:** `coxeter_matrix([])` returns `np.array(1.0)`, a 0-dimensional scalar array. Any downstream code that expects a 2D matrix (e.g., `matrix_period`, matrix multiplication with `@`) will fail or produce wrong results. The test on line 358 only checks `result is not None`, which masks this.
**Fix:** Either raise ValueError for empty input (preferred, since a Coxeter element with no reflections is ill-defined without knowing the dimension), or require a dimension parameter:
```python
def coxeter_matrix(reflections):
    if not reflections:
        raise ValueError("Cannot compute Coxeter matrix from empty list of reflections")
    return functools.reduce(np.matmul, reflections)
```

### WR-05: projected_int_nums silently returns raw int_nums for invalid n_projected

**File:** `cybir/core/util.py:237`
**Issue:** When `n_projected` is not 1, 2, or 3, the function falls through to `return int_nums` -- silently returning the original unprojected tensor. This could mask bugs in calling code that passes an incorrect value. The function should either raise ValueError or at minimum log a warning.
**Fix:**
```python
else:
    raise ValueError(f"n_projected must be 1, 2, or 3, got {n_projected}")
```

## Info

### IN-01: generate_snapshots.py contains hardcoded absolute path

**File:** `tests/generate_snapshots.py:31-33`
**Issue:** The path to the original cornell-dev code is hardcoded to a specific user's filesystem. This is acceptable for a dev-only fixture generator that is not meant to be portable, but worth noting. The script will fail silently on any other machine.
**Fix:** Consider reading the path from an environment variable with the hardcoded value as default:
```python
_ORIGINAL_DIR = pathlib.Path(
    os.environ.get("CORNELL_DEV_DIR",
        "/Users/elijahsheridan/Research/string/cytools_code/cornell-dev/projects/vex/elijah")
)
```

### IN-02: Unused import of null_space in util.py

**File:** `cybir/core/util.py:16`
**Issue:** `from scipy.linalg import null_space` is imported but never used anywhere in the file. All null-space-like operations use `hsnf.smith_normal_form` instead.
**Fix:** Remove the unused import:
```python
# Delete line 16:
# from scipy.linalg import null_space
```

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

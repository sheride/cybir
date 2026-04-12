---
phase: 01-foundation
reviewed: 2026-04-11T12:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - cybir/__init__.py
  - cybir/core/__init__.py
  - cybir/core/ekc.py
  - cybir/core/flop.py
  - cybir/core/graph.py
  - cybir/core/types.py
  - cybir/core/util.py
  - pyproject.toml
  - tests/__init__.py
  - tests/conftest.py
  - tests/test_graph.py
  - tests/test_types.py
  - tests/test_util.py
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-11
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

The Phase 1 foundation is well-structured: clean package layout, proper `__init__.py` exports, solid data types with freeze mechanisms, and good test coverage. The code is readable and follows NumPy-style docstrings consistently. No security issues or critical bugs found.

There are four warnings -- all logic/correctness concerns in the core types and utilities that could cause subtle bugs in downstream phases. Three informational items note minor quality improvements.

## Warnings

### WR-01: CalabiYauLite.__eq__ is asymmetric when only one side has c2

**File:** `cybir/core/types.py:223-228`
**Issue:** The `__eq__` method only compares `c2` when *both* objects have it set. This means `CalabiYauLite(int_nums=X, c2=[24,44])` equals `CalabiYauLite(int_nums=X, c2=None)`, which is mathematically incorrect -- two phases with the same intersection numbers but different (or unknown) second Chern classes should not be considered equal. The current logic silently treats "c2 not provided" as "c2 matches anything."
**Fix:**
```python
def __eq__(self, other):
    if not isinstance(other, CalabiYauLite):
        return NotImplemented
    if not np.allclose(self._int_nums, other._int_nums):
        return False
    # Require c2 status to match: both None or both set-and-equal
    if (self._c2 is None) != (other._c2 is None):
        return False
    if self._c2 is not None and not np.allclose(self._c2, other._c2):
        return False
    return True
```

### WR-02: CalabiYauLite.__hash__ is inconsistent with __eq__

**File:** `cybir/core/types.py:231`
**Issue:** `__hash__` uses only `label` while `__eq__` uses `int_nums` and `c2`. This violates the Python invariant that `a == b` implies `hash(a) == hash(b)`. Two `CalabiYauLite` objects with the same `int_nums`/`c2` but different labels will compare equal yet have different hashes. Conversely, two objects with the same label but different `int_nums` will have the same hash but compare unequal. This will cause silent data corruption in sets and dicts.
**Fix:** Either make `__hash__` consistent with `__eq__` (e.g., hash the `int_nums` bytes), or make `__eq__` use labels too. Given the graph uses labels as node keys, the simplest correct fix is to include `label` in `__eq__`:
```python
def __eq__(self, other):
    if not isinstance(other, CalabiYauLite):
        return NotImplemented
    return self._label == other._label

def __hash__(self):
    return hash(self._label)
```
Or if equality should remain physics-based (matching intersection data), change `__hash__` to match:
```python
def __hash__(self):
    return hash(self._int_nums.tobytes())
```

### WR-03: normalize_curve crashes on all-zero input

**File:** `cybir/core/util.py:162`
**Issue:** `next(c for c in curve if c != 0)` raises `StopIteration` if all elements are zero. While an all-zero curve is mathematically degenerate, this produces an unhelpful traceback. A zero curve could appear as a result of a projection or numerical operation in downstream EKC code.
**Fix:**
```python
def normalize_curve(curve, return_sign=False):
    first_nonzero = next((c for c in curve if c != 0), None)
    if first_nonzero is None:
        raise ValueError("Cannot normalize the zero curve.")
    if first_nonzero > 0:
        to_return = tuple(curve.tolist())
        sign = 1
    else:
        to_return = tuple((-curve).tolist())
        sign = -1
    return (to_return, sign) if return_sign else to_return
```

### WR-04: display_name silently falls through on invalid notation argument

**File:** `cybir/core/types.py:63-65`
**Issue:** `ContractionType.display_name("typo")` silently returns the paper notation instead of signaling an error, because the method only checks `if notation == "wilson"` and falls through to paper for anything else. This could mask bugs in calling code.
**Fix:**
```python
def display_name(self, notation="paper"):
    if notation == "wilson":
        return _WILSON_NOTATION[self.name]
    if notation == "paper":
        return _PAPER_NOTATION[self.name]
    raise ValueError(f"Unknown notation {notation!r}; expected 'paper' or 'wilson'.")
```

## Info

### IN-01: PhaseGraph.add_phase does not validate that label is set

**File:** `cybir/core/graph.py:43`
**Issue:** If `phase.label` is `None`, `self._graph.add_node(None, phase=phase)` succeeds silently, creating a node keyed by `None`. Later lookups like `get_phase(None)` would work but this is almost certainly a caller bug. A guard would catch construction mistakes early.
**Fix:** Add `if phase.label is None: raise ValueError("Phase must have a label set before adding to graph.")` at the top of `add_phase`.

### IN-02: ExtremalContraction.flopping_curve returns a reference, not a copy

**File:** `cybir/core/types.py:296`
**Issue:** `CalabiYauLite.int_nums` returns `np.copy()` to prevent mutation of internal state, but `ExtremalContraction.flopping_curve` returns the raw array. Since `ExtremalContraction` is frozen (attribute-level), callers could still mutate the array contents in-place via `ec.flopping_curve[0] = 99`. This is a minor inconsistency since the object is conceptually immutable.
**Fix:** Return `np.copy(self._flopping_curve)` for consistency, or document that numpy array contents are not protected by the freeze mechanism.

### IN-03: Stub files ekc.py and flop.py are empty placeholders

**File:** `cybir/core/ekc.py:1`, `cybir/core/flop.py:1`
**Issue:** These files contain only a docstring. They are not imported anywhere and contribute no functionality. This is fine for a Phase 1 skeleton, but they should be populated or removed before Phase 2 completion to avoid dead files.
**Fix:** No action needed now; track for Phase 2/3 implementation.

---

_Reviewed: 2026-04-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

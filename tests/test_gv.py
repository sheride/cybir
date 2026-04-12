"""Tests for cybir.core.gv GV series and curve classification functions."""

import numpy as np
import pytest

from cybir.core.gv import compute_gv_eff, compute_gv_series, is_nilpotent, is_potent


class MockGVInvariants:
    """Mock for CYTools Invariants object.

    Returns GV invariants from a predefined dict, None for out-of-range.
    """

    def __init__(self, gv_dict):
        self._gv_dict = gv_dict

    def gv(self, curve):
        key = tuple(curve)
        return self._gv_dict.get(key, None)


class TestComputeGVSeries:
    """Tests for compute_gv_series."""

    def test_basic_series(self):
        """Extract GV series for multiples of a curve."""
        gv_inv = MockGVInvariants({
            (1, 0): 252,
            (2, 0): 0,
            (3, 0): 0,
            # (4, 0) not in dict -> returns None -> stop
        })
        result = compute_gv_series(gv_inv, np.array([1, 0]))
        assert result == [252, 0, 0]

    def test_stops_at_none(self):
        """Series stops when gv returns None."""
        gv_inv = MockGVInvariants({
            (1, 0): 10,
            (2, 0): -5,
            # (3, 0) -> None
        })
        result = compute_gv_series(gv_inv, np.array([1, 0]))
        assert result == [10, -5]

    def test_first_call_none_returns_empty(self):
        """If gv(1*C) is None, return empty list."""
        gv_inv = MockGVInvariants({})
        result = compute_gv_series(gv_inv, np.array([1, 0]))
        assert result == []

    def test_multicomponent_curve(self):
        """Works with curves that have multiple nonzero components."""
        gv_inv = MockGVInvariants({
            (1, 1): 100,
            (2, 2): 50,
            (3, 3): None,  # explicit None in dict
        })
        # Note: (3,3) maps to None, so series stops
        # But MockGVInvariants.gv returns None for missing keys too,
        # so let's be explicit
        gv_inv2 = MockGVInvariants({
            (1, 1): 100,
            (2, 2): 50,
        })
        result = compute_gv_series(gv_inv2, np.array([1, 1]))
        assert result == [100, 50]


class TestComputeGVEff:
    """Tests for compute_gv_eff."""

    def test_single_element(self):
        """[252] -> gv_eff_1 = 252, gv_eff_3 = 252."""
        gv_eff_1, gv_eff_3 = compute_gv_eff([252])
        assert gv_eff_1 == 252
        assert gv_eff_3 == 252

    def test_series_252_0_0(self):
        """[252, 0, 0] -> gv_eff_1 = 252, gv_eff_3 = 252."""
        gv_eff_1, gv_eff_3 = compute_gv_eff([252, 0, 0])
        assert gv_eff_1 == 252
        assert gv_eff_3 == 252

    def test_series_with_higher_multiples(self):
        """[1, -2, 3] -> gv_eff_1 = 1-4+9 = 6, gv_eff_3 = 1-16+81 = 66."""
        gv_eff_1, gv_eff_3 = compute_gv_eff([1, -2, 3])
        assert gv_eff_1 == 6
        assert gv_eff_3 == 66

    def test_empty_raises_valueerror(self):
        """Empty series raises ValueError."""
        with pytest.raises(ValueError):
            compute_gv_eff([])

    def test_returns_tuple(self):
        """Result is a tuple of (gv_eff_1, gv_eff_3)."""
        result = compute_gv_eff([1])
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestIsPotent:
    """Tests for is_potent."""

    def test_potent_last_nonzero(self):
        """Potent when last entry is nonzero."""
        assert is_potent([252, 0, 1]) is True

    def test_not_potent_last_zero(self):
        """Not potent when last entry is zero."""
        assert is_potent([252, 0, 0]) is False

    def test_empty_not_potent(self):
        """Empty series is not potent."""
        assert is_potent([]) is False

    def test_single_nonzero(self):
        """Single nonzero element is potent."""
        assert is_potent([1]) is True

    def test_single_zero(self):
        """Single zero element is not potent."""
        assert is_potent([0]) is False


class TestIsNilpotent:
    """Tests for is_nilpotent."""

    def test_nilpotent_last_zero(self):
        """Nilpotent when last entry is zero."""
        assert is_nilpotent([252, 0, 0]) is True

    def test_not_nilpotent_last_nonzero(self):
        """Not nilpotent when last entry is nonzero."""
        assert is_nilpotent([252, 0, 1]) is False

    def test_empty_not_nilpotent(self):
        """Empty series is not nilpotent."""
        assert is_nilpotent([]) is False

    def test_single_zero(self):
        """Single zero is nilpotent."""
        assert is_nilpotent([0]) is True

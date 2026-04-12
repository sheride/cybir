"""Tests for cybir.core.classify module.

Uses real h11=2 polytope data from integration fixtures as ground truth
for classification correctness, plus synthetic h11=3 data for
asymptotic/CFT edge cases.
"""

import numpy as np
import pytest

from cybir.core.classify import (
    classify_contraction,
    zero_vol_divisor,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
)
from cybir.core.types import ContractionType, InsufficientGVError
from cybir.core.coxeter import coxeter_reflection


# ---------------------------------------------------------------------------
# Fixtures — synthetic h11=3 for asymptotic/CFT
# ---------------------------------------------------------------------------


@pytest.fixture
def h11_3_asymptotic():
    """Intersection numbers for h11=3 where projecting along curve gives all zeros.

    With curve = e_0, projection matrix drops the first index, so
    projected int_nums = kappa_{abc} with a,b,c in {1,2}.
    Setting those components to zero makes is_asymptotic True.
    """
    int_nums = np.zeros((3, 3, 3))
    int_nums[0, 1, 2] = 1
    int_nums[0, 2, 1] = 1
    int_nums[1, 0, 2] = 1
    int_nums[2, 0, 1] = 1
    int_nums[1, 2, 0] = 1
    int_nums[2, 1, 0] = 1
    curve = np.array([1, 0, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_non_asymptotic():
    """Intersection numbers where projected components do NOT vanish."""
    int_nums = np.zeros((3, 3, 3))
    int_nums[1, 1, 1] = 5
    int_nums[0, 1, 2] = 1
    int_nums[0, 2, 1] = 1
    int_nums[1, 0, 2] = 1
    int_nums[2, 0, 1] = 1
    int_nums[1, 2, 0] = 1
    int_nums[2, 1, 0] = 1
    curve = np.array([1, 0, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_cft():
    """Intersection numbers whose N=1 projected matrix is rank-deficient.

    With curve = [1,0,0], the projected matrix (projecting last index)
    has shape (3, 3, 2) reshaped to (3, 6). We make its rank < min(3,6)=3
    by having kappa_{1,j,k} = 2 * kappa_{2,j,k} for all j,k.
    """
    int_nums = np.zeros((3, 3, 3))
    int_nums[1, 0, 0] = 2
    int_nums[2, 0, 0] = 1
    int_nums[1, 1, 1] = 4
    int_nums[2, 1, 1] = 2
    int_nums[1, 2, 2] = 6
    int_nums[2, 2, 2] = 3
    curve = np.array([1, 0, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_not_cft():
    """Intersection numbers whose N=1 projected matrix is full-rank.

    With curve = [1,0,0], projection drops index 0. The resulting
    matrix (3, 3, 2) reshaped to (3, 6) must have rank = 3.
    """
    int_nums = np.zeros((3, 3, 3))
    # Row for a=0 (kappa_{0,j,P_k})
    int_nums[0, 0, 1] = 3
    int_nums[0, 1, 2] = 7
    int_nums[0, 2, 1] = 7  # symmetry
    # Row for a=1 (kappa_{1,j,P_k})
    int_nums[1, 1, 1] = 5
    int_nums[1, 2, 2] = 2
    # Row for a=2 (kappa_{2,j,P_k})
    int_nums[2, 2, 2] = 9
    int_nums[2, 0, 2] = 1
    int_nums[2, 2, 0] = 1  # symmetry
    curve = np.array([1, 0, 0])
    return int_nums, curve


# ---------------------------------------------------------------------------
# Fixtures — real h11=2 data from integration snapshots
# ---------------------------------------------------------------------------


@pytest.fixture
def real_symmetric_flop():
    """Polytope 2, wall 0: symmetric flop."""
    return {
        "int_nums": np.array([[[1, -1], [-1, 1]], [[-1, 1], [1, 2]]]),
        "c2": np.array([10, 32]),
        "curve": np.array([1, 0]),
        "gv_series": [6, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "zero_vol_divisor": np.array([-2, 1]),
        "coxeter_reflection": np.array([[-1.0, 1.0], [0.0, 1.0]]),
    }


@pytest.fixture
def real_generic_flop():
    """Polytope 5, wall 1: generic flop (type II, non-symmetric)."""
    return {
        "int_nums": np.array([[[3, 5], [5, 5]], [[5, 5], [5, 5]]]),
        "c2": np.array([42, 50]),
        "curve": np.array([0, 1]),
        "gv_series": [20, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "zero_vol_divisor": np.array([5, -3]),
    }


@pytest.fixture
def real_su2():
    """Polytope 9, wall 1: su(2) enhancement."""
    return {
        "int_nums": np.array([[[0, 3], [3, -1]], [[3, -1], [-1, -1]]]),
        "c2": np.array([36, 14]),
        "curve": np.array([1, -1]),
        "gv_series": [18, -2, 0, 0, 0, 0, 0, 0, 0, 0],
        "zero_vol_divisor": np.array([0, 1]),
        "coxeter_reflection": np.array([[1.0, 2.0], [0.0, -1.0]]),
    }


# ---------------------------------------------------------------------------
# is_asymptotic tests
# ---------------------------------------------------------------------------


class TestIsAsymptotic:
    def test_asymptotic_true(self, h11_3_asymptotic):
        int_nums, curve = h11_3_asymptotic
        assert is_asymptotic(int_nums, curve) is True

    def test_asymptotic_false(self, h11_3_non_asymptotic):
        int_nums, curve = h11_3_non_asymptotic
        assert is_asymptotic(int_nums, curve) is False


# ---------------------------------------------------------------------------
# is_cft tests
# ---------------------------------------------------------------------------


class TestIsCft:
    def test_cft_true(self, h11_3_cft):
        int_nums, curve = h11_3_cft
        assert is_cft(int_nums, curve) is True

    def test_cft_false(self, h11_3_not_cft):
        int_nums, curve = h11_3_not_cft
        assert is_cft(int_nums, curve) is False

    def test_cft_real_symmetric_is_not_cft(self, real_symmetric_flop):
        """A real symmetric flop wall should NOT be classified as CFT."""
        d = real_symmetric_flop
        assert is_cft(d["int_nums"], d["curve"]) is False

    def test_cft_real_su2_is_not_cft(self, real_su2):
        """A real su(2) wall should NOT be classified as CFT."""
        d = real_su2
        assert is_cft(d["int_nums"], d["curve"]) is False


# ---------------------------------------------------------------------------
# zero_vol_divisor tests
# ---------------------------------------------------------------------------


class TestFindZeroVolDivisor:
    def test_returns_integer_divisor(self, real_symmetric_flop):
        d = real_symmetric_flop
        result = zero_vol_divisor(d["int_nums"], d["curve"])
        assert result is not None
        assert np.allclose(result, np.round(result))

    def test_matches_expected(self, real_symmetric_flop):
        d = real_symmetric_flop
        result = zero_vol_divisor(d["int_nums"], d["curve"])
        assert result is not None
        # May differ by overall sign
        assert np.allclose(np.abs(result), np.abs(d["zero_vol_divisor"]))

    def test_sign_convention(self, real_symmetric_flop):
        """D . C < 0 (simple dot product)."""
        d = real_symmetric_flop
        result = zero_vol_divisor(d["int_nums"], d["curve"])
        assert result is not None
        assert result @ d["curve"] <= 0

    def test_generic_flop_has_divisor(self, real_generic_flop):
        d = real_generic_flop
        result = zero_vol_divisor(d["int_nums"], d["curve"])
        assert result is not None

    def test_su2_has_divisor(self, real_su2):
        d = real_su2
        result = zero_vol_divisor(d["int_nums"], d["curve"])
        assert result is not None


# ---------------------------------------------------------------------------
# is_symmetric_flop tests
# ---------------------------------------------------------------------------


class TestIsSymmetricFlop:
    def test_symmetric_true(self, real_symmetric_flop):
        d = real_symmetric_flop
        from cybir.core.gv import gv_eff

        gv_eff_1, gv_eff_3 = gv_eff(d["gv_series"])
        assert is_symmetric_flop(
            d["int_nums"], d["c2"], d["curve"],
            gv_eff_1, gv_eff_3, d["coxeter_reflection"]
        ) is True

    def test_symmetric_false(self, real_generic_flop):
        """Generic flop (II) is not symmetric."""
        d = real_generic_flop
        from cybir.core.gv import gv_eff

        gv_eff_1, gv_eff_3 = gv_eff(d["gv_series"])
        zvd = zero_vol_divisor(d["int_nums"], d["curve"])
        cox = coxeter_reflection(zvd, d["curve"])
        assert is_symmetric_flop(
            d["int_nums"], d["c2"], d["curve"],
            gv_eff_1, gv_eff_3, cox
        ) is False


# ---------------------------------------------------------------------------
# classify_contraction tests
# ---------------------------------------------------------------------------


class TestClassifyContraction:
    def test_asymptotic(self, h11_3_asymptotic):
        int_nums, curve = h11_3_asymptotic
        c2 = np.array([24, 44, 60])
        gv_series = [0, 0, 0]
        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.ASYMPTOTIC
        assert result["zero_vol_divisor"] is None
        assert result["coxeter_reflection"] is None

    def test_cft(self, h11_3_cft):
        int_nums, curve = h11_3_cft
        c2 = np.array([24, 44, 60])
        gv_series = [0, 0, 0]
        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.CFT

    def test_potent_raises(self):
        """Potent curve (last GV nonzero) raises InsufficientGVError.

        Uses h11=3 int_nums that are not asymptotic or CFT, so the
        classification reaches the potency check.
        """
        int_nums = np.zeros((3, 3, 3))
        int_nums[0, 0, 1] = 3
        int_nums[0, 1, 0] = 3
        int_nums[1, 0, 0] = 3
        int_nums[1, 1, 1] = 5
        int_nums[2, 2, 2] = 9
        int_nums[0, 2, 2] = 1
        int_nums[2, 0, 2] = 1
        int_nums[2, 2, 0] = 1
        c2 = np.array([24, 44, 60])
        curve = np.array([1, 0, 0])
        gv_series = [-2, 0, 1]  # last entry nonzero -> potent
        with pytest.raises(InsufficientGVError, match="potent"):
            classify_contraction(int_nums, c2, curve, gv_series)

    def test_symmetric_flop(self, real_symmetric_flop):
        d = real_symmetric_flop
        result = classify_contraction(
            d["int_nums"], d["c2"], d["curve"], d["gv_series"]
        )
        assert result["contraction_type"] == ContractionType.SYMMETRIC_FLOP
        assert result["zero_vol_divisor"] is not None
        assert result["coxeter_reflection"] is not None

    def test_su2(self, real_su2):
        d = real_su2
        result = classify_contraction(
            d["int_nums"], d["c2"], d["curve"], d["gv_series"]
        )
        assert result["contraction_type"] == ContractionType.SU2

    def test_generic_flop(self, real_generic_flop):
        d = real_generic_flop
        result = classify_contraction(
            d["int_nums"], d["c2"], d["curve"], d["gv_series"]
        )
        assert result["contraction_type"] == ContractionType.FLOP
        assert result["zero_vol_divisor"] is not None

    def test_result_dict_keys(self, h11_3_asymptotic):
        int_nums, curve = h11_3_asymptotic
        c2 = np.array([24, 44, 60])
        gv_series = [0, 0, 0]
        result = classify_contraction(int_nums, c2, curve, gv_series)
        expected_keys = {
            "contraction_type",
            "zero_vol_divisor",
            "coxeter_reflection",
            "gv_invariant",
            "effective_gv",
            "gv_eff_1",
            "gv_series",
        }
        assert set(result.keys()) == expected_keys

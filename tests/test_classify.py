"""Tests for cybir.core.classify module."""

import numpy as np
import pytest

from cybir.core.classify import (
    classify_contraction,
    find_zero_vol_divisor,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
)
from cybir.core.types import ContractionType, InsufficientGVError
from cybir.core.util import get_coxeter_reflection


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def h11_3_asymptotic():
    """Intersection numbers for h11=3 where projecting along curve gives all zeros.

    We choose int_nums such that kappa_{ijk} C^i C^j C^k = 0 for
    curve = [1, 0, 0], and the fully-projected components vanish.
    With curve = e_0, projection matrix drops the first index, so
    projected int_nums = kappa_{abc} with a,b,c in {1,2}.
    Setting those components to zero makes is_asymptotic True.
    """
    int_nums = np.zeros((3, 3, 3))
    # Only nonzero components involve index 0
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
    int_nums[1, 1, 1] = 5  # purely in projected space
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
    """Intersection numbers whose n_projected=1 matrix is rank-deficient.

    With curve = [1,0,0], projection drops index 0. The projected
    matrix M_{jk} = kappa_{ajk} P^a_i with a in {1,2}, j,k in {0,1,2}.
    We want the resulting (2, 3) matrix (after projection of one index)
    to be rank-deficient, i.e., the two rows are linearly dependent.
    """
    int_nums = np.zeros((3, 3, 3))
    # Make kappa_{1,j,k} = 2 * kappa_{2,j,k} for all j,k
    # so after projecting one index, the matrix rows are proportional
    int_nums[1, 0, 0] = 2
    int_nums[2, 0, 0] = 1
    int_nums[1, 1, 1] = 4
    int_nums[2, 1, 1] = 2
    int_nums[1, 2, 2] = 6
    int_nums[2, 2, 2] = 3
    curve = np.array([1, 0, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_full_rank():
    """Intersection numbers whose projected matrix is full-rank (not CFT)."""
    int_nums = np.zeros((3, 3, 3))
    int_nums[1, 1, 1] = 5
    int_nums[2, 2, 2] = 3
    int_nums[1, 2, 2] = 1
    curve = np.array([1, 0, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_zero_vol():
    """Intersection numbers with a known zero-volume divisor.

    Uses curve = [1, 1, 0] so that the projection matrix mixes
    basis directions and P.T @ null_vec can have nonzero dot product
    with the curve (enabling sign convention test).

    We need M_ab = P_ai P_bj kappa_ijk C_k to be singular.
    """
    # For curve = [1, 1, 0], hsnf gives P of shape (2, 3).
    # We construct int_nums so that M has a non-trivial null space.
    # Build a symmetric int_nums tensor where kappa contracted with
    # curve along one index gives a rank-deficient projected matrix.
    int_nums = np.zeros((3, 3, 3))
    # Set up so that kappa_{ij0} + kappa_{ij1} (contraction with [1,1,0])
    # gives a rank-1 matrix in the projected basis.
    # kappa_{ijk} C_k = kappa_{ij0} + kappa_{ij1}
    # Make this a rank-1 outer product: v_i v_j
    v = np.array([1.0, 1.0, 2.0])
    for i in range(3):
        for j in range(3):
            # Split equally between k=0 and k=1
            int_nums[i, j, 0] = v[i] * v[j] / 2.0
            int_nums[i, j, 1] = v[i] * v[j] / 2.0
    # Also add some off-curve components so it's not asymptotic
    int_nums[2, 2, 2] = 5.0
    curve = np.array([1, 1, 0])
    return int_nums, curve


@pytest.fixture
def h11_3_no_zero_vol():
    """Intersection numbers with no zero-volume divisor (full-rank projected matrix).

    Uses curve = [1, 1, 0] with int_nums such that the contracted
    projected matrix is full rank.
    """
    int_nums = np.zeros((3, 3, 3))
    # kappa_{ijk} C_k = kappa_{ij0} + kappa_{ij1}
    # Make this full-rank in the projected basis.
    int_nums[0, 0, 0] = 3
    int_nums[0, 0, 1] = 1
    int_nums[1, 1, 0] = 1
    int_nums[1, 1, 1] = 4
    int_nums[2, 2, 0] = 2
    int_nums[2, 2, 1] = 3
    int_nums[0, 1, 0] = 1
    int_nums[1, 0, 0] = 1  # symmetry
    int_nums[0, 2, 0] = 1
    int_nums[2, 0, 0] = 1  # symmetry
    # Non-zero projected int_nums
    int_nums[1, 1, 1] = 5
    int_nums[2, 2, 2] = 7
    curve = np.array([1, 1, 0])
    return int_nums, curve


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

    def test_cft_false(self, h11_3_full_rank):
        int_nums, curve = h11_3_full_rank
        assert is_cft(int_nums, curve) is False


# ---------------------------------------------------------------------------
# find_zero_vol_divisor tests
# ---------------------------------------------------------------------------


class TestFindZeroVolDivisor:
    def test_returns_none_when_no_zero_vol(self, h11_3_no_zero_vol):
        int_nums, curve = h11_3_no_zero_vol
        result = find_zero_vol_divisor(int_nums, curve)
        assert result is None

    def test_returns_integer_divisor(self, h11_3_zero_vol):
        int_nums, curve = h11_3_zero_vol
        result = find_zero_vol_divisor(int_nums, curve)
        assert result is not None
        # Check integrality
        assert np.allclose(result, np.round(result))

    def test_sign_convention(self, h11_3_zero_vol):
        """kappa_{ijk} D_i D_j C_k <= 0 (volume shrinks at wall).

        Since the simple dot product D.C vanishes identically for
        divisors found via the projection method, the sign is
        determined by the triple intersection number contracted
        with D, D, C.
        """
        int_nums, curve = h11_3_zero_vol
        result = find_zero_vol_divisor(int_nums, curve)
        assert result is not None
        vol = np.einsum("ijk,i,j,k", int_nums, result, result, curve)
        assert vol <= 0


# ---------------------------------------------------------------------------
# is_symmetric_flop tests
# ---------------------------------------------------------------------------


class TestIsSymmetricFlop:
    def test_symmetric_true(self):
        """When wall-crossed int_nums/c2 match Coxeter-reflected ones.

        We construct gv_eff values by computing what makes the
        wall-crossing match the Coxeter reflection, then verify
        is_symmetric_flop returns True.
        """
        h11 = 2
        curve = np.array([1, 0])
        # Construct int_nums and c2 such that the wall-crossing and
        # Coxeter reflection can agree. Use divisor parallel to curve
        # so M = I - 2*outer(C, D)/(C.D) acts simply.
        divisor = np.array([1, 0])  # D parallel to C
        cox = get_coxeter_reflection(divisor, curve)
        # cox = I - 2*outer([1,0],[1,0])/1 = [[-1,0],[0,1]]
        # So cox flips the first component only.

        # Choose int_nums = kappa with kappa_000=6, kappa_001=kappa_010=kappa_100=2
        # kappa_011=kappa_101=kappa_110=0, kappa_111=4
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[0, 0, 1] = 2
        int_nums[0, 1, 0] = 2
        int_nums[1, 0, 0] = 2
        int_nums[1, 1, 1] = 4

        # cox_intnums[i,j,k] = cox[i,a]*cox[j,b]*cox[k,c]*kappa[a,b,c]
        # cox = diag(-1, 1), so cox_intnums flips signs for odd count of 0-indices
        # cox_intnums[0,0,0] = (-1)^3 * 6 = -6
        # cox_intnums[0,0,1] = (-1)^2 * 2 = 2  (no change -- but wait, let me compute)
        # Actually: cox[0,0]=-1, cox[0,1]=0, cox[1,0]=0, cox[1,1]=1
        # cox_intnums[i,j,k] = sum cox[i,a]cox[j,b]cox[k,c] kappa[a,b,c]
        # For i=0,j=0,k=0: (-1)(-1)(-1)*6 = -6
        # For i=0,j=0,k=1: (-1)(-1)(1)*2 = 2
        # For i=1,j=1,k=1: (1)(1)(1)*4 = 4
        # For i=0,j=1,k=0: (-1)(1)(-1)*2 = 2
        # For i=1,j=0,k=0: (1)(-1)(-1)*2 = 2
        # So cox_intnums = int_nums except [0,0,0]: -6 instead of 6

        # wall_cross: kappa' = kappa - g3 * C_a C_b C_c
        # kappa'[0,0,0] = 6 - g3, others unchanged (C=[1,0] only affects [0,0,0])
        # Need: 6 - g3 = -6 => g3 = 12
        gv_eff_3 = 12

        # c2: choose so that c2' = c2 + 2*g1*C matches cox.T @ c2
        # cox.T @ c2 = [[-1,0],[0,1]] @ c2 = [-c2[0], c2[1]]
        # c2 + 2*g1*[1,0] = [c2[0]+2*g1, c2[1]]
        # Need: c2[0]+2*g1 = -c2[0] => g1 = -c2[0]
        c2 = np.array([24, 44])
        gv_eff_1 = -24

        assert is_symmetric_flop(int_nums, c2, curve, gv_eff_1, gv_eff_3, cox) is True

    def test_symmetric_false(self):
        """When wall-crossed values differ from Coxeter-reflected."""
        h11 = 2
        curve = np.array([1, 0])
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[1, 1, 1] = 4
        c2 = np.array([24, 44])
        divisor = np.array([1, 0])
        cox = get_coxeter_reflection(divisor, curve)

        # Use wrong gv_eff values that won't match
        gv_eff_1 = 999
        gv_eff_3 = 999

        assert is_symmetric_flop(int_nums, c2, curve, gv_eff_1, gv_eff_3, cox) is False


# ---------------------------------------------------------------------------
# classify_contraction tests
# ---------------------------------------------------------------------------


class TestClassifyContraction:
    """Tests for the classify_contraction orchestrator."""

    def test_asymptotic(self, h11_3_asymptotic):
        """Asymptotic contraction returns ASYMPTOTIC type."""
        int_nums, curve = h11_3_asymptotic
        c2 = np.array([24, 44, 60])
        gv_series = [0, 0, 0]  # not used for asymptotic
        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.ASYMPTOTIC
        assert result["zero_vol_divisor"] is None
        assert result["coxeter_reflection"] is None

    def test_cft(self, h11_3_cft):
        """CFT contraction returns CFT type."""
        int_nums, curve = h11_3_cft
        c2 = np.array([24, 44, 60])
        gv_series = [0, 0, 0]  # not used for CFT
        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.CFT
        assert result["zero_vol_divisor"] is None
        assert result["coxeter_reflection"] is None

    def test_potent_raises(self):
        """Potent curve (last GV nonzero) raises InsufficientGVError."""
        h11 = 2
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[1, 1, 1] = 4
        c2 = np.array([24, 44])
        curve = np.array([1, 0])
        gv_series = [-2, 0, 1]  # last entry nonzero -> potent
        with pytest.raises(InsufficientGVError, match="potent"):
            classify_contraction(int_nums, c2, curve, gv_series)

    def test_flop_no_zero_vol(self):
        """When no zero-vol divisor exists, returns FLOP."""
        h11 = 2
        # Use int_nums where the projected matrix contracted with curve
        # is full-rank (no null space), so find_zero_vol_divisor returns None.
        # For h11=2 with curve=[1,0], P=[0,1] (1x2), so proj2 contracted
        # with curve is a scalar. If it's nonzero, null space is empty.
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[0, 1, 1] = 2
        int_nums[1, 0, 1] = 2
        int_nums[1, 1, 0] = 2
        int_nums[1, 1, 1] = 4
        c2 = np.array([24, 44])
        curve = np.array([1, 0])
        gv_series = [-2, 0, 0]  # nilpotent
        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.FLOP
        assert result["zero_vol_divisor"] is None
        assert result["coxeter_reflection"] is None
        assert "gv_invariant" in result
        assert "effective_gv" in result
        assert "gv_eff_1" in result
        assert "gv_series" in result

    def test_symmetric_flop(self, monkeypatch):
        """Symmetric flop with non-negative GV returns SYMMETRIC_FLOP.

        Uses monkeypatch to provide a zero-vol divisor with nonzero
        curve intersection, enabling a non-trivial Coxeter reflection
        and a genuine symmetric flop test.
        """
        import cybir.core.classify as cls

        h11 = 2
        curve = np.array([1, 0])
        divisor = np.array([1, 0])
        cox = get_coxeter_reflection(divisor, curve)
        # cox = diag(-1, 1)

        # int_nums where wall-crossing matches Coxeter reflection
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[0, 0, 1] = 2
        int_nums[0, 1, 0] = 2
        int_nums[1, 0, 0] = 2
        int_nums[1, 1, 1] = 4
        c2 = np.array([24, 44])

        # Symmetry requires gv_eff_3=12, gv_eff_1=-24
        # Use monkeypatch to inject the zero-vol divisor
        monkeypatch.setattr(cls, "find_zero_vol_divisor", lambda *a: divisor.astype(float))

        # gv_series: g0 + 2*g1 = -24, g0 + 8*g1 = 12 => g1=6, g0=-36
        # Both non-negative check: gv[0]=-36 < 0 -> would be SU2.
        # Need to choose int_nums so gv_eff are small.
        # kappa[0,0,0]=1: g3=2, c2[0]=1: g1=-1
        # g0+2*g1=-1, g0+8*g1=2 => g1=0.5 non-integer.
        # With kappa[0,0,0]=0: g3=0, c2[0]=0: g1=0. gv=[0,0] works!
        int_nums2 = np.zeros((h11, h11, h11))
        int_nums2[1, 1, 1] = 4
        c2_sym = np.array([0, 44])
        gv_series = [0, 0]
        # gv_eff_1=0, gv_eff_3=0.
        # Wall-crossed: kappa'=kappa, c2'=c2.
        # Coxeter-reflected: only kappa[0,0,0]=0 is affected, stays 0.
        # cox_c2 = [0, 44]. Match!

        result = classify_contraction(int_nums2, c2_sym, curve, gv_series)
        assert result["contraction_type"] == ContractionType.SYMMETRIC_FLOP
        assert result["zero_vol_divisor"] is not None
        assert result["coxeter_reflection"] is not None

    def test_su2(self, monkeypatch):
        """Symmetric flop with negative GV returns SU2.

        Uses monkeypatch to inject a zero-vol divisor that produces
        a non-trivial Coxeter reflection enabling the SU2 branch.
        """
        import cybir.core.classify as cls

        h11 = 2
        curve = np.array([1, 0])
        divisor = np.array([1, 0])
        cox = get_coxeter_reflection(divisor, curve)
        # cox = diag(-1, 1)

        monkeypatch.setattr(cls, "find_zero_vol_divisor", lambda *a: divisor.astype(float))

        # Need: symmetric flop conditions hold, but gv[0] < 0.
        # Symmetry: K000 - g3 = -K000 => g3 = 2*K000
        #           c2[0] + 2*g1 = -c2[0] => g1 = -c2[0]
        # Choose K000=3, c2[0]=0: g3=6, g1=0
        # gv_series: g0 + 2*g1_s = 0, g0 + 8*g1_s = 6
        # => g1_s=1, g0=-2. gv=[-2, 1, 0]. gv[0]<0!
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 3
        int_nums[0, 0, 1] = 2
        int_nums[0, 1, 0] = 2
        int_nums[1, 0, 0] = 2
        int_nums[1, 1, 1] = 4
        c2 = np.array([0, 44])
        gv_series = [-2, 1, 0]

        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.SU2

    def test_flop_with_zero_vol_non_symmetric(self, monkeypatch):
        """Zero-vol divisor exists but flop is not symmetric -> FLOP.

        Uses monkeypatch to inject a zero-vol divisor, then provides
        GV values that break the symmetry condition.
        """
        import cybir.core.classify as cls

        h11 = 2
        curve = np.array([1, 0])
        divisor = np.array([1, 0])

        monkeypatch.setattr(cls, "find_zero_vol_divisor", lambda *a: divisor.astype(float))

        # With cox=diag(-1,1), symmetry requires specific gv_eff values.
        # Use GV that break symmetry:
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6
        int_nums[1, 1, 1] = 4
        c2 = np.array([24, 44])
        gv_series = [3, 0]  # gv_eff_1=3, gv_eff_3=3; symmetry needs g3=12

        result = classify_contraction(int_nums, c2, curve, gv_series)
        assert result["contraction_type"] == ContractionType.FLOP
        assert result["zero_vol_divisor"] is not None

    def test_result_dict_keys(self):
        """Returned dict contains all required metadata keys."""
        int_nums = np.zeros((3, 3, 3))
        int_nums[0, 1, 2] = 1
        int_nums[0, 2, 1] = 1
        int_nums[1, 0, 2] = 1
        int_nums[2, 0, 1] = 1
        int_nums[1, 2, 0] = 1
        int_nums[2, 1, 0] = 1
        c2 = np.array([24, 44, 60])
        curve = np.array([1, 0, 0])
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

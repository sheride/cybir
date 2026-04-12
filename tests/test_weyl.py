"""Tests for Weyl expansion helper functions.

Tests _reflect_phase (int_nums and c2 transformations) and
_is_new_phase (Mori cone deduplication) without requiring CYTools.
"""

import numpy as np
import pytest

from cybir.core.weyl import _reflect_phase, _is_new_phase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class _MockPhase:
    """Minimal mock of CalabiYauLite for testing."""

    def __init__(self, int_nums, c2=None, kahler_cone=None, mori_cone=None, label=None):
        self._int_nums = np.asarray(int_nums)
        self._c2 = np.asarray(c2) if c2 is not None else None
        self._kahler_cone = kahler_cone
        self._mori_cone = mori_cone
        self._label = label

    @property
    def int_nums(self):
        return np.copy(self._int_nums)

    @property
    def c2(self):
        if self._c2 is not None:
            return np.copy(self._c2)
        return None

    @property
    def kahler_cone(self):
        return self._kahler_cone

    @property
    def mori_cone(self):
        return self._mori_cone

    @property
    def label(self):
        return self._label


class _MockCone:
    """Mock cone that returns fixed rays."""

    def __init__(self, rays_array):
        self._rays = np.asarray(rays_array)

    def rays(self):
        return self._rays.copy()


# ---------------------------------------------------------------------------
# _reflect_phase tests
# ---------------------------------------------------------------------------

class TestReflectPhase:
    """Test intersection number and c2 transformations."""

    def test_identity_reflection_preserves_data(self):
        """Identity reflection should leave int_nums and c2 unchanged."""
        h11 = 3
        int_nums = np.random.randint(-5, 5, size=(h11, h11, h11)).astype(float)
        # Make symmetric
        for i in range(h11):
            for j in range(h11):
                for k in range(h11):
                    val = int_nums[i, j, k]
                    int_nums[i, k, j] = val
                    int_nums[j, i, k] = val
                    int_nums[j, k, i] = val
                    int_nums[k, i, j] = val
                    int_nums[k, j, i] = val

        c2 = np.array([1.0, 2.0, 3.0])
        phase = _MockPhase(int_nums, c2=c2, label="CY_0")
        M = np.eye(h11)

        result = _reflect_phase(phase, M)

        np.testing.assert_allclose(result["int_nums"], int_nums)
        np.testing.assert_allclose(result["c2"], c2)

    def test_permutation_reflection(self):
        """Permutation matrix should permute int_nums indices and c2 entries."""
        h11 = 2
        int_nums = np.zeros((h11, h11, h11))
        int_nums[0, 0, 0] = 6.0
        int_nums[0, 0, 1] = 3.0
        int_nums[0, 1, 0] = 3.0
        int_nums[1, 0, 0] = 3.0
        int_nums[1, 1, 1] = 8.0
        int_nums[0, 1, 1] = 2.0
        int_nums[1, 0, 1] = 2.0
        int_nums[1, 1, 0] = 2.0

        c2 = np.array([10.0, 20.0])

        # Permutation matrix swapping indices 0 <-> 1
        P = np.array([[0.0, 1.0], [1.0, 0.0]])

        phase = _MockPhase(int_nums, c2=c2, label="CY_0")
        result = _reflect_phase(phase, P)

        # After swapping, kappa'[0,0,0] should be original kappa[1,1,1] = 8
        assert result["int_nums"][0, 0, 0] == pytest.approx(8.0)
        # kappa'[1,1,1] should be original kappa[0,0,0] = 6
        assert result["int_nums"][1, 1, 1] == pytest.approx(6.0)
        # c2 should be swapped
        np.testing.assert_allclose(result["c2"], [20.0, 10.0])

    def test_c2_none_handled(self):
        """Phase with c2=None should return c2=None in result."""
        h11 = 2
        int_nums = np.ones((h11, h11, h11))
        phase = _MockPhase(int_nums, c2=None, label="CY_0")
        M = np.eye(h11)

        result = _reflect_phase(phase, M)

        assert result["c2"] is None

    def test_no_kahler_cone_returns_none_cones(self):
        """Phase without Kahler cone should return None cones."""
        h11 = 2
        int_nums = np.ones((h11, h11, h11))
        c2 = np.array([1.0, 2.0])
        phase = _MockPhase(int_nums, c2=c2, label="CY_0")
        M = np.eye(h11)

        result = _reflect_phase(phase, M)

        assert result["kahler_cone"] is None
        assert result["mori_cone"] is None

    def test_dimension_mismatch_raises(self):
        """Reflection matrix with wrong shape should raise ValueError."""
        h11 = 3
        int_nums = np.ones((h11, h11, h11))
        phase = _MockPhase(int_nums, label="CY_0")
        M = np.eye(2)  # Wrong dimension

        with pytest.raises(ValueError, match="does not match h11"):
            _reflect_phase(phase, M)

    def test_einsum_matches_manual(self):
        """Verify einsum result matches manual index contraction."""
        h11 = 2
        int_nums = np.array([
            [[1.0, 2.0], [3.0, 4.0]],
            [[5.0, 6.0], [7.0, 8.0]],
        ])
        # Simple non-trivial reflection
        M = np.array([[1.0, 1.0], [0.0, 1.0]])

        phase = _MockPhase(int_nums, c2=np.array([1.0, 2.0]), label="CY_0")
        result = _reflect_phase(phase, M)

        # Manual computation
        expected = np.einsum("abc,xa,yb,zc", int_nums, M, M, M)
        np.testing.assert_allclose(result["int_nums"], expected)

        expected_c2 = np.einsum("a,xa", np.array([1.0, 2.0]), M)
        np.testing.assert_allclose(result["c2"], expected_c2)


# ---------------------------------------------------------------------------
# _is_new_phase tests
# ---------------------------------------------------------------------------

class TestIsNewPhase:
    """Test Mori cone deduplication."""

    def test_new_cone_is_detected(self):
        """A cone with distinct rays should be recognized as new."""
        existing = {frozenset({(1, 0), (0, 1)})}
        new_cone = _MockCone([[1, 1], [0, 1]])

        assert _is_new_phase(existing, new_cone) is True

    def test_existing_cone_is_rejected(self):
        """A cone with matching rays should be recognized as duplicate."""
        existing = {frozenset({(1, 0), (0, 1)})}
        dup_cone = _MockCone([[1, 0], [0, 1]])

        assert _is_new_phase(existing, dup_cone) is False

    def test_none_cone_is_rejected(self):
        """None Mori cone should always be rejected."""
        existing = set()
        assert _is_new_phase(existing, None) is False

    def test_ray_order_invariant(self):
        """Deduplication should be order-independent (frozenset)."""
        existing = {frozenset({(1, 0), (0, 1)})}
        # Same rays, different order
        reordered = _MockCone([[0, 1], [1, 0]])

        assert _is_new_phase(existing, reordered) is False

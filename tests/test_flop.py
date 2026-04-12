"""Tests for cybir.core.flop wall-crossing functions."""

import numpy as np
import pytest

from cybir.core.flop import flop_phase, wall_cross_c2, wall_cross_intnums
from cybir.core.types import CalabiYauLite


class TestWallCrossIntnums:
    """Tests for wall_cross_intnums."""

    def test_basic_transformation(self, sample_int_nums):
        """Subtracting gv_eff_3 * C_a C_b C_c from kappa_abc."""
        curve = np.array([1, 0])
        result = wall_cross_intnums(sample_int_nums, curve, gv_eff_3=1)
        expected = sample_int_nums.copy()
        expected[0, 0, 0] -= 1  # only (0,0,0) component affected
        np.testing.assert_array_equal(result, expected)

    def test_zero_gv_eff_3_unchanged(self, sample_int_nums):
        """gv_eff_3=0 returns unchanged intersection numbers."""
        curve = np.array([1, 0])
        result = wall_cross_intnums(sample_int_nums, curve, gv_eff_3=0)
        np.testing.assert_array_equal(result, sample_int_nums)

    def test_does_not_mutate_input(self, sample_int_nums):
        """Input array must not be modified."""
        original = sample_int_nums.copy()
        curve = np.array([1, 0])
        wall_cross_intnums(sample_int_nums, curve, gv_eff_3=1)
        np.testing.assert_array_equal(sample_int_nums, original)

    def test_multidirectional_curve(self, sample_int_nums):
        """Curve [1,1] affects multiple components."""
        curve = np.array([1, 1])
        result = wall_cross_intnums(sample_int_nums, curve, gv_eff_3=2)
        # einsum('a,b,c', [1,1], [1,1], [1,1]) = all-ones 2x2x2 tensor
        expected = sample_int_nums - 2 * np.ones((2, 2, 2), dtype=int)
        np.testing.assert_array_equal(result, expected)


class TestWallCrossC2:
    """Tests for wall_cross_c2."""

    def test_basic_transformation(self, sample_c2):
        """c'_a = c_a + 2 * gv_eff_1 * C_a."""
        curve = np.array([1, 0])
        result = wall_cross_c2(sample_c2, curve, gv_eff_1=3)
        expected = np.array([24 + 6, 44 + 0])
        np.testing.assert_array_equal(result, expected)

    def test_zero_gv_eff_1_unchanged(self, sample_c2):
        """gv_eff_1=0 returns unchanged c2."""
        curve = np.array([1, 0])
        result = wall_cross_c2(sample_c2, curve, gv_eff_1=0)
        np.testing.assert_array_equal(result, sample_c2)

    def test_does_not_mutate_input(self, sample_c2):
        """Input array must not be modified."""
        original = sample_c2.copy()
        curve = np.array([1, 0])
        wall_cross_c2(sample_c2, curve, gv_eff_1=3)
        np.testing.assert_array_equal(sample_c2, original)


class TestFlopPhase:
    """Tests for flop_phase."""

    def test_creates_new_calabi_yau_lite(self, sample_cyl):
        """flop_phase returns a new CalabiYauLite."""
        curve = np.array([1, 0])
        result = flop_phase(sample_cyl, curve, gv_series=[1, 0, 0])
        assert isinstance(result, CalabiYauLite)
        assert result is not sample_cyl

    def test_transforms_int_nums(self, sample_cyl):
        """Int nums are transformed by wall-crossing formula."""
        curve = np.array([1, 0])
        # gv_series=[1,0,0] -> gv_eff_3 = 1*1 + 8*0 + 27*0 = 1
        result = flop_phase(sample_cyl, curve, gv_series=[1, 0, 0])
        expected_int_nums = sample_cyl.int_nums.copy()
        expected_int_nums[0, 0, 0] -= 1
        np.testing.assert_array_equal(result.int_nums, expected_int_nums)

    def test_transforms_c2(self, sample_cyl):
        """c2 is transformed by wall-crossing formula."""
        curve = np.array([1, 0])
        # gv_series=[1,0,0] -> gv_eff_1 = 1*1 + 2*0 + 3*0 = 1
        result = flop_phase(sample_cyl, curve, gv_series=[1, 0, 0])
        expected_c2 = np.array([24 + 2, 44])  # c2 + 2 * 1 * [1,0]
        np.testing.assert_array_equal(result.c2, expected_c2)

    def test_gv_invariants_is_none(self, sample_cyl):
        """Flopped phase should not have gv_invariants set."""
        curve = np.array([1, 0])
        result = flop_phase(sample_cyl, curve, gv_series=[1, 0, 0])
        assert result.gv_invariants is None

    def test_label_passed_through(self, sample_cyl):
        """Label is passed to the new CalabiYauLite."""
        curve = np.array([1, 0])
        result = flop_phase(
            sample_cyl, curve, gv_series=[1, 0, 0], label="phase_1"
        )
        assert result.label == "phase_1"

    def test_cones_not_copied(self, sample_cyl):
        """Flopped phase should not copy cones (they change under flop)."""
        curve = np.array([1, 0])
        result = flop_phase(sample_cyl, curve, gv_series=[1, 0, 0])
        assert result.kahler_cone is None
        assert result.mori_cone is None

    def test_c2_none_handled(self, sample_int_nums):
        """flop_phase works when c2 is None."""
        cyl_no_c2 = CalabiYauLite(int_nums=sample_int_nums, c2=None)
        curve = np.array([1, 0])
        result = flop_phase(cyl_no_c2, curve, gv_series=[1, 0, 0])
        assert result.c2 is None

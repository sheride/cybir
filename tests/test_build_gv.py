"""Tests for BFS builder helper functions.

Tests the helper functions in ``cybir.core.build_gv`` that support
the BFS construction loop. Does NOT test the full BFS loop (that
requires CYTools runtime) -- only unit tests for helpers.
"""

import numpy as np
import pytest

from cybir.core.build_gv import (
    _accumulate_generators,
    _compute_tip,
    _find_matching_phase,
    _update_all_curve_signs,
)
from cybir.core.types import CalabiYauLite, ContractionType


# ---------------------------------------------------------------------------
# _find_matching_phase
# ---------------------------------------------------------------------------


class TestFindMatchingPhase:
    """Tests for curve-sign dictionary matching."""

    def test_finds_exact_match(self):
        curve_signs = {
            "CY_0": {(1, 0): 1, (0, 1): -1},
            "CY_1": {(1, 0): -1, (0, 1): 1},
        }
        target = {(1, 0): -1, (0, 1): 1}
        assert _find_matching_phase(curve_signs, target) == "CY_1"

    def test_returns_none_for_no_match(self):
        curve_signs = {
            "CY_0": {(1, 0): 1, (0, 1): -1},
            "CY_1": {(1, 0): -1, (0, 1): 1},
        }
        target = {(1, 0): 1, (0, 1): 1}
        assert _find_matching_phase(curve_signs, target) is None

    def test_empty_curve_signs(self):
        assert _find_matching_phase({}, {(1, 0): 1}) is None

    def test_single_curve(self):
        curve_signs = {"CY_0": {(1,): 1}}
        assert _find_matching_phase(curve_signs, {(1,): 1}) == "CY_0"
        assert _find_matching_phase(curve_signs, {(1,): -1}) is None

    def test_multiple_matches_returns_first(self):
        """If multiple phases match, returns one of them (first found)."""
        curve_signs = {
            "CY_0": {(1, 0): 1},
            "CY_1": {(1, 0): 1},
        }
        result = _find_matching_phase(curve_signs, {(1, 0): 1})
        assert result in ("CY_0", "CY_1")


# ---------------------------------------------------------------------------
# _update_all_curve_signs
# ---------------------------------------------------------------------------


class TestUpdateAllCurveSigns:
    """Tests for global curve-sign update."""

    def test_updates_all_phases(self):
        """When a new curve is added, all phases get a new entry."""
        # Mock ekc (not used by this function directly)

        curve_signs = {
            "CY_0": {(1, 0): 1},
            "CY_1": {(1, 0): -1},
        }
        tips = {
            "CY_0": np.array([1.0, 2.0]),
            "CY_1": np.array([-1.0, 3.0]),
        }
        new_curve = (0, 1)

        _update_all_curve_signs(None, curve_signs, new_curve, tips)

        # CY_0: tip=[1,2], curve=[0,1] -> sign(2) = +1
        assert curve_signs["CY_0"][(0, 1)] == 1
        # CY_1: tip=[-1,3], curve=[0,1] -> sign(3) = +1
        assert curve_signs["CY_1"][(0, 1)] == 1

    def test_negative_sign(self):
        curve_signs = {"CY_0": {}}
        tips = {"CY_0": np.array([-1.0, -2.0])}
        new_curve = (1, 0)

        _update_all_curve_signs(None, curve_signs, new_curve, tips)
        assert curve_signs["CY_0"][(1, 0)] == -1

    def test_zero_sign(self):
        """Zero dot product gives sign 0."""
        curve_signs = {"CY_0": {}}
        tips = {"CY_0": np.array([0.0, 1.0])}
        new_curve = (1, 0)

        _update_all_curve_signs(None, curve_signs, new_curve, tips)
        assert curve_signs["CY_0"][(1, 0)] == 0


# ---------------------------------------------------------------------------
# _accumulate_generators
# ---------------------------------------------------------------------------


class MockEKC:
    """Minimal mock of CYBirationalClass for testing accumulation."""

    def __init__(self):
        self._coxeter_refs = set()
        self._sym_flop_refs = set()
        self._sym_flop_pairs = []
        self._infinity_cone_gens = set()
        self._eff_cone_gens = set()


class TestAccumulateGenerators:
    """Tests for generator accumulation."""

    def test_asymptotic_adds_infinity_gen(self):
        ekc = MockEKC()
        result = {
            "contraction_curve": (1, 0, 0),
            "zero_vol_divisor": None,
            "coxeter_reflection": None,
        }
        _accumulate_generators(ekc, ContractionType.ASYMPTOTIC, result)
        assert (1, 0, 0) in ekc._infinity_cone_gens

    def test_cft_adds_infinity_and_eff_gens(self):
        ekc = MockEKC()
        result = {
            "contraction_curve": (1, 0, 0),
            "zero_vol_divisor": np.array([0, 1, 0]),
            "coxeter_reflection": None,
        }
        _accumulate_generators(ekc, ContractionType.CFT, result)
        assert (1, 0, 0) in ekc._infinity_cone_gens
        assert (0, 1, 0) in ekc._eff_cone_gens

    def test_su2_adds_eff_gen_and_coxeter_ref(self):
        ekc = MockEKC()
        M = np.eye(3)
        M[0, 1] = -2
        result = {
            "contraction_curve": (1, 0, 0),
            "zero_vol_divisor": np.array([0, 1, 0]),
            "coxeter_reflection": M,
        }
        _accumulate_generators(ekc, ContractionType.SU2, result)
        assert (0, 1, 0) in ekc._eff_cone_gens
        assert len(ekc._coxeter_refs) == 1
        assert len(ekc._sym_flop_refs) == 0

    def test_symmetric_flop_adds_coxeter_and_sym_flop_ref(self):
        ekc = MockEKC()
        M = np.eye(3)
        M[0, 1] = -2
        result = {
            "contraction_curve": (1, 0, 0),
            "zero_vol_divisor": None,
            "coxeter_reflection": M,
        }
        _accumulate_generators(ekc, ContractionType.SYMMETRIC_FLOP, result)
        assert len(ekc._coxeter_refs) == 1
        assert len(ekc._sym_flop_refs) == 1

    def test_generic_flop_adds_nothing(self):
        ekc = MockEKC()
        result = {
            "contraction_curve": (1, 0, 0),
            "zero_vol_divisor": None,
            "coxeter_reflection": None,
        }
        _accumulate_generators(ekc, ContractionType.FLOP, result)
        assert len(ekc._infinity_cone_gens) == 0
        assert len(ekc._eff_cone_gens) == 0
        assert len(ekc._coxeter_refs) == 0
        assert len(ekc._sym_flop_refs) == 0


# ---------------------------------------------------------------------------
# _compute_tip
# ---------------------------------------------------------------------------


class TestComputeTip:
    """Tests for Kahler cone tip computation."""

    def test_raises_on_no_kahler_cone(self):
        phase = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label="test")
        with pytest.raises(RuntimeError, match="no Kahler cone"):
            _compute_tip(phase)

    def test_works_with_simple_cone(self):
        """Use a cytools Cone if available, otherwise skip."""
        try:
            import cytools
        except ImportError:
            pytest.skip("CYTools not available")

        cone = cytools.Cone(rays=[[1, 0], [0, 1]])
        phase = CalabiYauLite(
            int_nums=np.zeros((2, 2, 2)),
            kahler_cone=cone,
            label="test",
        )
        tip = _compute_tip(phase)
        assert tip is not None
        assert len(tip) == 2
        # Tip should be in the interior (all positive for this cone)
        assert np.all(tip > 0)


# ---------------------------------------------------------------------------
# Import tests
# ---------------------------------------------------------------------------


class TestImports:
    """Verify that the module imports and has expected functions."""

    def test_setup_root_importable(self):
        from cybir.core.build_gv import setup_root
        assert callable(setup_root)

    def test_construct_phases_importable(self):
        from cybir.core.build_gv import construct_phases
        assert callable(construct_phases)

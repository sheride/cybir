"""Tests for cybir.core.types -- CalabiYauLite, ExtremalContraction,
ContractionType, and InsufficientGVError."""

import numpy as np
import pytest

from cybir.core.types import (
    CalabiYauLite,
    ContractionType,
    ExtremalContraction,
    InsufficientGVError,
)


# ============================================================
# CalabiYauLite
# ============================================================


class TestCalabiYauLiteConstruction:
    """Test CalabiYauLite instantiation and property access."""

    def test_minimal_construction(self):
        """CalabiYauLite can be created with only int_nums."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        assert cyl.int_nums is not None
        assert cyl.int_nums.shape == (2, 2, 2)

    def test_int_nums_returns_copy(self):
        """Returned int_nums is a copy -- modifying it does not change internal state."""
        original = np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])
        cyl = CalabiYauLite(int_nums=original)
        returned = cyl.int_nums
        returned[0, 0, 0] = 999
        assert cyl.int_nums[0, 0, 0] == 0

    def test_c2_returns_copy(self):
        """Returned c2 is a copy -- modifying it does not change internal state."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), c2=np.array([24, 44]))
        returned = cyl.c2
        returned[0] = 999
        assert cyl.c2[0] == 24

    def test_all_optional_fields(self):
        """All optional fields are accessible and default to None."""
        cyl = CalabiYauLite(
            int_nums=np.zeros((2, 2, 2)),
            c2=np.array([24, 44]),
            kahler_cone="kc",
            mori_cone="mc",
            polytope="poly",
            charges="charges",
            indices="indices",
            eff_cone="ec",
            triangulation="triang",
            fan="fan",
            gv_invariants="gv",
            label="phase_0",
        )
        assert np.allclose(cyl.c2, np.array([24, 44]))
        assert cyl.kahler_cone == "kc"
        assert cyl.mori_cone == "mc"
        assert cyl.polytope == "poly"
        assert cyl.charges == "charges"
        assert cyl.indices == "indices"
        assert cyl.eff_cone == "ec"
        assert cyl.triangulation == "triang"
        assert cyl.fan == "fan"
        assert cyl.gv_invariants == "gv"
        assert cyl.label == "phase_0"

    def test_optional_fields_default_none(self):
        """Unset optional fields return None."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        assert cyl.c2 is None
        assert cyl.kahler_cone is None
        assert cyl.mori_cone is None
        assert cyl.polytope is None
        assert cyl.charges is None
        assert cyl.indices is None
        assert cyl.eff_cone is None
        assert cyl.triangulation is None
        assert cyl.fan is None
        assert cyl.gv_invariants is None
        assert cyl.label is None


class TestCalabiYauLiteFreeze:
    """Test freeze / immutability mechanism."""

    def test_mutable_before_freeze(self):
        """Before freeze, setting private attributes directly works."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl._int_nums = np.ones((2, 2, 2))
        assert np.allclose(cyl.int_nums, np.ones((2, 2, 2)))

    def test_freeze_prevents_modification(self):
        """After freeze(), setting any attribute raises AttributeError."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl.freeze()
        with pytest.raises(AttributeError, match="frozen"):
            cyl._int_nums = np.ones((2, 2, 2))

    def test_freeze_prevents_new_attributes(self):
        """After freeze(), adding new attributes raises AttributeError."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl.freeze()
        with pytest.raises(AttributeError, match="frozen"):
            cyl._new_attr = "test"


class TestCalabiYauLiteEquality:
    """Test __eq__ and __hash__."""

    def test_equal_same_int_nums(self):
        """Two CalabiYauLite with same int_nums are equal."""
        a = CalabiYauLite(int_nums=np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]))
        b = CalabiYauLite(int_nums=np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]]))
        assert a == b

    def test_not_equal_different_int_nums(self):
        """Two CalabiYauLite with different int_nums are not equal."""
        a = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        b = CalabiYauLite(int_nums=np.ones((2, 2, 2)))
        assert a != b

    def test_not_equal_different_c2(self):
        """Two CalabiYauLite with same int_nums but different c2 are not equal."""
        nums = np.zeros((2, 2, 2))
        a = CalabiYauLite(int_nums=nums, c2=np.array([24, 44]))
        b = CalabiYauLite(int_nums=nums, c2=np.array([24, 50]))
        assert a != b

    def test_equal_not_implemented_for_other_types(self):
        """Comparing with non-CalabiYauLite returns NotImplemented."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        assert cyl.__eq__("not a cyl") is NotImplemented

    def test_hash_uses_label(self):
        """__hash__ returns hash of label."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label="phase_0")
        assert hash(cyl) == hash("phase_0")

    def test_hash_same_label(self):
        """Two objects with same label have same hash."""
        a = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label="phase_0")
        b = CalabiYauLite(int_nums=np.ones((2, 2, 2)), label="phase_0")
        assert hash(a) == hash(b)


class TestCalabiYauLiteRepr:
    """Test __repr__ and __str__."""

    def test_repr_includes_class_name_and_label(self):
        """__repr__ includes CalabiYauLite and the label."""
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label="phase_0")
        r = repr(cyl)
        assert "CalabiYauLite" in r
        assert "phase_0" in r

    def test_repr_small_h11_shows_details(self):
        """For h11<=3, repr shows intersection numbers and c2."""
        int_nums = np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])
        cyl = CalabiYauLite(int_nums=int_nums, c2=np.array([24, 44]), label="CY_0")
        r = repr(cyl)
        assert "kappa=" in r
        assert "c2=" in r
        assert "24" in r
        assert "44" in r

    def test_repr_large_h11_shows_short_form(self):
        """For h11>3, repr shows only label and h11."""
        cyl = CalabiYauLite(int_nums=np.zeros((5, 5, 5)), label="CY_big")
        r = repr(cyl)
        assert "h11=5" in r
        assert "kappa=" not in r

    def test_str_always_shows_details(self):
        """__str__ shows full details regardless of h11."""
        cyl = CalabiYauLite(
            int_nums=np.zeros((5, 5, 5)), c2=np.ones(5), label="CY_big"
        )
        s = str(cyl)
        assert "kappa=" in s
        assert "c2=" in s


# ============================================================
# ExtremalContraction
# ============================================================


class TestExtremalContractionConstruction:
    """Test ExtremalContraction instantiation and frozen-by-default."""

    def test_minimal_construction(self):
        """ExtremalContraction can be created with only contraction_curve."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        assert np.array_equal(ec.contraction_curve, np.array([1, 0]))

    def test_optional_fields_default_none(self):
        """All optional fields default to None."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        assert ec.contraction_type is None
        assert ec.gv_invariant is None
        assert ec.effective_gv is None
        assert ec.zero_vol_divisor is None
        assert ec.coxeter_reflection is None
        assert ec.cone_face is None

    def test_frozen_by_default(self):
        """ExtremalContraction is frozen immediately after construction."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        with pytest.raises(AttributeError, match="frozen"):
            ec._contraction_curve = np.array([0, 1])

    def test_frozen_prevents_new_attributes(self):
        """Cannot add new attributes after construction."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        with pytest.raises(AttributeError, match="frozen"):
            ec._new_attr = "test"


class TestExtremalContractionGVFields:
    """Test gv_series and gv_eff_1 fields."""

    def test_construction_with_gv_series_and_gv_eff_1(self):
        """ExtremalContraction can be constructed with gv_series and gv_eff_1."""
        ec = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            gv_series=[1, 0, 0],
            gv_eff_1=5,
        )
        assert ec.gv_series == [1, 0, 0]
        assert ec.gv_eff_1 == 5

    def test_gv_series_returns_defensive_copy(self):
        """Mutating the returned gv_series does not affect the object."""
        ec = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            gv_series=[1, 0, 0],
        )
        returned = ec.gv_series
        returned[0] = 999
        assert ec.gv_series == [1, 0, 0]

    def test_gv_series_defaults_to_none(self):
        """gv_series defaults to None when not provided."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        assert ec.gv_series is None

    def test_gv_eff_1_defaults_to_none(self):
        """gv_eff_1 defaults to None when not provided."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        assert ec.gv_eff_1 is None


class TestExtremalContractionRepr:
    """Test __repr__."""

    def test_repr_includes_type_display_name(self):
        """__repr__ shows type display name (paper notation)."""
        ec = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            contraction_type=ContractionType.FLOP,
        )
        r = repr(ec)
        assert "generic flop" in r

    def test_repr_includes_curve_as_list(self):
        """__repr__ shows curve as list of ints."""
        ec = ExtremalContraction(
            contraction_curve=np.array([0, 1, -1]),
            contraction_type=ContractionType.SYMMETRIC_FLOP,
        )
        r = repr(ec)
        assert "curve=[0, 1, -1]" in r
        assert "symmetric flop" in r

    def test_repr_includes_zvd(self):
        """__repr__ shows zero_vol_divisor when present."""
        ec = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            contraction_type=ContractionType.CFT,
            zero_vol_divisor=np.array([0, 1]),
        )
        r = repr(ec)
        assert "zvd=[0, 1]" in r

    def test_repr_includes_gv_series(self):
        """__repr__ shows gv_series for small h11 (short curve)."""
        ec = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            contraction_type=ContractionType.FLOP,
            gv_series=[480, 480, 1054],
        )
        r = repr(ec)
        assert "gv=[480, 480, 1054]" in r

    def test_repr_unclassified(self):
        """__repr__ shows 'unclassified' when type is None."""
        ec = ExtremalContraction(contraction_curve=np.array([1, 0]))
        r = repr(ec)
        assert "unclassified" in r


# ============================================================
# ContractionType
# ============================================================


class TestContractionType:
    """Test ContractionType enum."""

    def test_exactly_6_members(self):
        """ContractionType has exactly 6 members."""
        assert len(ContractionType) == 6

    def test_values(self):
        """Enum values match expected strings."""
        assert ContractionType.ASYMPTOTIC.value == "asymptotic"
        assert ContractionType.CFT.value == "CFT"
        assert ContractionType.SU2.value == "su2"
        assert ContractionType.SU2_NONGENERIC_CS.value == "su2_nongeneric_cs"
        assert ContractionType.SYMMETRIC_FLOP.value == "symmetric_flop"
        assert ContractionType.FLOP.value == "flop"

    def test_display_name_paper_notation(self):
        """Paper notation display names are correct."""
        assert ContractionType.FLOP.display_name("paper") == "generic flop"
        assert ContractionType.SU2.display_name("paper") == "su(2) enhancement"
        assert ContractionType.SU2_NONGENERIC_CS.display_name("paper") == "su(2) enhancement (non-generic CS)"
        assert ContractionType.SYMMETRIC_FLOP.display_name("paper") == "symmetric flop"
        assert ContractionType.CFT.display_name("paper") == "CFT"
        assert ContractionType.ASYMPTOTIC.display_name("paper") == "asymptotic"

    def test_display_name_wilson_notation(self):
        """Wilson notation display names are correct."""
        assert ContractionType.FLOP.display_name("wilson") == "Flop"
        assert ContractionType.SU2.display_name("wilson") == "Type I"
        assert ContractionType.SU2_NONGENERIC_CS.display_name("wilson") == "Type I (non-generic CS)"
        assert ContractionType.CFT.display_name("wilson") == "Type II"
        assert ContractionType.ASYMPTOTIC.display_name("wilson") == "Type III"
        assert ContractionType.SYMMETRIC_FLOP.display_name("wilson") == "Symmetric Flop"

    def test_display_name_default_is_paper(self):
        """Default notation (no arg) returns paper notation."""
        assert ContractionType.FLOP.display_name() == "generic flop"
        assert ContractionType.ASYMPTOTIC.display_name() == "asymptotic"

    def test_su2_nongeneric_cs_enum(self):
        """SU2_NONGENERIC_CS exists and has correct display names."""
        ct = ContractionType.SU2_NONGENERIC_CS
        assert ct.value == "su2_nongeneric_cs"
        assert ct.display_name("paper") == "su(2) enhancement (non-generic CS)"
        assert ct.display_name("wilson") == "Type I (non-generic CS)"


# ============================================================
# InsufficientGVError
# ============================================================


class TestInsufficientGVError:
    """Test InsufficientGVError exception."""

    def test_is_runtime_error_subclass(self):
        """InsufficientGVError is a subclass of RuntimeError."""
        assert issubclass(InsufficientGVError, RuntimeError)

    def test_stores_message(self):
        """InsufficientGVError stores message correctly."""
        err = InsufficientGVError("need more GV data")
        assert str(err) == "need more GV data"

    def test_isinstance_check(self):
        """isinstance check against RuntimeError works."""
        err = InsufficientGVError("x")
        assert isinstance(err, RuntimeError)


# ============================================================
# Fixture-based tests
# ============================================================


class TestConfestFixtures:
    """Test that conftest fixtures work correctly with the types."""

    def test_sample_cyl_construction(self, sample_cyl):
        """sample_cyl fixture creates a valid CalabiYauLite."""
        assert sample_cyl.label == "phase_0"
        assert sample_cyl.int_nums.shape == (2, 2, 2)
        assert np.allclose(sample_cyl.c2, np.array([24, 44]))

    def test_sample_cyl_not_frozen(self, sample_cyl):
        """sample_cyl is not frozen by default."""
        sample_cyl._label = "modified"
        assert sample_cyl.label == "modified"

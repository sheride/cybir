"""Tests for cybir.core.coxeter -- Coxeter group construction and BFS enumeration.

Tests the full chain: matrix_period -> coxeter_reflection -> coxeter_order_matrix
-> bilinear form -> finite type check -> classification -> group order -> BFS enumeration.

Uses concrete A_2 and B_2 reflection matrices as fixtures.
"""

import logging
import warnings

import numpy as np
import pytest

from cybir.core.coxeter import (
    _classify_irreducible,
    _decompose_irreducible,
    _matrix_key,
    classify_coxeter_type,
    coxeter_bilinear_form,
    coxeter_element,
    coxeter_order_matrix,
    coxeter_reflection,
    enumerate_coxeter_group,
    is_finite_type,
    matrix_period,
    coxeter_group_order,
)


# ============================================================
# Fixtures: known reflection matrices
# ============================================================

@pytest.fixture
def a2_reflections():
    """A_2 simple reflections in R^2.

    M1 = [[-1, 1], [0, 1]], M2 = [[1, 0], [1, -1]]
    Product M1 @ M2 has order 3, |W(A_2)| = 6.
    """
    M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
    M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
    return [M1, M2]


@pytest.fixture
def b2_reflections():
    """B_2 simple reflections in R^2 (from B_2 Cartan matrix).

    M1 = [[-1, 0], [1, 1]], M2 = [[1, 2], [0, -1]]
    Product M1 @ M2 has order 4, |W(B_2)| = 8.
    """
    M1 = np.array([[-1, 0], [1, 1]], dtype=np.int64)
    M2 = np.array([[1, 2], [0, -1]], dtype=np.int64)
    return [M1, M2]


@pytest.fixture
def a1xa1_reflections():
    """A_1 x A_1: two commuting reflections.

    M1 = [[-1, 0], [0, 1]], M2 = [[1, 0], [0, -1]]
    Product M1 @ M2 has order 2, |W| = 4.
    """
    M1 = np.array([[-1, 0], [0, 1]], dtype=np.int64)
    M2 = np.array([[1, 0], [0, -1]], dtype=np.int64)
    return [M1, M2]


# ============================================================
# matrix_period tests
# ============================================================

class TestMatrixPeriod:
    """Test matrix_period function."""

    def test_identity_period_is_1(self):
        """Identity matrix has period 1."""
        I = np.eye(2, dtype=np.int64)
        assert matrix_period(I) == 1

    def test_negation_period_is_2(self):
        """Negative identity has period 2."""
        neg_I = -np.eye(2, dtype=np.int64)
        assert matrix_period(neg_I) == 2

    def test_a2_product_order_3(self, a2_reflections):
        """Product of A_2 reflections has order 3."""
        M1, M2 = a2_reflections
        product = M1 @ M2
        assert matrix_period(product) == 3

    def test_b2_product_order_4(self, b2_reflections):
        """Product of B_2 reflections has order 4."""
        M1, M2 = b2_reflections
        product = M1 @ M2
        assert matrix_period(product) == 4

    def test_reflection_period_is_2(self, a2_reflections):
        """Each individual reflection has period 2."""
        for M in a2_reflections:
            assert matrix_period(M) == 2

    def test_max_iter_raises(self):
        """Raises ValueError when period exceeds max_iter."""
        # Rotation by irrational angle has no finite period
        # Use a finite but large period matrix
        # 3x3 permutation with period > 3
        M = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], dtype=np.int64)  # period 3
        # Should succeed with max_iter=3
        assert matrix_period(M, max_iter=3) == 3
        # Should fail with max_iter=2
        with pytest.raises(ValueError, match="does not return to identity"):
            matrix_period(M, max_iter=2)

    def test_int64_arithmetic(self, a2_reflections):
        """matrix_period uses integer arithmetic (no float drift)."""
        M1, M2 = a2_reflections
        product = M1 @ M2
        # Should work with exact integer comparison
        assert matrix_period(product) == 3


# ============================================================
# coxeter_reflection tests
# ============================================================

class TestCoxeterReflection:
    """Test coxeter_reflection function."""

    def test_reflects_curve_to_negative(self):
        """M @ curve == -curve."""
        div = np.array([1.0, 0.0])
        curve = np.array([1.0, 0.0])
        M = coxeter_reflection(div, curve)
        result = M @ curve
        np.testing.assert_allclose(result, -curve)

    def test_involutory(self):
        """M^2 == I for any reflection."""
        div = np.array([1.0, 2.0])
        curve = np.array([3.0, 1.0])
        M = coxeter_reflection(div, curve)
        np.testing.assert_allclose(M @ M, np.eye(2), atol=1e-12)

    def test_identity_when_dot_zero(self):
        """Returns identity when curve . divisor == 0."""
        div = np.array([0.0, 1.0])
        curve = np.array([1.0, 0.0])
        M = coxeter_reflection(div, curve)
        np.testing.assert_allclose(M, np.eye(2))


# ============================================================
# coxeter_element tests
# ============================================================

class TestCoxeterElement:
    """Test coxeter_element (renamed from coxeter_matrix)."""

    def test_product_of_two(self, a2_reflections):
        """coxeter_element returns M1 @ M2."""
        M1, M2 = a2_reflections
        C = coxeter_element(a2_reflections)
        np.testing.assert_array_equal(C, M1 @ M2)

    def test_empty_raises(self):
        """Empty reflections list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot compute"):
            coxeter_element([])

    def test_deprecated_alias_via_util(self):
        """coxeter_matrix via util.py delegates to coxeter_element."""
        from cybir.core.util import coxeter_matrix
        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = coxeter_matrix([M1, M2])
        np.testing.assert_array_equal(result, M1 @ M2)


# ============================================================
# coxeter_order_matrix tests
# ============================================================

class TestCoxeterOrderMatrix:
    """Test coxeter_order_matrix computation."""

    def test_a2_order_matrix(self, a2_reflections):
        """A_2 order matrix is [[1, 3], [3, 1]]."""
        om = coxeter_order_matrix(a2_reflections)
        expected = np.array([[1, 3], [3, 1]])
        np.testing.assert_array_equal(om, expected)

    def test_b2_order_matrix(self, b2_reflections):
        """B_2 order matrix is [[1, 4], [4, 1]]."""
        om = coxeter_order_matrix(b2_reflections)
        expected = np.array([[1, 4], [4, 1]])
        np.testing.assert_array_equal(om, expected)

    def test_a1xa1_order_matrix(self, a1xa1_reflections):
        """A_1 x A_1 order matrix is [[1, 2], [2, 1]]."""
        om = coxeter_order_matrix(a1xa1_reflections)
        expected = np.array([[1, 2], [2, 1]])
        np.testing.assert_array_equal(om, expected)

    def test_diagonal_is_1(self, a2_reflections):
        """Diagonal entries are all 1."""
        om = coxeter_order_matrix(a2_reflections)
        np.testing.assert_array_equal(np.diag(om), np.ones(2))

    def test_symmetric(self, a2_reflections):
        """Order matrix is symmetric."""
        om = coxeter_order_matrix(a2_reflections)
        np.testing.assert_array_equal(om, om.T)


# ============================================================
# coxeter_bilinear_form tests
# ============================================================

class TestCoxeterBilinearForm:
    """Test coxeter_bilinear_form computation."""

    def test_a2_bilinear_form(self):
        """A_2 bilinear form: B_ii = -cos(pi/1) = 1, B_12 = -cos(pi/3) = -0.5."""
        om = np.array([[1, 3], [3, 1]])
        B = coxeter_bilinear_form(om)
        np.testing.assert_allclose(B[0, 0], 1.0)
        np.testing.assert_allclose(B[0, 1], -0.5, atol=1e-14)

    def test_b2_bilinear_form(self):
        """B_2 bilinear form: B_12 = -cos(pi/4) = -sqrt(2)/2."""
        om = np.array([[1, 4], [4, 1]])
        B = coxeter_bilinear_form(om)
        np.testing.assert_allclose(B[0, 1], -np.sqrt(2) / 2, atol=1e-14)


# ============================================================
# is_finite_type tests
# ============================================================

class TestIsFiniteType:
    """Test is_finite_type detection."""

    def test_a2_is_finite(self):
        """A_2 is finite type."""
        om = np.array([[1, 3], [3, 1]])
        assert is_finite_type(om) is True

    def test_b2_is_finite(self):
        """B_2 is finite type."""
        om = np.array([[1, 4], [4, 1]])
        assert is_finite_type(om) is True

    def test_affine_is_infinite(self):
        """Affine A_1 (m=infinity, order_matrix entry=0 for infinity) is infinite."""
        # For affine: use m_ij = 0 to represent infinity
        # B_ij = -cos(pi/0) is undefined; but we use m_ij large or 0
        # In practice, infinite order means the bilinear form is NOT positive definite
        # Use the affine A_2 Coxeter matrix (3 generators, all m_ij = 3, triangular graph)
        # Actually, affine A_2 has m_12=m_23=m_13=3, which has det(B)=0
        om = np.array([[1, 3, 3], [3, 1, 3], [3, 3, 1]])
        assert is_finite_type(om) is False


# ============================================================
# classify_coxeter_type tests
# ============================================================

class TestClassifyCoxeterType:
    """Test classify_coxeter_type function."""

    def test_a2_classification(self):
        """A_2 is classified correctly."""
        om = np.array([[1, 3], [3, 1]])
        types = classify_coxeter_type(om)
        assert len(types) == 1
        assert types[0][0] == "A"
        assert types[0][1] == 2

    def test_b2_classification(self):
        """B_2 is classified correctly."""
        om = np.array([[1, 4], [4, 1]])
        types = classify_coxeter_type(om)
        assert len(types) == 1
        assert types[0][0] == "B"
        assert types[0][1] == 2

    def test_a1xa1_classification(self):
        """A_1 x A_1 decomposes into two A_1 components."""
        om = np.array([[1, 2], [2, 1]])
        types = classify_coxeter_type(om)
        assert len(types) == 2
        for t in types:
            assert t[0] == "A"
            assert t[1] == 1

    def test_g2_classification(self):
        """G_2 (m=6) is classified correctly."""
        om = np.array([[1, 6], [6, 1]])
        types = classify_coxeter_type(om)
        assert len(types) == 1
        assert types[0][0] == "G"
        assert types[0][1] == 2

    def test_i2_5_classification(self):
        """I_2(5) is classified correctly."""
        om = np.array([[1, 5], [5, 1]])
        types = classify_coxeter_type(om)
        assert len(types) == 1
        assert types[0][0] == "I"
        assert types[0][1] == 2


# ============================================================
# coxeter_group_order tests
# ============================================================

class TestCoxeterGroupOrder:
    """Test coxeter_group_order function."""

    def test_a2_order_6(self):
        """A_2 group has order 6."""
        types = [("A", 2, 6)]
        assert coxeter_group_order(types) == 6

    def test_b2_order_8(self):
        """B_2 group has order 8."""
        types = [("B", 2, 8)]
        assert coxeter_group_order(types) == 8

    def test_a1xa1_order_4(self):
        """A_1 x A_1 has order 4."""
        types = [("A", 1, 2), ("A", 1, 2)]
        assert coxeter_group_order(types) == 4

    def test_d4_order_192(self):
        """D_4 has order 192."""
        types = [("D", 4, 192)]
        assert coxeter_group_order(types) == 192


# ============================================================
# enumerate_coxeter_group tests
# ============================================================

class TestEnumerateCoxeterGroup:
    """Test BFS enumeration of Coxeter group."""

    def test_a2_yields_6_elements(self, a2_reflections):
        """A_2 Coxeter group has exactly 6 elements."""
        elements = list(enumerate_coxeter_group(a2_reflections, expected_order=6))
        assert len(elements) == 6

    def test_b2_yields_8_elements(self, b2_reflections):
        """B_2 Coxeter group has exactly 8 elements."""
        elements = list(enumerate_coxeter_group(b2_reflections, expected_order=8))
        assert len(elements) == 8

    def test_a1xa1_yields_4_elements(self, a1xa1_reflections):
        """A_1 x A_1 Coxeter group has exactly 4 elements."""
        elements = list(enumerate_coxeter_group(a1xa1_reflections, expected_order=4))
        assert len(elements) == 4

    def test_identity_first(self, a2_reflections):
        """First yielded element is the identity."""
        elements = list(enumerate_coxeter_group(a2_reflections))
        np.testing.assert_array_equal(elements[0], np.eye(2, dtype=np.int64))

    def test_all_int64(self, a2_reflections):
        """All BFS elements are int64 matrices."""
        for g in enumerate_coxeter_group(a2_reflections):
            assert g.dtype == np.int64, f"Expected int64, got {g.dtype}"

    def test_all_unique(self, a2_reflections):
        """All yielded elements are distinct."""
        elements = list(enumerate_coxeter_group(a2_reflections))
        keys = [_matrix_key(g) for g in elements]
        assert len(set(keys)) == len(keys)

    def test_memory_warning(self, a2_reflections, caplog):
        """Large expected_order triggers memory warning."""
        # Set very low memory cap to trigger warning
        with caplog.at_level(logging.WARNING, logger="cybir"):
            list(enumerate_coxeter_group(
                a2_reflections, expected_order=10**9, max_memory_bytes=100
            ))
        assert any("memory" in r.message.lower() or "Memory" in r.message for r in caplog.records)


# ============================================================
# Deprecation re-exports from util.py
# ============================================================

class TestDeprecationReexports:
    """Test that util.py re-exports with deprecation warnings."""

    def test_matrix_period_deprecation(self):
        """Importing matrix_period from util emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from cybir.core.util import matrix_period as mp_util
            result = mp_util(np.eye(2))
            assert result == 1
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_coxeter_reflection_deprecation(self):
        """Importing coxeter_reflection from util emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from cybir.core.util import coxeter_reflection as cr_util
            M = cr_util(np.array([1.0, 0.0]), np.array([1.0, 0.0]))
            assert M.shape == (2, 2)
            assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_coxeter_matrix_deprecation(self):
        """Importing coxeter_matrix from util emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from cybir.core.util import coxeter_matrix as cm_util
            M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
            M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
            result = cm_util([M1, M2])
            np.testing.assert_array_equal(result, M1 @ M2)
            assert any(issubclass(x.category, DeprecationWarning) for x in w)


# ============================================================
# CalabiYauLite curve_signs and tip fields
# ============================================================

class TestCalabiYauLiteCurveSignsAndTip:
    """Test curve_signs and tip fields on CalabiYauLite."""

    def test_curve_signs_default_none(self):
        """curve_signs defaults to None."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        assert cyl.curve_signs is None

    def test_tip_default_none(self):
        """tip defaults to None."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        assert cyl.tip is None

    def test_curve_signs_settable_before_freeze(self):
        """curve_signs can be set before freeze."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl._curve_signs = {(1, 0): 1, (0, 1): -1}
        assert cyl.curve_signs == {(1, 0): 1, (0, 1): -1}

    def test_tip_settable_before_freeze(self):
        """tip can be set before freeze."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl._tip = np.array([1.0, 2.0])
        np.testing.assert_array_equal(cyl.tip, np.array([1.0, 2.0]))

    def test_curve_signs_frozen_after_freeze(self):
        """curve_signs cannot be set after freeze."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl.freeze()
        with pytest.raises(AttributeError, match="frozen"):
            cyl._curve_signs = {(1, 0): 1}

    def test_tip_frozen_after_freeze(self):
        """tip cannot be set after freeze."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl.freeze()
        with pytest.raises(AttributeError, match="frozen"):
            cyl._tip = np.array([1.0, 2.0])

    def test_tip_returns_copy(self):
        """tip property returns a copy."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl._tip = np.array([1.0, 2.0])
        returned = cyl.tip
        returned[0] = 999.0
        assert cyl.tip[0] == 1.0

    def test_curve_signs_returns_copy(self):
        """curve_signs property returns a copy."""
        from cybir.core.types import CalabiYauLite
        cyl = CalabiYauLite(int_nums=np.zeros((2, 2, 2)))
        cyl._curve_signs = {(1, 0): 1}
        returned = cyl.curve_signs
        returned[(0, 1)] = -1
        assert (0, 1) not in cyl.curve_signs


# ============================================================
# reflect_phase_data tests
# ============================================================

class TestReflectPhaseData:
    """Test reflect_phase_data function."""

    def test_identity_returns_unchanged_kappa(self):
        """reflect_phase_data with identity returns same kappa."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )
        g = np.eye(2, dtype=np.int64)
        new_phase = reflect_phase_data(phase, g, label="CY_test")
        np.testing.assert_array_equal(new_phase.int_nums, kappa)

    def test_identity_returns_unchanged_c2(self):
        """reflect_phase_data with identity returns same c2."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )
        g = np.eye(2, dtype=np.int64)
        new_phase = reflect_phase_data(phase, g, label="CY_test")
        np.testing.assert_array_equal(new_phase.c2, c2)

    def test_single_reflection_transforms_correctly(self):
        """reflect_phase_data with single reflection produces correct einsum result."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )
        # A_2 reflection
        M = np.array([[-1, 1], [0, 1]], dtype=np.int64)

        new_phase = reflect_phase_data(phase, M, label="CY_ref")

        # Manually compute expected kappa and c2
        M_float = M.astype(float)
        expected_kappa = np.round(np.einsum("abc,xa,yb,zc", kappa, M_float, M_float, M_float)).astype(int)
        expected_c2 = (M @ c2).astype(int)

        np.testing.assert_allclose(new_phase.int_nums, expected_kappa, atol=1e-10)
        np.testing.assert_allclose(new_phase.c2, expected_c2, atol=1e-10)

    def test_product_element_kahler_uses_proper_inverse(self):
        """For a product g = M1 @ M2, Kahler rays use (g^-1)^T, NOT g (D-09)."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )

        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
        g = (M1 @ M2).astype(np.int64)

        new_phase = reflect_phase_data(phase, g, label="CY_product")

        # Verify: Kahler rays should be old_rays @ inv(g),
        # NOT old_rays @ g
        g_inv = np.round(np.linalg.inv(g)).astype(int)
        expected_rays = kc.rays() @ g_inv
        actual_rays = new_phase.kahler_cone.rays()

        # Convert both to sets of tuples for comparison
        expected_set = set(tuple(r) for r in expected_rays)
        actual_set = set(tuple(r) for r in actual_rays)
        assert expected_set == actual_set

    def test_single_reflection_g_inv_equals_g(self):
        """For a single reflection, g^-1 = g, so Kahler transform by g is correct."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )

        M = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        new_phase = reflect_phase_data(phase, M, label="CY_ref")

        # For single reflection, inv(M) == M
        expected_rays = kc.rays() @ M
        actual_rays = new_phase.kahler_cone.rays()

        expected_set = set(tuple(r) for r in expected_rays)
        actual_set = set(tuple(r) for r in actual_rays)
        assert expected_set == actual_set

    def test_integrality_assertion(self):
        """reflect_phase_data asserts integrality of g_inv (T-04-04)."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import reflect_phase_data
        from cybir.core.types import CalabiYauLite

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0",
        )

        # Non-integer-invertible matrix should fail assertion
        g_bad = np.array([[1, 1], [1, 3]])  # inv has non-integer entries: [[3, -1], [-1, 1]] / 2
        with pytest.raises(AssertionError):
            reflect_phase_data(phase, g_bad, label="CY_bad")


# ============================================================
# apply_coxeter_orbit tests
# ============================================================

class TestApplyCoxeterOrbit:
    """Test apply_coxeter_orbit function."""

    def _make_ekc_with_a2(self):
        """Create a mock EKC object with A_2 symmetric-flop reflections.

        Returns an EKC-like object with 1 fundamental phase and 2 reflections.
        """
        cytools = pytest.importorskip("cytools")
        from cybir.core.types import CalabiYauLite, ContractionType, ExtremalContraction
        from cybir.core.graph import CYGraph
        from cybir.core.util import tuplify

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0", tip=np.array([1.0, 1.0]),
        )

        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)

        graph = CYGraph()
        graph.add_phase(phase)

        # Add a terminal wall (ASYMPTOTIC) as self-loop
        asym_curve = np.array([1, 0])
        asym_contr = ExtremalContraction(
            contraction_curve=asym_curve,
            contraction_type=ContractionType.ASYMPTOTIC,
        )
        graph.add_contraction(asym_contr, "CY_0", "CY_0")

        # Create mock ekc
        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._sym_flop_refs = {tuplify(M1), tuplify(M2)}
        ekc._sym_flop_pairs = [(tuplify(M1), (1, 0)), (tuplify(M2), (0, 1))]
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._weyl_expanded = False
        ekc._weyl_phases = []
        ekc._coxeter_type_info = None
        ekc._coxeter_order = None
        ekc._root_label = "CY_0"

        return ekc

    def _make_ekc_with_two_phases_and_flop(self):
        """Create a mock EKC with 2 fundamental phases connected by a flop,
        plus A_2 symmetric-flop reflections.
        """
        cytools = pytest.importorskip("cytools")
        from cybir.core.types import CalabiYauLite, ContractionType, ExtremalContraction
        from cybir.core.graph import CYGraph
        from cybir.core.util import tuplify

        kappa_a = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        kappa_b = np.array([[[2, -1], [-1, 0]], [[-1, 0], [0, 3]]])
        c2 = np.array([24, 30])

        kc_a = cytools.Cone(rays=[[1, 0], [0, 1]])
        kc_b = cytools.Cone(rays=[[1, 0], [-1, 1]])

        phase_a = CalabiYauLite(
            int_nums=kappa_a, c2=c2, kahler_cone=kc_a, mori_cone=kc_a.dual(),
            label="CY_0", tip=np.array([1.0, 1.0]),
        )
        phase_b = CalabiYauLite(
            int_nums=kappa_b, c2=c2, kahler_cone=kc_b, mori_cone=kc_b.dual(),
            label="CY_1", tip=np.array([0.5, 1.0]),
        )

        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)

        graph = CYGraph()
        graph.add_phase(phase_a)
        graph.add_phase(phase_b)

        # Flop edge connecting A and B
        flop_curve = np.array([0, 1])
        flop_contr = ExtremalContraction(
            contraction_curve=flop_curve,
            contraction_type=ContractionType.FLOP,
            gv_invariant=1,
        )
        graph.add_contraction(flop_contr, "CY_0", "CY_1",
                              curve_sign_a=1, curve_sign_b=-1)

        # Terminal wall on CY_0
        asym_contr = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            contraction_type=ContractionType.ASYMPTOTIC,
        )
        graph.add_contraction(asym_contr, "CY_0", "CY_0")

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._sym_flop_refs = {tuplify(M1), tuplify(M2)}
        ekc._sym_flop_pairs = [(tuplify(M1), (1, 0)), (tuplify(M2), (0, 1))]
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._weyl_expanded = False
        ekc._weyl_phases = []
        ekc._coxeter_type_info = None
        ekc._coxeter_order = None
        ekc._root_label = "CY_0"

        return ekc

    def test_orbit_creates_correct_number_of_phases(self):
        """apply_coxeter_orbit with phases=True creates |W|-1 reflected phases per fund phase."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        assert ekc._graph.num_phases == 1
        apply_coxeter_orbit(ekc, phases=True)
        # |W(A_2)| = 6, identity skipped => 5 new phases per fundamental phase
        # 1 fund phase => 5 new + 1 original = 6 total
        assert ekc._graph.num_phases == 6

    def test_orbit_phases_false_no_new_phases(self):
        """apply_coxeter_orbit with phases=False creates no new phases."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        assert ekc._graph.num_phases == 1
        apply_coxeter_orbit(ekc, phases=False)
        assert ekc._graph.num_phases == 1

    def test_orbit_phases_false_accumulates_generators(self):
        """phases=False mode accumulates eff_cone_gens."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=False)
        # Should have reflected Kahler rays
        assert len(ekc._eff_cone_gens) > 0

    def test_orbit_phases_false_accumulates_infinity_gens(self):
        """phases=False mode accumulates infinity_cone_gens from terminal walls."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=False)
        # The asymptotic self-loop curve [1,0] reflected by 5 group elements
        assert len(ekc._infinity_cone_gens) > 0

    def test_reflected_terminal_walls_are_self_loops(self):
        """Reflected terminal walls appear as self-loops on reflected phases."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=True)

        # Each reflected phase should have self-loop terminal walls
        for phase in ekc._graph.phases:
            if phase.label == "CY_0":
                continue
            contrs = ekc._graph.contractions_from(phase.label)
            # Should have at least one contraction (the reflected terminal wall)
            assert len(contrs) >= 1

    def test_reflected_flop_edges_connect_reflected_phases(self):
        """Reflected flop edges connect corresponding reflected phases (D-12)."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_two_phases_and_flop()
        assert ekc._graph.num_phases == 2
        apply_coxeter_orbit(ekc, phases=True)

        # 2 fund phases, |W| = 6 => 2 * 5 = 10 new + 2 original = 12 total
        assert ekc._graph.num_phases == 12

        # Check that flop edges exist between reflected phase pairs
        # Count FLOP type edges
        from cybir.core.types import ContractionType
        flop_edges = 0
        for u, v, data in ekc._graph._graph.edges(data=True):
            contr = data["contraction"]
            if contr.contraction_type == ContractionType.FLOP:
                flop_edges += 1
        # Original 1 flop + 5 reflected flops = 6 total
        assert flop_edges == 6

    def test_generator_accumulation_kahler_rays_in_eff(self):
        """Generator accumulation includes reflected Kahler rays in eff_cone_gens."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=True)
        # Each of 5 reflected phases contributes Kahler rays
        assert len(ekc._eff_cone_gens) >= 5

    def test_generator_accumulation_terminal_curves_in_infinity(self):
        """Generator accumulation includes reflected terminal wall curves in infinity_cone_gens."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=True)
        # 5 reflected terminal walls from the asymptotic self-loop
        assert len(ekc._infinity_cone_gens) >= 1

    def test_generator_accumulation_zvd_in_eff(self):
        """Generator accumulation includes reflected zero-vol divisors in eff_cone_gens."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import apply_coxeter_orbit
        from cybir.core.types import CalabiYauLite, ContractionType, ExtremalContraction
        from cybir.core.graph import CYGraph
        from cybir.core.util import tuplify

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0", tip=np.array([1.0, 1.0]),
        )

        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)

        graph = CYGraph()
        graph.add_phase(phase)

        # CFT self-loop with zero_vol_divisor
        cft_contr = ExtremalContraction(
            contraction_curve=np.array([1, 0]),
            contraction_type=ContractionType.CFT,
            zero_vol_divisor=np.array([1, -1]),
        )
        graph.add_contraction(cft_contr, "CY_0", "CY_0")

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._sym_flop_refs = {tuplify(M1), tuplify(M2)}
        ekc._sym_flop_pairs = [(tuplify(M1), (1, 0)), (tuplify(M2), (0, 1))]
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._weyl_expanded = False
        ekc._weyl_phases = []
        ekc._coxeter_type_info = None
        ekc._coxeter_order = None
        ekc._root_label = "CY_0"

        apply_coxeter_orbit(ekc, phases=True)
        # zvd [1, -1] reflected by 5 group elements -> at least some in eff_cone_gens
        # Plus Kahler rays
        zvd_tuples = set()
        for gen in ekc._eff_cone_gens:
            zvd_tuples.add(gen)
        assert len(ekc._eff_cone_gens) > 2  # Kahler rays + reflected zvds

    def test_no_reflections_is_noop(self):
        """apply_coxeter_orbit with no symmetric-flop reflections is a no-op."""
        from cybir.core.coxeter import apply_coxeter_orbit
        from cybir.core.graph import CYGraph
        from cybir.core.types import CalabiYauLite

        graph = CYGraph()
        phase = CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label="CY_0")
        graph.add_phase(phase)

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._sym_flop_refs = set()
        ekc._sym_flop_pairs = []
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._weyl_expanded = False
        ekc._weyl_phases = []
        ekc._coxeter_type_info = None
        ekc._coxeter_order = None
        ekc._root_label = "CY_0"

        apply_coxeter_orbit(ekc, phases=True)
        assert ekc._graph.num_phases == 1

    def test_infinite_type_logs_warning(self, caplog):
        """apply_coxeter_orbit with infinite-type group logs warning."""
        from cybir.core.coxeter import apply_coxeter_orbit
        from cybir.core.graph import CYGraph
        from cybir.core.types import CalabiYauLite
        from cybir.core.util import tuplify

        # Affine A_2: 3 permutation-matrix reflections in R^3
        # All pairwise products have order 3, giving all m_ij = 3
        # The bilinear form B has a zero eigenvalue => NOT positive definite
        M1 = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=np.int64)
        M3 = np.array([[0, 0, 1], [0, 1, 0], [1, 0, 0]], dtype=np.int64)

        graph = CYGraph()
        phase = CalabiYauLite(int_nums=np.zeros((3, 3, 3)), label="CY_0")
        graph.add_phase(phase)

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._sym_flop_refs = {tuplify(M1), tuplify(M2), tuplify(M3)}
        ekc._sym_flop_pairs = [
            (tuplify(M1), (1, 0, 0)),
            (tuplify(M2), (0, 1, 0)),
            (tuplify(M3), (0, 0, 1)),
        ]
        ekc._infinity_cone_gens = set()
        ekc._eff_cone_gens = set()
        ekc._weyl_expanded = False
        ekc._weyl_phases = []
        ekc._coxeter_type_info = None
        ekc._coxeter_order = None
        ekc._root_label = "CY_0"

        with caplog.at_level(logging.WARNING, logger="cybir"):
            apply_coxeter_orbit(ekc, phases=True)

        # Should still be 1 phase (no expansion)
        assert ekc._graph.num_phases == 1
        # Should have logged a warning about infinite
        assert any("infinite" in r.message.lower() or "Infinite" in r.message for r in caplog.records)

    def test_coxeter_type_stored_on_ekc(self):
        """apply_coxeter_orbit stores coxeter type info on ekc."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        apply_coxeter_orbit(ekc, phases=True)
        assert ekc._coxeter_type_info is not None
        assert ekc._coxeter_order == 6

    def test_reflected_phase_has_curve_signs(self):
        """Reflected phases from apply_coxeter_orbit have non-None curve_signs (SC-4)."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        # Set curve_signs on root phase (simulates what construct_phases does)
        root = ekc._graph.get_phase("CY_0")
        root._curve_signs = {(1, 0): 1, (0, 1): 1}
        ekc._root_label = "CY_0"

        apply_coxeter_orbit(ekc, phases=True)

        # Every Weyl-expanded phase should have curve_signs
        for label in ekc._weyl_phases:
            phase = ekc._graph.get_phase(label)
            assert phase.curve_signs is not None, (
                f"Phase {label} has curve_signs=None"
            )
            # Keys should match root's curve_signs keys
            assert set(phase.curve_signs.keys()) == set(root.curve_signs.keys()), (
                f"Phase {label} curve_signs keys mismatch"
            )

    def test_reflected_phase_has_tip(self):
        """Reflected phases from apply_coxeter_orbit have non-None tip (SC-4)."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        root = ekc._graph.get_phase("CY_0")
        root._curve_signs = {(1, 0): 1, (0, 1): 1}
        ekc._root_label = "CY_0"

        apply_coxeter_orbit(ekc, phases=True)

        for label in ekc._weyl_phases:
            phase = ekc._graph.get_phase(label)
            assert phase.tip is not None, f"Phase {label} has tip=None"

    def test_reflected_phase_curve_signs_differ_from_root(self):
        """At least some reflected phases have different curve_signs than root."""
        from cybir.core.coxeter import apply_coxeter_orbit

        ekc = self._make_ekc_with_a2()
        root = ekc._graph.get_phase("CY_0")
        root._curve_signs = {(1, 0): 1, (0, 1): 1}
        ekc._root_label = "CY_0"

        apply_coxeter_orbit(ekc, phases=True)

        root_signs = root.curve_signs
        any_different = False
        for label in ekc._weyl_phases:
            phase = ekc._graph.get_phase(label)
            if phase.curve_signs != root_signs:
                any_different = True
                break
        assert any_different, (
            "All reflected phases have identical curve_signs to root; "
            "expected at least one to differ"
        )

    def test_invariants_for_weyl_phase_warns_on_missing_signs(self, caplog):
        """_invariants_for_impl warns when Weyl phase has no curve_signs (IN-06)."""
        from cybir.core.coxeter import _invariants_for_impl
        from cybir.core.types import CalabiYauLite
        from cybir.core.graph import CYGraph

        graph = CYGraph()
        root = CalabiYauLite(
            int_nums=np.zeros((2, 2, 2)), label="CY_0",
            tip=np.array([1.0, 1.0]),
        )
        root._curve_signs = {(1, 0): 1, (0, 1): 1}
        # Create a Weyl-expanded phase WITHOUT curve_signs
        weyl_phase = CalabiYauLite(
            int_nums=np.zeros((2, 2, 2)), label="CY_1",
        )
        graph.add_phase(root)
        graph.add_phase(weyl_phase)

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._root_label = "CY_0"
        ekc._root_invariants = "mock_invariants"
        ekc._weyl_phases = ["CY_1"]

        with caplog.at_level(logging.WARNING, logger="cybir"):
            result = _invariants_for_impl(ekc, "CY_1")

        assert result == "mock_invariants"
        assert any("Weyl-expanded" in r.message or "curve_signs" in r.message
                    for r in caplog.records)


# ============================================================
# to_fundamental_domain tests
# ============================================================

class TestToFundamentalDomain:
    """Test to_fundamental_domain chamber walk algorithm."""

    @pytest.fixture
    def a2_setup(self):
        """A_2 reflections and curves for chamber walk tests.

        Returns reflections, curves, and a point in the fundamental domain.
        The fundamental domain is the region where point @ curve >= 0
        for all curves.
        """
        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
        # Curves that define the walls (simple roots for A_2)
        c1 = np.array([1, 0])  # M1 reflects through hyperplane c1.x = 0
        c2 = np.array([0, 1])  # M2 reflects through hyperplane c2.x = 0
        return [M1, M2], [c1, c2]

    def test_point_in_fund_domain_returns_unchanged(self, a2_setup):
        """A point already in the fundamental domain returns unchanged."""
        from cybir.core.coxeter import to_fundamental_domain

        reflections, curves = a2_setup
        point = np.array([1.0, 1.0])  # positive pairing with both curves
        mapped, g = to_fundamental_domain(point, reflections, curves)
        np.testing.assert_allclose(mapped, point)
        np.testing.assert_array_equal(g, np.eye(2, dtype=np.int64))

    def test_reflected_point_walks_back(self, a2_setup):
        """A reflected point is walked back to the fundamental domain."""
        from cybir.core.coxeter import to_fundamental_domain

        reflections, curves = a2_setup
        M1 = reflections[0]
        fund_point = np.array([2.0, 1.0])
        reflected = (M1 @ fund_point).astype(float)
        # reflected should have negative pairing with curve c1
        assert reflected @ curves[0] < 0

        mapped, g = to_fundamental_domain(reflected, reflections, curves)
        # mapped should be back in the fundamental domain
        for c in curves:
            assert mapped @ c >= -1e-12
        # mapped should equal the original fund_point
        np.testing.assert_allclose(mapped, fund_point, atol=1e-10)

    def test_max_iter_raises(self, a2_setup):
        """RuntimeError raised if max_iter exceeded."""
        from cybir.core.coxeter import to_fundamental_domain

        reflections, curves = a2_setup
        # Use max_iter=0 to force failure
        point = np.array([-1.0, -1.0])  # needs reflections
        with pytest.raises(RuntimeError, match="max_iter"):
            to_fundamental_domain(point, reflections, curves, max_iter=0)

    def test_wall_point_not_reflected(self, a2_setup):
        """A point on a wall (curve pairing = 0) is not reflected through it."""
        from cybir.core.coxeter import to_fundamental_domain

        reflections, curves = a2_setup
        # Point on the c1 wall: c1.x = 0, c2.x > 0
        point = np.array([0.0, 1.0])
        mapped, g = to_fundamental_domain(point, reflections, curves)
        np.testing.assert_allclose(mapped, point)
        np.testing.assert_array_equal(g, np.eye(2, dtype=np.int64))

    def test_group_element_maps_back(self, a2_setup):
        """The returned group element g maps the fund domain point back to input."""
        from cybir.core.coxeter import to_fundamental_domain

        reflections, curves = a2_setup
        M1, M2 = reflections
        fund_point = np.array([3.0, 2.0])
        # Apply M2 then M1: g_applied = M1 @ M2
        reflected = (M1 @ M2 @ fund_point).astype(float)

        mapped, g = to_fundamental_domain(reflected, reflections, curves)
        # g @ mapped should give back the reflected point
        np.testing.assert_allclose(g @ mapped, reflected, atol=1e-10)


# ============================================================
# _invariants_for_impl tests
# ============================================================

class TestInvariantsForImpl:
    """Test _invariants_for_impl helper for on-demand GV reconstruction."""

    def test_root_phase_returns_root_invariants(self):
        """invariants_for on root phase returns root invariants unchanged."""
        cytools = pytest.importorskip("cytools")
        from cybir.core.coxeter import _invariants_for_impl
        from cybir.core.types import CalabiYauLite, ContractionType, ExtremalContraction
        from cybir.core.graph import CYGraph

        kappa = np.array([[[2, 1], [1, 0]], [[1, 0], [0, 3]]])
        c2 = np.array([24, 30])
        kc = cytools.Cone(rays=[[1, 0], [0, 1]])
        mori = kc.dual()
        phase = CalabiYauLite(
            int_nums=kappa, c2=c2, kahler_cone=kc, mori_cone=mori,
            label="CY_0", tip=np.array([1.0, 1.0]),
            curve_signs={(1, 0): 1, (0, 1): 1},
        )

        graph = CYGraph()
        graph.add_phase(phase)

        class _MockEKC:
            pass

        ekc = _MockEKC()
        ekc._graph = graph
        ekc._root_label = "CY_0"
        ekc._root_invariants = "mock_invariants"

        # Root phase has same curve_signs as root => no flops needed
        # Should return root_invariants directly
        result = _invariants_for_impl(ekc, "CY_0")
        assert result == "mock_invariants"


# ============================================================
# CYBirationalClass.invariants_for and to_fundamental_domain
# ============================================================

class TestCYBirationalClassNewMethods:
    """Test CYBirationalClass.invariants_for and to_fundamental_domain exist."""

    def test_invariants_for_method_exists(self):
        """CYBirationalClass has invariants_for method."""
        from cybir.core.ekc import CYBirationalClass
        assert hasattr(CYBirationalClass, "invariants_for")

    def test_to_fundamental_domain_method_exists(self):
        """CYBirationalClass has to_fundamental_domain method."""
        from cybir.core.ekc import CYBirationalClass
        assert hasattr(CYBirationalClass, "to_fundamental_domain")

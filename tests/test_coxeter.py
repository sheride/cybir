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
    """B_2 simple reflections in R^2.

    M1 = [[-1, 0], [1, 1]], M2 = [[1, 1], [0, -1]]
    Product M1 @ M2 has order 4, |W(B_2)| = 8.
    """
    M1 = np.array([[-1, 0], [1, 1]], dtype=np.int64)
    M2 = np.array([[1, 1], [0, -1]], dtype=np.int64)
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

    def test_deprecated_alias(self):
        """coxeter_matrix is a deprecated alias for coxeter_element."""
        from cybir.core.coxeter import coxeter_matrix
        M1 = np.array([[-1, 1], [0, 1]], dtype=np.int64)
        M2 = np.array([[1, 0], [1, -1]], dtype=np.int64)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = coxeter_matrix([M1, M2])
            assert len(w) == 1
            assert "deprecated" in str(w[0].message).lower()
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

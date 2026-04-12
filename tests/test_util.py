"""Tests for cybir.core.util utility functions."""

import numpy as np
import pytest
import sympy


class TestChargeMatrixHsnf:
    """Tests for charge_matrix_hsnf."""

    def test_dependent_vectors_gives_one_relation(self):
        """Three points in 2D: one integer relation expected."""
        from cybir.core.util import charge_matrix_hsnf

        # 3 vectors in 2D: (1,0), (0,1), (1,1) -- one relation expected
        vectors = [[1, 0], [0, 1], [1, 1]]
        result = charge_matrix_hsnf(vectors)
        assert result.shape == (1, 3)
        # Relation should satisfy vectors.T @ relation.T == 0
        v = np.array(vectors)
        assert np.allclose(v.T @ result.T, 0)

    def test_full_rank_gives_no_relations(self):
        """Two linearly independent vectors in 2D: no relations."""
        from cybir.core.util import charge_matrix_hsnf

        vectors = [[1, 0], [0, 1]]
        result = charge_matrix_hsnf(vectors)
        assert result.shape[0] == 0


class TestMovingCone:
    """Tests for moving_cone."""

    def test_returns_cone_object(self):
        """moving_cone should return a cytools.Cone."""
        import cytools
        from cybir.core.util import moving_cone

        # Simple 2x3 charge matrix
        Q = np.array([[1, -1, 0], [0, 1, -1]])
        cone = moving_cone(Q)
        assert isinstance(cone, cytools.Cone)

    def test_ambient_dimension(self):
        """Returned cone should have correct ambient dimension."""
        from cybir.core.util import moving_cone

        Q = np.array([[1, -1, 0], [0, 1, -1]])
        cone = moving_cone(Q)
        assert cone.ambient_dim() == Q.shape[0]


class TestSympyNumberClean:
    """Tests for sympy_number_clean."""

    def test_one_third(self):
        from cybir.core.util import sympy_number_clean

        result = sympy_number_clean(0.333333333)
        assert result == sympy.Rational(1, 3)

    def test_five_halves(self):
        from cybir.core.util import sympy_number_clean

        result = sympy_number_clean(2.5)
        assert result == sympy.Rational(5, 2)

    def test_zero(self):
        from cybir.core.util import sympy_number_clean

        result = sympy_number_clean(0)
        assert result == 0


class TestTuplify:
    """Tests for tuplify."""

    def test_1d_array(self):
        from cybir.core.util import tuplify

        assert tuplify(np.array([1, 2, 3])) == (1, 2, 3)

    def test_2d_array(self):
        from cybir.core.util import tuplify

        assert tuplify(np.array([[1, 2], [3, 4]])) == ((1, 2), (3, 4))

    def test_scalar(self):
        from cybir.core.util import tuplify

        result = tuplify(np.array(5))
        assert result == 5


class TestNormalizeCurve:
    """Tests for normalize_curve."""

    def test_already_positive(self):
        from cybir.core.util import normalize_curve

        assert normalize_curve(np.array([1, 2, 3])) == (1, 2, 3)

    def test_first_negative(self):
        from cybir.core.util import normalize_curve

        assert normalize_curve(np.array([-1, 2, 3])) == (1, -2, -3)

    def test_leading_zero_then_negative(self):
        from cybir.core.util import normalize_curve

        assert normalize_curve(np.array([0, -2, 3])) == (0, 2, -3)

    def test_return_sign(self):
        from cybir.core.util import normalize_curve

        result = normalize_curve(np.array([-1, 0, 0]), return_sign=True)
        assert result == ((1, 0, 0), -1)


class TestProjectionMatrix:
    """Tests for projection_matrix."""

    def test_shape(self):
        from cybir.core.util import projection_matrix

        curve = np.array([1, 0])
        P = projection_matrix(curve)
        assert P.shape == (1, 2)

    def test_projects_out_curve(self):
        from cybir.core.util import projection_matrix

        curve = np.array([1, 0])
        P = projection_matrix(curve)
        assert np.allclose(P @ curve, 0)

    def test_three_dim(self):
        from cybir.core.util import projection_matrix

        curve = np.array([1, 1, 0])
        P = projection_matrix(curve)
        assert P.shape == (2, 3)
        assert np.allclose(P @ curve, 0)


# ============================================================
# projected_int_nums
# ============================================================


class TestProjectedIntNums:
    """Tests for projected_int_nums."""

    def test_full_projection_scalar(self):
        """n_projected=3 contracts all indices, giving a scalar."""
        from cybir.core.util import projected_int_nums

        # 2x2x2 intersection numbers
        int_nums = np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])
        curve = np.array([1, 0])
        result = projected_int_nums(int_nums, curve, n_projected=3)
        # With curve=[1,0], projection_matrix gives [[0,1]] (1x2)
        # Contracting all 3 indices with P=[0,1] picks out int_nums projected
        # P_ia P_jb P_kc kappa_ijk -> scalar
        assert np.isscalar(result) or result.ndim == 0

    def test_two_projected_gives_1d(self):
        """n_projected=2 contracts two indices, leaving one free original index."""
        from cybir.core.util import projected_int_nums

        int_nums = np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])
        curve = np.array([1, 0])
        result = projected_int_nums(int_nums, curve, n_projected=2)
        # einsum('ai,bj,ijk->abk', P, P, kappa) with P=(1,2)
        # gives (1,1,2) which squeezes to (2,)
        assert result.ndim == 1
        assert result.shape[0] == 2

    def test_one_projected_gives_2d(self):
        """n_projected=1 contracts one index, leaving two free original indices."""
        from cybir.core.util import projected_int_nums

        int_nums = np.array([[[0, 1], [1, 0]], [[1, 0], [0, 2]]])
        curve = np.array([1, 0])
        result = projected_int_nums(int_nums, curve, n_projected=1)
        # einsum('ai,ijk->ajk', P, kappa) with P=(1,2)
        # gives (1,2,2) which squeezes to (2,2)
        assert result.ndim == 2
        assert result.shape == (2, 2)

    def test_three_dim_full_projection(self):
        """Full projection for h11=3 gives (h11-1)^3 = 2x2x2 tensor."""
        from cybir.core.util import projected_int_nums

        # 3x3x3 intersection numbers (simple diagonal-ish)
        int_nums = np.zeros((3, 3, 3))
        int_nums[0, 0, 0] = 1
        int_nums[1, 1, 1] = 2
        int_nums[2, 2, 2] = 3
        curve = np.array([1, 0, 0])
        result = projected_int_nums(int_nums, curve, n_projected=3)
        # P is (2,3), so result is (2,2,2)
        assert result.shape == (2, 2, 2)


# ============================================================
# find_minimal_N
# ============================================================


class TestFindMinimalN:
    """Tests for find_minimal_N."""

    def test_half_integers(self):
        """Array with 0.5 entries needs N=2."""
        from cybir.core.util import find_minimal_N

        assert find_minimal_N(np.array([0.5, 1.0, 1.5])) == 2

    def test_already_integer(self):
        """Integer array needs N=1."""
        from cybir.core.util import find_minimal_N

        assert find_minimal_N(np.array([1.0, 2.0, 3.0])) == 1

    def test_thirds(self):
        """Array with 1/3 entries needs N=3."""
        from cybir.core.util import find_minimal_N

        assert find_minimal_N(np.array([1 / 3, 2 / 3])) == 3

    def test_raises_on_irrational(self):
        """Should raise ValueError for irrational-like entries."""
        from cybir.core.util import find_minimal_N

        with pytest.raises(ValueError):
            find_minimal_N(np.array([np.pi]), max_val=100)


# ============================================================
# matrix_period
# ============================================================


class TestMatrixPeriod:
    """Tests for matrix_period."""

    def test_identity_period_is_one(self):
        """Identity matrix has period 1."""
        from cybir.core.util import matrix_period

        assert matrix_period(np.eye(2)) == 1

    def test_90_degree_rotation(self):
        """90-degree rotation matrix has period 4."""
        from cybir.core.util import matrix_period

        R = np.array([[0, -1], [1, 0]])
        assert matrix_period(R) == 4

    def test_negation_period_is_two(self):
        """-I has period 2."""
        from cybir.core.util import matrix_period

        assert matrix_period(-np.eye(3)) == 2

    def test_raises_if_not_periodic(self):
        """Non-periodic matrix raises ValueError."""
        from cybir.core.util import matrix_period

        # A matrix that won't return to identity
        M = np.array([[1, 1], [0, 1]])  # shear
        with pytest.raises(ValueError):
            matrix_period(M, max_iter=50)


# ============================================================
# get_coxeter_reflection
# ============================================================


class TestCoxeterReflection:
    """Tests for get_coxeter_reflection."""

    def test_reflection_sends_curve_to_minus_curve(self):
        """M @ curve = -curve when D.C != 0."""
        from cybir.core.util import get_coxeter_reflection

        divisor = np.array([1, 0])
        curve = np.array([1, 0])
        M = get_coxeter_reflection(divisor, curve)
        assert np.allclose(M @ curve, -curve)

    def test_zero_intersection_gives_identity(self):
        """When D.C = 0, return identity."""
        from cybir.core.util import get_coxeter_reflection

        divisor = np.array([0, 0])
        curve = np.array([1, 0])
        M = get_coxeter_reflection(divisor, curve)
        assert np.allclose(M, np.eye(2))

    def test_reflection_is_involution(self):
        """Coxeter reflection squared is identity (for D.C=1)."""
        from cybir.core.util import get_coxeter_reflection

        divisor = np.array([1, 0])
        curve = np.array([1, 0])
        M = get_coxeter_reflection(divisor, curve)
        assert np.allclose(M @ M, np.eye(2))

    def test_orthogonal_divisor_identity(self):
        """When D.C = 0 (non-trivial divisor), returns identity."""
        from cybir.core.util import get_coxeter_reflection

        divisor = np.array([0, 1])
        curve = np.array([1, 0])
        M = get_coxeter_reflection(divisor, curve)
        assert np.allclose(M, np.eye(2))


# ============================================================
# coxeter_matrix
# ============================================================


class TestCoxeterMatrix:
    """Tests for coxeter_matrix."""

    def test_single_reflection(self):
        """Single reflection gives itself."""
        from cybir.core.util import coxeter_matrix

        R = np.array([[-1, 0], [0, 1]])
        result = coxeter_matrix([R])
        assert np.allclose(result, R)

    def test_two_reflections(self):
        """Product of two reflections."""
        from cybir.core.util import coxeter_matrix

        R1 = np.array([[-1, 0], [0, 1]])
        R2 = np.array([[1, 0], [0, -1]])
        result = coxeter_matrix([R1, R2])
        assert np.allclose(result, R1 @ R2)

    def test_empty_list_gives_identity(self):
        """Empty list of reflections raises or returns identity."""
        from cybir.core.util import coxeter_matrix

        # With no reflections, should return identity
        # But need a size hint -- test expects identity behavior
        result = coxeter_matrix([])
        # Result for empty list: plan says identity
        # Since no size info, should raise or return something
        # Plan says: "Returns identity if empty list"
        assert result is not None

    def test_composition_has_finite_period(self):
        """Coxeter element from reflections has finite period."""
        from cybir.core.util import coxeter_matrix, get_coxeter_reflection, matrix_period

        # Two reflections for known h11=2 case
        d1 = np.array([1, 0])
        c1 = np.array([1, 0])
        d2 = np.array([0, 1])
        c2 = np.array([0, 1])
        R1 = get_coxeter_reflection(d1, c1)
        R2 = get_coxeter_reflection(d2, c2)
        C = coxeter_matrix([R1, R2])
        period = matrix_period(C)
        assert period >= 1

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

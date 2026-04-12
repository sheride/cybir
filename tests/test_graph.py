"""Tests for cybir.core.graph CYGraph."""

import numpy as np
import pytest

from cybir.core.types import CalabiYauLite, ExtremalContraction, ContractionType


def _make_phase(label):
    """Create a minimal CalabiYauLite for testing."""
    return CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label=label)


def _make_contraction(curve=None):
    """Create a minimal ExtremalContraction for testing."""
    if curve is None:
        curve = np.array([1, 0])
    return ExtremalContraction(flopping_curve=curve)


class TestCYGraphEmpty:
    """Tests for empty CYGraph."""

    def test_empty_graph(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        assert g.num_phases == 0
        assert g.num_contractions == 0

    def test_repr_empty(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        assert "phases=0" in repr(g)


class TestCYGraphNodes:
    """Tests for adding phases."""

    def test_add_single_phase(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        p = _make_phase("A")
        g.add_phase(p)
        assert g.num_phases == 1
        assert len(g.phases) == 1

    def test_phases_returns_calabi_yau_lite(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        p = _make_phase("A")
        g.add_phase(p)
        assert isinstance(g.phases[0], CalabiYauLite)
        assert g.phases[0].label == "A"

    def test_get_phase_by_label(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        p = _make_phase("X")
        g.add_phase(p)
        assert g.get_phase("X") is p


class TestCYGraphEdges:
    """Tests for adding contractions and neighbors."""

    def test_add_contraction(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        assert g.num_contractions == 1

    def test_contractions_returns_objects(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        assert isinstance(g.contractions[0], ExtremalContraction)

    def test_neighbors_single_edge(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        pa = _make_phase("A")
        pb = _make_phase("B")
        g.add_phase(pa)
        g.add_phase(pb)
        g.add_contraction(_make_contraction(), "A", "B")
        neighbors = g.neighbors("A")
        assert len(neighbors) == 1
        assert neighbors[0].label == "B"

    def test_neighbors_chain(self):
        """A-B-C chain: neighbors of B should be [A, C]."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        for label in ["A", "B", "C"]:
            g.add_phase(_make_phase(label))
        g.add_contraction(_make_contraction(), "A", "B")
        g.add_contraction(_make_contraction(), "B", "C")
        neighbors = g.neighbors("B")
        labels = sorted(n.label for n in neighbors)
        assert labels == ["A", "C"]

    def test_num_phases_count(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        for label in ["A", "B", "C"]:
            g.add_phase(_make_phase(label))
        assert g.num_phases == 3


class TestCYGraphContractionsFrom:
    """Tests for contractions_from method."""

    def test_contractions_from_returns_tuples(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        result = g.contractions_from("A")
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2

    def test_contractions_from_sign_phase_a(self):
        """Phase A (phase_a) should get curve_sign_a."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B", curve_sign_a=1, curve_sign_b=-1)
        result = g.contractions_from("A")
        contraction, sign = result[0]
        assert contraction is c
        assert sign == 1

    def test_contractions_from_sign_phase_b(self):
        """Phase B (phase_b) should get curve_sign_b."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B", curve_sign_a=1, curve_sign_b=-1)
        result = g.contractions_from("B")
        contraction, sign = result[0]
        assert contraction is c
        assert sign == -1

    def test_contractions_from_multiple(self):
        """Phase B in A-B-C chain has two contractions."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        for label in ["A", "B", "C"]:
            g.add_phase(_make_phase(label))
        c1 = _make_contraction(np.array([1, 0]))
        c2 = _make_contraction(np.array([0, 1]))
        g.add_contraction(c1, "A", "B")
        g.add_contraction(c2, "B", "C")
        result = g.contractions_from("B")
        assert len(result) == 2

    def test_contractions_from_default_signs(self):
        """Default signs are +1 for phase_a, -1 for phase_b."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        _, sign_a = g.contractions_from("A")[0]
        _, sign_b = g.contractions_from("B")[0]
        assert sign_a == 1
        assert sign_b == -1


class TestCYGraphPhasesAdjacentTo:
    """Tests for phases_adjacent_to method."""

    def test_phases_adjacent_to_returns_phases(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        pa = _make_phase("A")
        pb = _make_phase("B")
        g.add_phase(pa)
        g.add_phase(pb)
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        result = g.phases_adjacent_to(c)
        assert result is not None
        assert len(result) == 2
        labels = {result[0].label, result[1].label}
        assert labels == {"A", "B"}

    def test_phases_adjacent_to_identity(self):
        """Uses identity comparison, not equality."""
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction()
        g.add_contraction(c, "A", "B")
        # A different contraction with same curve should not match
        c2 = _make_contraction()
        assert g.phases_adjacent_to(c2) is None

    def test_phases_adjacent_to_not_found(self):
        from cybir.core.graph import CYGraph

        g = CYGraph()
        g.add_phase(_make_phase("A"))
        c = _make_contraction()
        assert g.phases_adjacent_to(c) is None

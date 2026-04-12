"""Tests for cybir.core.graph PhaseGraph."""

import numpy as np
import pytest

from cybir.core.types import CalabiYauLite, ExtremalContraction, ContractionType


def _make_phase(label):
    """Create a minimal CalabiYauLite for testing."""
    return CalabiYauLite(int_nums=np.zeros((2, 2, 2)), label=label)


def _make_contraction(start_label, end_label):
    """Create a minimal ExtremalContraction for testing."""
    return ExtremalContraction(
        flopping_curve=np.array([1, 0]),
        start_phase=start_label,
        end_phase=end_label,
    )


class TestPhaseGraphEmpty:
    """Tests for empty PhaseGraph."""

    def test_empty_graph(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        assert g.num_phases == 0
        assert g.num_contractions == 0

    def test_repr_empty(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        assert "phases=0" in repr(g)


class TestPhaseGraphNodes:
    """Tests for adding phases."""

    def test_add_single_phase(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        p = _make_phase("A")
        g.add_phase(p)
        assert g.num_phases == 1
        assert len(g.phases) == 1

    def test_phases_returns_calabi_yau_lite(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        p = _make_phase("A")
        g.add_phase(p)
        assert isinstance(g.phases[0], CalabiYauLite)
        assert g.phases[0].label == "A"

    def test_get_phase_by_label(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        p = _make_phase("X")
        g.add_phase(p)
        assert g.get_phase("X") is p


class TestPhaseGraphEdges:
    """Tests for adding contractions and neighbors."""

    def test_add_contraction(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction("A", "B")
        g.add_contraction(c)
        assert g.num_contractions == 1

    def test_contractions_returns_objects(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        g.add_phase(_make_phase("A"))
        g.add_phase(_make_phase("B"))
        c = _make_contraction("A", "B")
        g.add_contraction(c)
        assert isinstance(g.contractions[0], ExtremalContraction)

    def test_neighbors_single_edge(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        pa = _make_phase("A")
        pb = _make_phase("B")
        g.add_phase(pa)
        g.add_phase(pb)
        g.add_contraction(_make_contraction("A", "B"))
        neighbors = g.neighbors("A")
        assert len(neighbors) == 1
        assert neighbors[0].label == "B"

    def test_neighbors_chain(self):
        """A-B-C chain: neighbors of B should be [A, C]."""
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        for label in ["A", "B", "C"]:
            g.add_phase(_make_phase(label))
        g.add_contraction(_make_contraction("A", "B"))
        g.add_contraction(_make_contraction("B", "C"))
        neighbors = g.neighbors("B")
        labels = sorted(n.label for n in neighbors)
        assert labels == ["A", "C"]

    def test_num_phases_count(self):
        from cybir.core.graph import PhaseGraph

        g = PhaseGraph()
        for label in ["A", "B", "C"]:
            g.add_phase(_make_phase(label))
        assert g.num_phases == 3

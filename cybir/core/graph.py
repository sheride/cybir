"""Phase adjacency graph for extended Kahler cone construction.

The :class:`PhaseGraph` stores CalabiYauLite phases as nodes and
ExtremalContraction objects as edges, backed by a ``networkx.Graph``.
"""

import networkx as nx

from .types import CalabiYauLite, ExtremalContraction


class PhaseGraph:
    """Adjacency graph with CalabiYauLite phases as nodes and
    ExtremalContraction objects as edges.

    Uses an undirected ``networkx.Graph`` internally. Contractions
    connect two phases symmetrically (you can flop in either
    direction). The start/end distinction is stored on the
    :class:`~cybir.core.types.ExtremalContraction` object, not the
    graph edge.

    Examples
    --------
    >>> g = PhaseGraph()
    >>> g.add_phase(phase_a)
    >>> g.add_phase(phase_b)
    >>> g.add_contraction(contraction_ab)
    >>> g.neighbors("A")
    [CalabiYauLite(label='B')]
    """

    def __init__(self):
        self._graph = nx.Graph()

    def add_phase(self, phase):
        """Add a phase node.

        Parameters
        ----------
        phase : CalabiYauLite
            Phase with a label set.
        """
        self._graph.add_node(phase.label, phase=phase)

    def add_contraction(self, contraction):
        """Add a contraction edge between two phases.

        Parameters
        ----------
        contraction : ExtremalContraction
            Contraction with ``start_phase`` and ``end_phase`` labels set.
        """
        self._graph.add_edge(
            contraction.start_phase,
            contraction.end_phase,
            contraction=contraction,
        )

    @property
    def phases(self):
        """All phase objects.

        Returns
        -------
        list of CalabiYauLite
        """
        return [d["phase"] for _, d in self._graph.nodes(data=True)]

    @property
    def contractions(self):
        """All contraction objects.

        Returns
        -------
        list of ExtremalContraction
        """
        return [d["contraction"] for _, _, d in self._graph.edges(data=True)]

    @property
    def num_phases(self):
        """Number of phases in the graph."""
        return self._graph.number_of_nodes()

    @property
    def num_contractions(self):
        """Number of contractions in the graph."""
        return self._graph.number_of_edges()

    def neighbors(self, label):
        """Phases adjacent to the given phase.

        Parameters
        ----------
        label : str
            Phase label.

        Returns
        -------
        list of CalabiYauLite
            Adjacent phase objects.
        """
        return [
            self._graph.nodes[n]["phase"] for n in self._graph.neighbors(label)
        ]

    def get_phase(self, label):
        """Get a phase by label.

        Parameters
        ----------
        label : str
            Phase label.

        Returns
        -------
        CalabiYauLite
        """
        return self._graph.nodes[label]["phase"]

    def __repr__(self):
        return (
            f"PhaseGraph(phases={self.num_phases}, "
            f"contractions={self.num_contractions})"
        )

"""Phase adjacency graph for extended Kahler cone construction.

The :class:`CYGraph` stores CalabiYauLite phases as nodes and
ExtremalContraction objects as edges, backed by a ``networkx.Graph``.

Topology (which phases a contraction connects, and with what curve
orientation) is owned by the graph, not by the contraction object.
"""

import networkx as nx

from .types import CalabiYauLite, ExtremalContraction


class CYGraph:
    """Adjacency graph with CalabiYauLite phases as nodes and
    ExtremalContraction objects as edges.

    Uses an undirected ``networkx.Graph`` internally. Contractions
    connect two phases symmetrically (you can flop in either
    direction). The graph edge stores which phase was ``phase_a``
    and ``phase_b``, along with signed curve orientations.

    Examples
    --------
    >>> g = CYGraph()
    >>> g.add_phase(phase_a)
    >>> g.add_phase(phase_b)
    >>> g.add_contraction(contraction_ab, "A", "B")
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

    def add_contraction(self, contraction, phase_a_label, phase_b_label,
                        curve_sign_a=1, curve_sign_b=-1):
        """Add a contraction edge between two phases.

        The graph owns the topology: which two phases a contraction
        connects, and the signed curve orientation in each phase.

        Parameters
        ----------
        contraction : ExtremalContraction
            The contraction object (no phase references needed).
        phase_a_label : str
            Label of the first phase.
        phase_b_label : str
            Label of the second phase.
        curve_sign_a : int, optional
            Curve sign in phase_a (default +1).
        curve_sign_b : int, optional
            Curve sign in phase_b (default -1).
        """
        self._graph.add_edge(
            phase_a_label, phase_b_label,
            contraction=contraction,
            phase_a=phase_a_label,
            curve_sign_a=curve_sign_a,
            curve_sign_b=curve_sign_b,
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

    def contractions_from(self, label):
        """Contractions incident to a phase, with curve orientation signs.

        For each edge incident to *label*, returns the contraction
        and the signed curve orientation appropriate for that phase.

        Parameters
        ----------
        label : str
            Phase label.

        Returns
        -------
        list of (ExtremalContraction, int)
            Pairs of (contraction, sign) where sign is ``curve_sign_a``
            if *label* was ``phase_a`` when the edge was added, or
            ``curve_sign_b`` otherwise.
        """
        results = []
        for neighbor in self._graph.neighbors(label):
            edge = self._graph.edges[label, neighbor]
            contraction = edge["contraction"]
            if edge["phase_a"] == label:
                sign = edge.get("curve_sign_a", 1)
            else:
                sign = edge.get("curve_sign_b", -1)
            results.append((contraction, sign))
        return results

    def phases_adjacent_to(self, contraction):
        """Find the two phases connected by a contraction.

        Parameters
        ----------
        contraction : ExtremalContraction
            The contraction to look up (identity comparison).

        Returns
        -------
        tuple of (CalabiYauLite, CalabiYauLite) or None
            The two phase objects, or None if the contraction is
            not in the graph.
        """
        for u, v, data in self._graph.edges(data=True):
            if data["contraction"] is contraction:
                return (self.get_phase(u), self.get_phase(v))
        return None

    def __repr__(self):
        return (
            f"CYGraph(phases={self.num_phases}, "
            f"contractions={self.num_contractions})"
        )

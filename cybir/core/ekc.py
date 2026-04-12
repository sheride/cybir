"""CYBirationalClass orchestrator for extended Kahler cone construction.

The main result container and query API for GV-based EKC computation.
Construction is performed by builder modules (``build_gv``, ``weyl``);
this class owns the result data and provides read-only access.

See arXiv:2212.10573 and arXiv:2303.00757 for the underlying theory.
"""

import logging

import numpy as np

from .graph import CYGraph

logger = logging.getLogger("cybir")


class CYBirationalClass:
    """Orchestrator and result container for EKC construction.

    Holds a :class:`CYGraph` of phases and contractions, a reference
    to the root CYTools ``CalabiYau``, cone generators accumulated
    during BFS, and Weyl expansion data.

    Parameters
    ----------
    cy : cytools.calabiyau.CalabiYau
        The root Calabi-Yau threefold.

    Notes
    -----
    Construction follows a step-by-step API (arXiv:2303.00757):

    1. ``ekc = CYBirationalClass(cy)`` -- cheap: wraps CY, creates empty graph
    2. ``ekc.setup_root(max_deg=10)`` -- moderate: computes GVs
    3. ``ekc.construct_phases(verbose=True)`` -- expensive: BFS
    4. ``ekc.expand_weyl()`` -- optional: Weyl orbit expansion

    Or use the convenience classmethod ``CYBirationalClass.from_gv(cy)``.

    Examples
    --------
    >>> ekc = CYBirationalClass.from_gv(cy, max_deg=10)
    >>> ekc.phases
    [CalabiYauLite(label='CY_0'), ...]
    >>> ekc.coxeter_matrix
    array([[...]])
    """

    def __init__(self, cy):
        self._cy = cy
        self._graph = CYGraph()
        self._root_label = None
        self._root_invariants = None  # CYTools Invariants object
        self._coxeter_refs = set()
        self._sym_flop_refs = set()
        self._infinity_cone_gens = set()
        self._eff_cone_gens = set()
        self._build_log = []
        self._constructed = False
        self._weyl_expanded = False
        self._weyl_phases = []  # labels of Weyl-expanded phases

    # --- Step-by-step construction API ---

    def setup_root(self, max_deg=10):
        """Set up the root phase from the CYTools CalabiYau.

        Computes GV invariants and creates the first CalabiYauLite
        phase in the graph.

        Parameters
        ----------
        max_deg : int, optional
            Maximum degree for GV computation. Default 10.
        """
        from .build_gv import setup_root

        setup_root(self, max_deg=max_deg)

    def construct_phases(self, verbose=True, limit=100):
        """Run BFS construction of the extended Kahler cone.

        Iterates over undiagnosed Mori cone walls, classifies each,
        flops when appropriate, and deduplicates phases by curve-sign
        dictionaries.

        Parameters
        ----------
        verbose : bool, optional
            Enable info-level logging. Default True.
        limit : int, optional
            Maximum number of phases. Default 100.
        """
        from .build_gv import construct_phases

        construct_phases(self, verbose=verbose, limit=limit)
        self._constructed = True

    def expand_weyl(self):
        """Expand to the hyperextended cone via Weyl orbit reflections.

        Applies symmetric-flop Coxeter reflections to fundamental-domain
        phases to discover additional phases. Can be called lazily.
        """
        from .weyl import expand_weyl

        expand_weyl(self)
        self._weyl_expanded = True

    @classmethod
    def from_gv(cls, cy, max_deg=10, verbose=True, limit=100):
        """Construct EKC from GV invariants (convenience classmethod).

        Runs ``setup_root`` -> ``construct_phases`` and returns the
        populated ``CYBirationalClass``. Does NOT run ``expand_weyl``
        automatically (call it separately if needed).

        Parameters
        ----------
        cy : cytools.calabiyau.CalabiYau
            The root Calabi-Yau.
        max_deg : int, optional
            Maximum degree for GV computation. Default 10.
        verbose : bool, optional
            Enable info-level logging. Default True.
        limit : int, optional
            Maximum number of phases. Default 100.

        Returns
        -------
        CYBirationalClass
            Populated result object.
        """
        ekc = cls(cy)
        ekc.setup_root(max_deg=max_deg)
        ekc.construct_phases(verbose=verbose, limit=limit)
        return ekc

    # --- Read-only API ---

    @property
    def cy(self):
        """The root CYTools CalabiYau object."""
        return self._cy

    @property
    def graph(self):
        """The phase adjacency graph (:class:`CYGraph`)."""
        return self._graph

    @property
    def phases(self):
        """All CalabiYauLite phase objects.

        Returns
        -------
        list of CalabiYauLite
        """
        return self._graph.phases

    @property
    def contractions(self):
        """All ExtremalContraction objects.

        Returns
        -------
        list of ExtremalContraction
        """
        return self._graph.contractions

    @property
    def root_label(self):
        """Label of the root phase."""
        return self._root_label

    @property
    def root_phase(self):
        """The root CalabiYauLite phase.

        Returns
        -------
        CalabiYauLite or None
        """
        if self._root_label is not None:
            return self._graph.get_phase(self._root_label)
        return None

    @property
    def root_invariants(self):
        """The CYTools Invariants object from the root phase."""
        return self._root_invariants

    @property
    def coxeter_refs(self):
        """Set of Coxeter reflection matrices (as tuples of tuples).

        Returns
        -------
        frozenset
        """
        return frozenset(self._coxeter_refs)

    @property
    def sym_flop_refs(self):
        """Set of symmetric-flop reflection matrices.

        Returns
        -------
        frozenset
        """
        return frozenset(self._sym_flop_refs)

    @property
    def infinity_cone_gens(self):
        """Set of infinity cone generators (curve tuples).

        Returns
        -------
        frozenset
        """
        return frozenset(self._infinity_cone_gens)

    @property
    def eff_cone_gens(self):
        """Set of effective cone generators (divisor tuples).

        Returns
        -------
        frozenset
        """
        return frozenset(self._eff_cone_gens)

    @property
    def coxeter_matrix(self):
        """Coxeter matrix from accumulated reflections, or None.

        Returns
        -------
        numpy.ndarray or None
        """
        if not self._coxeter_refs:
            return None
        from .util import coxeter_matrix

        refs = [np.array(r) for r in self._coxeter_refs]
        return coxeter_matrix(refs)

    @property
    def build_log(self):
        """BFS construction log entries.

        Returns
        -------
        list of dict
        """
        return list(self._build_log)

    @property
    def is_constructed(self):
        """Whether BFS construction has been run.

        Returns
        -------
        bool
        """
        return self._constructed

    @property
    def is_weyl_expanded(self):
        """Whether Weyl expansion has been run.

        Returns
        -------
        bool
        """
        return self._weyl_expanded

    def __repr__(self):
        status = "constructed" if self._constructed else "empty"
        weyl = ", weyl-expanded" if self._weyl_expanded else ""
        return (
            f"CYBirationalClass({status}{weyl}, "
            f"phases={self._graph.num_phases}, "
            f"contractions={self._graph.num_contractions})"
        )

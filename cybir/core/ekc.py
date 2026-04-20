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
    gvs : cytools.calabiyau.Invariants, optional
        Pre-computed GV invariants. If provided, ``setup_root`` skips
        the expensive ``compute_gvs`` call. Useful for caching GVs
        across multiple runs on the same geometry.

    Notes
    -----
    Construction follows a step-by-step API (arXiv:2303.00757):

    1. ``ekc = CYBirationalClass(cy)`` -- cheap: wraps CY, creates empty graph
    2. ``ekc.setup_root(max_deg=10)`` -- moderate: computes GVs
    3. ``ekc.construct_phases(verbose=True)`` -- expensive: BFS
    4. ``ekc.apply_coxeter_orbit()`` -- optional: Coxeter orbit expansion

    Or use the convenience classmethod ``CYBirationalClass.from_gv(cy)``.

    Examples
    --------
    >>> ekc = CYBirationalClass.from_gv(cy, max_deg=10)
    >>> ekc.phases
    [CalabiYauLite(label='CY_0'), ...]
    >>> ekc.coxeter_matrix
    array([[...]])
    """

    def __init__(self, cy, gvs=None):
        self._cy = cy
        self._graph = CYGraph()
        self._root_label = None
        self._root_invariants = gvs  # pre-computed CYTools Invariants, or None
        self._coxeter_refs = set()
        self._sym_flop_refs = set()
        self._infinity_cone_gens = set()
        self._eff_cone_gens = set()
        self._build_log = []
        self._unresolved_walls = []  # walls that could not be classified
        self._constructed = False
        self._weyl_expanded = False
        self._weyl_phases = []  # labels of Weyl-expanded phases
        self._coxeter_type_info = None
        self._coxeter_order = None
        self._coxeter_group = None       # CoxeterGroup dataclass
        self._sym_flop_pairs = []  # list of (ref_tuple, curve_tuple) for chamber walk (WR-04 fix)
        self._nongeneric_cs_pairs = []   # [(ref_tuple, curve_tuple), ...] for SU2_NONGENERIC_CS
        self._su2_pairs = []             # [(ref_tuple, curve_tuple), ...] for genuine SU2

    # --- Step-by-step construction API ---

    def setup_root(self, max_deg=4):
        """Set up the root phase from the CYTools CalabiYau.

        Computes GV invariants and creates the first CalabiYauLite
        phase in the graph.

        Parameters
        ----------
        max_deg : int, optional
            Initial maximum degree for GV computation. Default 4.
            The BFS will adaptively recompute to higher degrees if
            needed.
        """
        from .build_gv import setup_root

        setup_root(self, max_deg=max_deg)

    def construct_phases(self, verbose=True, limit=100,
                         max_deg_ceiling=20, deg_step=2,
                         validate_stability=False, check_toric=False):
        """Run BFS construction of the extended Kahler cone.

        Iterates over undiagnosed Mori cone walls, classifies each,
        flops when appropriate, and deduplicates phases by curve-sign
        dictionaries. Adaptively recomputes GVs to higher degree when
        walls cannot be classified at the current degree.

        Parameters
        ----------
        verbose : bool, optional
            Enable info-level logging. Default True.
        limit : int, optional
            Maximum number of phases. Default 100.
        max_deg_ceiling : int, optional
            Maximum degree to recompute GVs to. Default 20.
        deg_step : int, optional
            Degree increment per retry round. Default 2.
        validate_stability : bool, optional
            If True, after BFS completes, bump degree and re-run to
            verify results are unchanged. Default False.
        check_toric : bool, optional
            If True, detect FRST phases and compile toric curves
            incrementally. Enables phase classification and Mori
            cone bounds. Default False.
        """
        from .build_gv import construct_phases

        construct_phases(self, verbose=verbose, limit=limit,
                         max_deg_ceiling=max_deg_ceiling, deg_step=deg_step,
                         validate_stability=validate_stability,
                         check_toric=check_toric)
        self._constructed = True

    def apply_coxeter_orbit(self, reflections='ekc', phases=True):
        """Expand to the extended/hyperextended cone via Coxeter group orbit.

        Parameters
        ----------
        reflections : str or iterable, optional
            Which reflections to use for orbit expansion:

            - ``'ekc'`` (default): symmetric flop reflections only (produces EKC)
            - ``'hekc'``: sym flop + SU2_NONGENERIC_CS (produces HEKC)
            - ``'all'``: all Coxeter reflections (full group)
            - Custom iterable of reflection matrices
        phases : bool, optional
            If True (default), create full reflected phase objects.
            If False, only accumulate cone generators.

        See Also
        --------
        arXiv:2212.10573 Section 4.3
        """
        from .coxeter import apply_coxeter_orbit

        apply_coxeter_orbit(self, reflections=reflections, phases=phases)
        self._weyl_expanded = True

    def invariants_for(self, phase_label):
        """Reconstruct GV invariants for a phase on demand.

        Picks a tip point in the phase's Kahler cone and re-orients
        flop curves that pair negatively with that point, starting
        from the root invariants.

        Parameters
        ----------
        phase_label : str
            Label of the phase.

        Returns
        -------
        Invariants
            CYTools Invariants with flop curves reoriented for this phase.

        See Also
        --------
        arXiv:2212.10573 Section 4.3
        """
        from .coxeter import _invariants_for_impl

        return _invariants_for_impl(self, phase_label)

    def to_fundamental_domain(self, point):
        """Map a point to the fundamental domain via chamber walk.

        Reflects the point through symmetric-flop walls that pair
        negatively until it lies in the fundamental domain.

        Parameters
        ----------
        point : array_like
            Point in Mori space.

        Returns
        -------
        (numpy.ndarray, numpy.ndarray)
            ``(fundamental_domain_point, group_element)`` where the group
            element maps the fundamental domain to the input chamber.

        See Also
        --------
        arXiv:2212.10573 Section 4.3
        """
        from .coxeter import to_fundamental_domain

        reflections = [np.array(r) for r, _ in self._sym_flop_pairs]
        curves = [np.array(c) for _, c in self._sym_flop_pairs]
        return to_fundamental_domain(np.asarray(point), reflections, curves)

    @classmethod
    def from_gv(cls, cy, max_deg=4, verbose=True, limit=100, gvs=None,
                max_deg_ceiling=20, deg_step=2, validate_stability=False,
                check_toric=False):
        """Construct EKC from GV invariants (convenience classmethod).

        Runs ``setup_root`` -> ``construct_phases`` and returns the
        populated ``CYBirationalClass``. Does NOT run ``apply_coxeter_orbit``
        automatically (call it separately if needed).

        Parameters
        ----------
        cy : cytools.calabiyau.CalabiYau
            The root Calabi-Yau.
        max_deg : int, optional
            Initial maximum degree for GV computation. Default 4.
            The BFS adaptively recomputes to higher degrees if needed.
        verbose : bool, optional
            Enable info-level logging. Default True.
        limit : int, optional
            Maximum number of phases. Default 100.
        gvs : cytools.calabiyau.Invariants, optional
            Pre-computed GV invariants. If provided, skips the expensive
            ``compute_gvs`` call in ``setup_root``. Useful for caching
            GVs across multiple runs.
        max_deg_ceiling : int, optional
            Maximum degree to recompute GVs to. Default 20.
        deg_step : int, optional
            Degree increment per retry round. Default 2.
        validate_stability : bool, optional
            If True, after BFS completes, bump degree and re-run to
            verify results are unchanged. Default False.
        check_toric : bool, optional
            If True, detect FRST phases and compile toric curves
            incrementally. Default False.

        Returns
        -------
        CYBirationalClass
            Populated result object.
        """
        # Guard: non-favorable polytopes cannot compute GV-based EKC
        if hasattr(cy, 'polytope') and callable(cy.polytope):
            poly = cy.polytope()
            if hasattr(poly, 'is_favorable') and not poly.is_favorable('N'):
                poly_id = poly.id() if hasattr(poly, 'id') else "unknown"
                raise ValueError(
                    f"Non-favorable polytope (polytope ID {poly_id}): cannot "
                    "compute GV-based EKC. The polytope is not favorable in "
                    "the N-lattice."
                )

        ekc = cls(cy, gvs=gvs)
        ekc.setup_root(max_deg=max_deg)
        ekc.construct_phases(verbose=verbose, limit=limit,
                             max_deg_ceiling=max_deg_ceiling,
                             deg_step=deg_step,
                             validate_stability=validate_stability,
                             check_toric=check_toric)
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
    def coxeter_group(self):
        """CoxeterGroup dataclass with factors, order, rank, repr.

        Set by :meth:`apply_coxeter_orbit`. Returns None if orbit
        expansion has not been run.

        Returns
        -------
        CoxeterGroup or None
        """
        return self._coxeter_group

    @property
    def coxeter_type(self):
        """Coxeter group type classification, or None.

        Set by :meth:`apply_coxeter_orbit`. Returns a list of
        ``(type_string, rank, order)`` tuples for each irreducible
        component.

        Returns
        -------
        list of tuple or None
        """
        return self._coxeter_type_info

    @property
    def coxeter_order(self):
        """Order |W| of the Coxeter group, or None.

        Set by :meth:`apply_coxeter_orbit`.

        Returns
        -------
        int or None
        """
        return self._coxeter_order

    @property
    def coxeter_matrix(self):
        """Coxeter matrix from accumulated reflections, or None.

        Returns
        -------
        numpy.ndarray or None
        """
        if not self._coxeter_refs:
            return None
        from .coxeter import coxeter_element

        refs = [np.array(r) for r in self._coxeter_refs]
        return coxeter_element(refs)

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

    # --- Phase classification API (D-14) ---

    def phase_type(self, phase_label):
        """Classification of a phase as FRST, vex, or non-inherited.

        Only available when ``check_toric=True`` was passed to
        ``construct_phases``.

        Parameters
        ----------
        phase_label : str
            Label of the phase.

        Returns
        -------
        str or None
            One of ``'frst'``, ``'vex'``, ``'non_inherited'``, or None
            if toric checking was not enabled.
        """
        return getattr(self, '_phase_types', {}).get(phase_label)

    def frst_phases(self):
        """Labels of all FRST phases.

        Returns
        -------
        list of str
        """
        return [l for l, t in getattr(self, '_phase_types', {}).items()
                if t == 'frst']

    def vex_phases(self):
        """Labels of all vex phases.

        Returns
        -------
        list of str
        """
        return [l for l, t in getattr(self, '_phase_types', {}).items()
                if t == 'vex']

    def non_inherited_phases(self):
        """Labels of all non-inherited phases.

        Returns
        -------
        list of str
        """
        return [l for l, t in getattr(self, '_phase_types', {}).items()
                if t == 'non_inherited']

    # --- Mori cone bounds (D-09) ---

    def mori_cone_outer(self, phase_label):
        """Outer Mori cone bound from CYTools mori_cone_cap.

        Available only for FRST phases.

        Parameters
        ----------
        phase_label : str

        Returns
        -------
        cytools.Cone or None
        """
        try:
            phase = self._graph.get_phase(phase_label)
        except (KeyError, Exception):
            return None
        if phase is None or phase.mori_cone is None:
            return None
        return phase.mori_cone

    def mori_cone_inner(self, phase_label):
        """Inner Mori cone bound from toric curves.

        Available only when ``check_toric=True`` was used and toric
        curves have been computed for this phase.

        Parameters
        ----------
        phase_label : str

        Returns
        -------
        cytools.Cone or None
        """
        tcd = getattr(self, '_toric_curve_data', None)
        if tcd is None:
            return None
        try:
            phase = self._graph.get_phase(phase_label)
        except (KeyError, Exception):
            return None
        if phase is None or phase.tip is None:
            return None

        from .toric_curves import orient_curves_for_phase
        all_curves = tcd.all_curves()
        if not all_curves:
            return None

        oriented = orient_curves_for_phase(all_curves, phase.tip)
        rays = np.array([c for c in oriented if not np.allclose(c, 0)])
        if len(rays) == 0:
            return None

        import cytools
        return cytools.Cone(rays=rays)

    def mori_cone_exact(self, phase_label):
        """Exact Mori cone if inner == outer bounds match.

        Returns
        -------
        cytools.Cone or None
        """
        inner = self.mori_cone_inner(phase_label)
        outer = self.mori_cone_outer(phase_label)
        if inner is None or outer is None:
            return None
        # Check if they are the same cone (same rays up to scaling)
        try:
            inner_rays = set(tuple(r) for r in inner.rays())
            outer_rays = set(tuple(r) for r in outer.rays())
            if inner_rays == outer_rays:
                return outer
        except Exception:
            pass
        return None

    # --- Toric curves accessor (D-10) ---

    def toric_curves(self, phase_label=None):
        """Access toric curve data, optionally re-oriented for a phase.

        Parameters
        ----------
        phase_label : str, optional
            If provided, re-orient curves for this phase's Kahler cone.
            If None, return curves in canonical orientation.

        Returns
        -------
        ToricCurveData or None
        """
        tcd = getattr(self, '_toric_curve_data', None)
        if tcd is None:
            return None
        if phase_label is None:
            return tcd

        phase = self._graph.get_phase(phase_label)
        if phase is None or phase.tip is None:
            return tcd

        from .toric_curves import orient_curves_for_phase, ToricCurveData
        return ToricCurveData(
            flop_curves=orient_curves_for_phase(tcd.flop_curves, phase.tip),
            weyl_curves_g0=orient_curves_for_phase(
                tcd.weyl_curves_g0, phase.tip
            ),
            weyl_curves_higher_genus=orient_curves_for_phase(
                tcd.weyl_curves_higher_genus, phase.tip
            ),
            other_curves=orient_curves_for_phase(
                tcd.other_curves, phase.tip
            ),
            minface1_curves=orient_curves_for_phase(
                tcd.minface1_curves, phase.tip
            ),
            gv_dict=tcd.gv_dict,
        )

    # --- Active Mori verification (D-09) ---

    def _verify_mori_bounds(self, phase_label):
        """Verify inner <= discovered Mori <= outer and cross-check toric GVs.

        Called from ``_run_bfs`` after toric curves are compiled for an
        FRST phase. Checks that all inner-bound rays satisfy outer-bound
        inequalities. Cross-validates toric GV invariants against
        computed GV invariants. Logs warnings on discrepancies.

        Parameters
        ----------
        phase_label : str
            Label of the FRST phase to verify.
        """
        inner = self.mori_cone_inner(phase_label)
        outer = self.mori_cone_outer(phase_label)

        if inner is not None and outer is not None:
            # Check inner <= outer: every inner ray should be in outer cone
            try:
                if not outer.contains(inner):
                    logger.warning(
                        "Mori bound violation for %s: inner cone NOT contained "
                        "in outer cone. Some toric curves lie outside "
                        "mori_cone_cap.",
                        phase_label,
                    )
                else:
                    logger.info(
                        "Mori bounds consistent for %s: inner <= outer",
                        phase_label,
                    )
            except Exception as exc:
                logger.warning(
                    "Could not verify Mori bounds for %s: %s",
                    phase_label, exc,
                )

        # Cross-check toric GVs against computed GVs
        tcd = getattr(self, '_toric_curve_data', None)
        if (
            tcd is not None
            and tcd.gv_dict
            and hasattr(self, '_root_invariants')
            and self._root_invariants is not None
        ):
            phase = self._graph.get_phase(phase_label)
            if phase is not None and phase.tip is not None:
                from .toric_curves import orient_curves_for_phase
                for curve_tuple, toric_gv in tcd.gv_dict.items():
                    curve_arr = np.array(curve_tuple)
                    # Orient for this phase
                    sign = np.sign(phase.tip @ curve_arr)
                    if sign < 0:
                        curve_arr = -curve_arr
                    # Try to get computed GV for this curve
                    try:
                        series = self._root_invariants.gv_series_cybir(
                            curve_arr
                        )
                        if series and len(series) > 0:
                            computed_gv = series[0]
                            if computed_gv != toric_gv:
                                logger.warning(
                                    "Toric GV mismatch for curve %s in "
                                    "phase %s: toric=%s, computed=%s",
                                    tuple(int(x) for x in curve_arr),
                                    phase_label, toric_gv, computed_gv,
                                )
                    except Exception:
                        pass  # Curve may not be in computed GV range

    def __repr__(self):
        if not self._constructed:
            return "CYBirationalClass(empty)"

        total = self._graph.num_phases
        n_weyl = len(self._weyl_phases)
        fundamental = total - n_weyl

        if self._weyl_expanded and self._coxeter_group is not None:
            type_str = repr(self._coxeter_group)
            order = self._coxeter_group.order
            return (
                f"CYBirationalClass({total} phases "
                f"({fundamental} fundamental), "
                f"orbit={type_str} |W|={order})"
            )
        elif self._weyl_expanded and self._coxeter_type_info:
            # Backward compat fallback
            type_parts = []
            for t, rank, _order in self._coxeter_type_info:
                type_parts.append(f"{t}{rank}")
            type_str = " x ".join(type_parts)
            order = self._coxeter_order or "?"
            return (
                f"CYBirationalClass({total} phases "
                f"({fundamental} fundamental), "
                f"orbit={type_str} |W|={order})"
            )
        elif self._weyl_expanded:
            return (
                f"CYBirationalClass({total} phases "
                f"({fundamental} fundamental), orbit expanded)"
            )
        else:
            return (
                f"CYBirationalClass({total} phases, "
                f"no orbit expansion)"
            )

"""Core data types for cybir.

Provides CalabiYauLite, ExtremalContraction, ContractionType,
and InsufficientGVError. Full implementation in Task 2.
"""

import enum

import numpy as np


# --- Notation mappings for ContractionType (module-level to avoid enum pitfalls) ---

_WILSON_NOTATION = {
    "ASYMPTOTIC": "Type III",
    "CFT": "Type II",
    "SU2": "Type I",
    "SYMMETRIC_FLOP": "Symmetric Flop",
    "FLOP": "Flop",
}

_PAPER_NOTATION = {
    "ASYMPTOTIC": "asymptotic",
    "CFT": "CFT",
    "SU2": "su(2) enhancement",
    "SYMMETRIC_FLOP": "symmetric flop",
    "FLOP": "generic flop",
}


class InsufficientGVError(RuntimeError):
    """Raised when GV series has not been computed to high enough degree."""

    pass


class ContractionType(enum.Enum):
    """Type of extremal birational contraction.

    Five types following the classification in arXiv:2212.10573:
    asymptotic, CFT, su(2) enhancement, symmetric flop, generic flop.
    """

    ASYMPTOTIC = "asymptotic"
    CFT = "CFT"
    SU2 = "su2"
    SYMMETRIC_FLOP = "symmetric_flop"
    FLOP = "flop"

    def display_name(self, notation="paper"):
        """Return human-readable name in the given notation.

        Parameters
        ----------
        notation : str
            Either ``"paper"`` (default) for arXiv notation or
            ``"wilson"`` for Wilson's Type I/II/III convention.

        Returns
        -------
        str
        """
        if notation == "wilson":
            return _WILSON_NOTATION[self.name]
        return _PAPER_NOTATION[self.name]


class CalabiYauLite:
    """Lightweight container for Calabi-Yau phase data.

    Stores precomputed intersection numbers, second Chern class,
    cones, and charge matrices. Interface-compatible with the
    dbrane-tools ``CalabiYauLite`` class, with additional fields
    for GV invariants and a phase label.

    Mutable during construction; call :meth:`freeze` to make
    immutable after the EKC orchestrator finishes building.

    Parameters
    ----------
    int_nums : numpy.ndarray
        Triple intersection numbers :math:`\\kappa_{ijk}`.
    c2 : numpy.ndarray, optional
        Second Chern class :math:`c_2 \\cdot D_i`.
    kahler_cone : optional
        Kahler cone (``cytools.Cone``).
    mori_cone : optional
        Mori cone (``cytools.Cone``).
    polytope : optional
        The underlying polytope.
    charges : optional
        CY charge matrix.
    indices : optional
        CY labels list.
    eff_cone : optional
        Effective cone (``cytools.Cone``).
    triangulation : optional
        A ``cytools.triangulation.Triangulation``.
    fan : optional
        A ``cytools.vector_config.fan.Fan``.
    gv_invariants : optional
        Reference to a CYTools Invariants object.
    label : optional
        Phase identifier for the adjacency graph.
    """

    def __init__(
        self,
        int_nums,
        c2=None,
        kahler_cone=None,
        mori_cone=None,
        polytope=None,
        charges=None,
        indices=None,
        eff_cone=None,
        triangulation=None,
        fan=None,
        gv_invariants=None,
        label=None,
    ):
        self._int_nums = np.asarray(int_nums)
        self._c2 = np.asarray(c2) if c2 is not None else None
        self._kahler_cone = kahler_cone
        self._mori_cone = mori_cone
        self._polytope = polytope
        self._charges = charges
        self._indices = indices
        self._eff_cone = eff_cone
        self._triangulation = triangulation
        self._fan = fan
        self._gv_invariants = gv_invariants
        self._label = label
        self._frozen = False

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name != "_frozen":
            raise AttributeError(
                f"Cannot modify frozen CalabiYauLite (attribute '{name}')"
            )
        super().__setattr__(name, value)

    # --- Properties ---

    @property
    def int_nums(self):
        """Triple intersection numbers :math:`\\kappa_{ijk}`."""
        return np.copy(self._int_nums)

    @property
    def c2(self):
        """Second Chern class :math:`c_2 \\cdot D_i`."""
        if self._c2 is not None:
            return np.copy(self._c2)
        return None

    @property
    def kahler_cone(self):
        """Kahler cone (``cytools.Cone``)."""
        return self._kahler_cone

    @property
    def mori_cone(self):
        """Mori cone (``cytools.Cone``)."""
        return self._mori_cone

    @property
    def polytope(self):
        """The underlying polytope."""
        return self._polytope

    @property
    def charges(self):
        """CY charge matrix."""
        return self._charges

    @property
    def indices(self):
        """CY labels list."""
        return self._indices

    @property
    def eff_cone(self):
        """Effective cone (``cytools.Cone``)."""
        return self._eff_cone

    @property
    def triangulation(self):
        """A ``cytools.triangulation.Triangulation``."""
        return self._triangulation

    @property
    def fan(self):
        """A ``cytools.vector_config.fan.Fan``."""
        return self._fan

    @property
    def gv_invariants(self):
        """Reference to a CYTools Invariants object."""
        return self._gv_invariants

    @property
    def label(self):
        """Phase identifier for the adjacency graph."""
        return self._label

    # --- Freeze mechanism ---

    def freeze(self):
        """Make this object immutable.

        Called by the EKC orchestrator after construction is complete.
        After freezing, any attempt to set an attribute raises
        ``AttributeError``.
        """
        self._frozen = True

    # --- Dunder methods ---

    def __eq__(self, other):
        if not isinstance(other, CalabiYauLite):
            return NotImplemented
        if not np.allclose(self._int_nums, other._int_nums):
            return False
        if self._c2 is not None and other._c2 is not None:
            if not np.allclose(self._c2, other._c2):
                return False
        return True

    def __hash__(self):
        return hash(self._label)

    def __repr__(self):
        return f"CalabiYauLite(label={self._label!r})"


class ExtremalContraction:
    """An extremal birational contraction between two CY3 phases.

    Represents a wall in the extended Kahler cone where a curve
    shrinks to zero volume. Frozen by default after construction.

    Parameters
    ----------
    flopping_curve : numpy.ndarray
        The curve class that shrinks at this wall.
    start_phase : CalabiYauLite, optional
        Phase on one side of the wall.
    end_phase : CalabiYauLite, optional
        Phase on the other side of the wall.
    contraction_type : ContractionType, optional
        Classification of this contraction.
    gv_invariant : int, optional
        Gopakumar-Vafa invariant for the flopping curve.
    effective_gv : int, optional
        Effective GV invariant (accounting for multiplicity).
    zero_vol_divisor : numpy.ndarray, optional
        Divisor that shrinks at this wall.
    coxeter_reflection : numpy.ndarray, optional
        Coxeter reflection matrix for this contraction.
    """

    def __init__(
        self,
        flopping_curve,
        start_phase=None,
        end_phase=None,
        contraction_type=None,
        gv_invariant=None,
        effective_gv=None,
        zero_vol_divisor=None,
        coxeter_reflection=None,
    ):
        self._flopping_curve = np.asarray(flopping_curve)
        self._start_phase = start_phase
        self._end_phase = end_phase
        self._contraction_type = contraction_type
        self._gv_invariant = gv_invariant
        self._effective_gv = effective_gv
        self._zero_vol_divisor = zero_vol_divisor
        self._coxeter_reflection = coxeter_reflection
        self._frozen = True

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name != "_frozen":
            raise AttributeError(
                f"Cannot modify frozen ExtremalContraction (attribute '{name}')"
            )
        super().__setattr__(name, value)

    # --- Properties ---

    @property
    def flopping_curve(self):
        """The curve class that shrinks at this wall."""
        return self._flopping_curve

    @property
    def start_phase(self):
        """Phase on one side of the wall."""
        return self._start_phase

    @property
    def end_phase(self):
        """Phase on the other side of the wall."""
        return self._end_phase

    @property
    def contraction_type(self):
        """Classification of this contraction."""
        return self._contraction_type

    @property
    def gv_invariant(self):
        """Gopakumar-Vafa invariant for the flopping curve."""
        return self._gv_invariant

    @property
    def effective_gv(self):
        """Effective GV invariant (accounting for multiplicity)."""
        return self._effective_gv

    @property
    def zero_vol_divisor(self):
        """Divisor that shrinks at this wall."""
        return self._zero_vol_divisor

    @property
    def coxeter_reflection(self):
        """Coxeter reflection matrix for this contraction."""
        return self._coxeter_reflection

    # --- Dunder methods ---

    def __repr__(self):
        return (
            f"ExtremalContraction(flopping_curve={self._flopping_curve},"
            f" type={self._contraction_type})"
        )

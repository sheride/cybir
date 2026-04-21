"""Core data types for cybir.

Provides CalabiYauLite, ExtremalContraction, ContractionType,
CoxeterGroup, and InsufficientGVError.
"""

import enum
from dataclasses import dataclass

import numpy as np


# --- Notation mappings for ContractionType (module-level to avoid enum pitfalls) ---

_WILSON_NOTATION = {
    "ASYMPTOTIC": "Type III",
    "CFT": "Type II",
    "SU2": "Type I",
    "SU2_NONGENERIC_CS": "Type I (non-generic CS)",
    "SYMMETRIC_FLOP": "Symmetric Flop",
    "GROSS_FLOP": "Gross Flop",
    "FLOP": "Flop",
    "UNRESOLVED": "Unresolved (degree cap)",
}

_PAPER_NOTATION = {
    "ASYMPTOTIC": "asymptotic",
    "CFT": "CFT",
    "SU2": "su(2) enhancement",
    "SU2_NONGENERIC_CS": "su(2) enhancement (non-generic CS)",
    "SYMMETRIC_FLOP": "symmetric flop",
    "GROSS_FLOP": "gross flop",
    "FLOP": "generic flop",
    "UNRESOLVED": "unresolved (degree cap)",
}


class InsufficientGVError(RuntimeError):
    """Raised when GV series has not been computed to high enough degree."""

    pass


class ContractionType(enum.Enum):
    """Type of extremal birational contraction.

    Eight types following the classification in arXiv:2212.10573:
    asymptotic, CFT, su(2) enhancement, su(2) enhancement at
    non-generic complex structure, symmetric flop, gross flop,
    generic flop, plus an ``UNRESOLVED`` sentinel for walls that
    require higher GV degree than the ceiling allows.
    """

    ASYMPTOTIC = "asymptotic"
    CFT = "CFT"
    SU2 = "su2"
    SU2_NONGENERIC_CS = "su2_nongeneric_cs"
    SYMMETRIC_FLOP = "symmetric_flop"
    GROSS_FLOP = "gross_flop"
    FLOP = "flop"
    UNRESOLVED = "unresolved"

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
        curve_signs=None,
        tip=None,
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
        self._curve_signs = dict(curve_signs) if curve_signs is not None else None
        self._tip = np.asarray(tip) if tip is not None else None
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

    @property
    def curve_signs(self):
        """Curve-sign dictionary {curve_tuple: +1/-1}.

        Records the sign of ``tip @ curve`` for each known flop curve.
        Persisted during BFS construction for use in orbit expansion
        and on-demand GV reconstruction (D-15).
        """
        if self._curve_signs is not None:
            return dict(self._curve_signs)
        return None

    @property
    def tip(self):
        """Interior point of the Kahler cone.

        Persisted during BFS construction for use in orbit expansion
        and curve-sign computation (D-15).
        """
        if self._tip is not None:
            return np.copy(self._tip)
        return None

    # --- Freeze mechanism ---

    def freeze(self):
        """Make this object immutable.

        Called by the EKC orchestrator after construction is complete.
        After freezing, any attempt to set an attribute raises
        ``AttributeError``.
        """
        self._frozen = True

    # --- Convenience methods ---

    def flop(self, curve, gv_series, label=None):
        """Create a new phase by flopping across a wall.

        Thin wrapper around :func:`cybir.core.flop.flop_phase`.

        Parameters
        ----------
        curve : numpy.ndarray
            Flopping curve class.
        gv_series : list[int]
            GV series for the flopping curve.
        label : str, optional
            Label for the new phase.

        Returns
        -------
        CalabiYauLite
            New phase with transformed intersection numbers and c2.
        """
        from .flop import flop_phase

        return flop_phase(self, curve, gv_series, label=label)

    # --- Dunder methods ---

    def __eq__(self, other):
        if not isinstance(other, CalabiYauLite):
            return NotImplemented
        if not np.allclose(self._int_nums, other._int_nums):
            return False
        if (self._c2 is None) != (other._c2 is None):
            return False
        if self._c2 is not None and other._c2 is not None:
            if not np.allclose(self._c2, other._c2):
                return False
        return True

    def __hash__(self):
        if self._label is not None:
            return hash(self._label)
        return hash(self._int_nums.tobytes())

    def __repr__(self):
        h11 = self._int_nums.shape[0]
        if h11 <= 3:
            return self.__str__()
        return f"CalabiYauLite(label={self._label!r}, h11={h11})"

    def __str__(self):
        h11 = self._int_nums.shape[0]
        # Collect nonzero intersection numbers (upper triangular)
        indices = np.triu_indices(h11, m=h11)  # not quite right for rank-3 tensor
        # Flatten the symmetric rank-3 tensor: collect unique entries
        nonzero_entries = []
        for i in range(h11):
            for j in range(i, h11):
                for k in range(j, h11):
                    val = self._int_nums[i, j, k]
                    if val != 0:
                        nonzero_entries.append(int(val))

        if h11 > 10:
            display_entries = nonzero_entries[:20]
            suffix = ", ..." if len(nonzero_entries) > 20 else ""
        else:
            display_entries = nonzero_entries
            suffix = ""

        parts = [f"label={self._label!r}", f"h11={h11}"]
        parts.append(f"kappa={display_entries}{suffix}")

        if self._c2 is not None:
            parts.append(f"c2={self._c2.tolist()}")

        if self._kahler_cone is not None:
            try:
                n_rays = len(self._kahler_cone.rays())
                parts.append(f"kahler_rays={n_rays}")
            except Exception:
                pass

        return f"CalabiYauLite({', '.join(parts)})"


class ExtremalContraction:
    """An extremal birational contraction between two CY3 phases.

    Represents a wall in the extended Kahler cone where a curve
    shrinks to zero volume. Frozen by default after construction.

    Parameters
    ----------
    contraction_curve : numpy.ndarray
        The curve class that shrinks at this wall.
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
    gv_series : list of int, optional
        GV series :math:`[n^0_{[\\mathcal{C}]}, n^0_{2[\\mathcal{C}]}, \\ldots]`.
    gv_eff_1 : int, optional
        Linear effective GV invariant :math:`\\sum_k k \\, n^0_{k[\\mathcal{C}]}`.
    cone_face : optional
        Reference to the Mori cone face associated with this contraction.
    toric_origin : str, optional
        Toric origin tag (e.g. ``"flop"``) when this contraction was
        identified from toric data.
    """

    def __init__(
        self,
        contraction_curve,
        contraction_type=None,
        gv_invariant=None,
        effective_gv=None,
        zero_vol_divisor=None,
        coxeter_reflection=None,
        gv_series=None,
        gv_eff_1=None,
        cone_face=None,
        toric_origin=None,
    ):
        self._contraction_curve = np.asarray(contraction_curve)
        self._contraction_type = contraction_type
        self._gv_invariant = gv_invariant
        self._effective_gv = effective_gv
        self._zero_vol_divisor = zero_vol_divisor
        self._coxeter_reflection = coxeter_reflection
        self._gv_series = list(gv_series) if gv_series is not None else None
        self._gv_eff_1 = gv_eff_1
        self._cone_face = cone_face
        self._toric_origin = toric_origin
        self._frozen = True

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name != "_frozen":
            raise AttributeError(
                f"Cannot modify frozen ExtremalContraction (attribute '{name}')"
            )
        super().__setattr__(name, value)

    # --- Properties ---

    @property
    def contraction_curve(self):
        """The curve class that shrinks at this wall."""
        return self._contraction_curve

    @property
    def cone_face(self):
        """Mori cone face associated with this contraction."""
        return self._cone_face

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

    @property
    def gv_series(self):
        """GV series :math:`[n^0_{[\\mathcal{C}]}, n^0_{2[\\mathcal{C}]}, \\ldots]`."""
        if self._gv_series is not None:
            return list(self._gv_series)  # defensive copy
        return None

    @property
    def gv_eff_1(self):
        """Linear effective GV invariant :math:`\\sum_k k \\, n^0_{k[\\mathcal{C}]}`."""
        return self._gv_eff_1

    # --- Dunder methods ---

    def __repr__(self):
        parts = []
        # Type display name
        if self._contraction_type is not None:
            parts.append(self._contraction_type.display_name())
        else:
            parts.append("unclassified")

        # Curve as list of ints
        curve_list = [int(x) for x in self._contraction_curve]
        parts.append(f"curve={curve_list}")

        # Zero-vol divisor
        if self._zero_vol_divisor is not None:
            zvd_list = [int(x) for x in self._zero_vol_divisor]
            parts.append(f"zvd={zvd_list}")

        # GV series (only for small h11, i.e. short curves)
        if self._gv_series is not None and len(self._contraction_curve) <= 10:
            parts.append(f"gv={self._gv_series}")

        return f"ExtremalContraction({', '.join(parts)})"

    @property
    def toric_origin(self):
        """Toric origin tag for this contraction, if any."""
        return self._toric_origin


@dataclass(frozen=True)
class CoxeterGroup:
    """Coxeter group data from orbit expansion.

    Parameters
    ----------
    factors : tuple
        Tuple of (family, rank, order) tuples, one per irreducible component.
    order_matrix : object
        The Coxeter order matrix m_ij (numpy.ndarray).
    reflections : tuple
        The generator reflection matrices as a tuple of numpy arrays.
    """

    factors: tuple
    order_matrix: object  # numpy.ndarray, use object to avoid frozen issues
    reflections: tuple

    @property
    def order(self):
        """Total group order |W| (product of factor orders)."""
        result = 1
        for _, _, o in self.factors:
            result *= o
        return result

    @property
    def rank(self):
        """Total rank (sum of factor ranks)."""
        return sum(r for _, r, _ in self.factors)

    def __repr__(self):
        _sub = str.maketrans(
            "0123456789", "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089"
        )
        parts = []
        for family, rank, _ in self.factors:
            parts.append(f"{family}{str(rank).translate(_sub)}")
        return " \u00d7 ".join(parts)

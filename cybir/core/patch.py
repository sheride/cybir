"""CYTools monkey-patches for cybir integration.

Provides ``patch_cytools()`` to add GV flop-tracking methods to the
CYTools ``Invariants`` class and convenience entry points to
``CalabiYau`` and ``Polytope``.

The patches are applied *explicitly* -- never on import -- so that
cybir can be used for offline analysis without CYTools present.

See arXiv:2303.00757 Section 2 for the GV propagation logic and
arXiv:2212.10573 Section 4 for the contraction classification that
motivates these methods.
"""

import copy as copy_library
import inspect
import logging
import warnings

import numpy as np

logger = logging.getLogger("cybir")

# Track whether patches have been applied (idempotent guard)
_patched = False


# ---------------------------------------------------------------------------
# Helper functions (translated from original extended_kahler_cone.py)
# ---------------------------------------------------------------------------

def _is_parallel(x, y):
    """Check if two vectors are parallel (same direction)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    norm = np.sqrt((x @ x) * (y @ y))
    if norm == 0:
        return False
    return np.allclose(x @ y / norm, 1, atol=1e-4)


def _is_antiparallel(x, y):
    """Check if two vectors are antiparallel (opposite direction)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    norm = np.sqrt((x @ x) * (y @ y))
    if norm == 0:
        return False
    return np.allclose(x @ y / norm, -1, atol=1e-4)


def _is_aligned(x, y):
    """Check if two vectors are parallel or antiparallel."""
    return _is_parallel(x, y) or _is_antiparallel(x, y)


# ---------------------------------------------------------------------------
# Invariants method implementations
# ---------------------------------------------------------------------------

def _invariants_copy(self):
    """Deep-copy an Invariants object, preserving flop-tracking attributes.

    Creates a new ``Invariants`` instance with the same GV data and
    copies the ``flop_curves`` and ``precompose`` attributes added
    by cybir.

    Returns
    -------
    Invariants
        A deep copy.
    """
    new_gvs = type(self)(
        invariant_type="gv",
        charge2invariant=copy_library.deepcopy(self._charge2invariant),
        grading_vec=self.grading_vec,
        cutoff=self.cutoff,
        calabiyau=self._cy,
        basis=self._basis,
    )
    # Copy cybir-specific attributes
    if hasattr(self, "flop_curves"):
        new_gvs.flop_curves = copy_library.deepcopy(self.flop_curves)
    else:
        new_gvs.flop_curves = []
    if hasattr(self, "precompose"):
        new_gvs.precompose = copy_library.deepcopy(self.precompose)
    else:
        new_gvs.precompose = np.eye(len(self.grading_vec))
    return new_gvs


def _invariants_flop_gvs(self, curves, do_ensure_nilpotency=False, **kwargs):
    """Clone Invariants with flop-curve tracking updated.

    For each curve in *curves*, toggles it in the ``flop_curves``
    list: if the negation is already tracked, removes it (double-flop
    cancels); otherwise appends the curve.

    This is a faithful translation of the original
    ``extended_kahler_cone.py`` lines 2655-2670.

    Parameters
    ----------
    curves : list of array_like
        Flopping curves to apply.
    do_ensure_nilpotency : bool, optional
        If True, call ensure_nilpotency for each curve first.

    Returns
    -------
    Invariants
        New Invariants with updated flop tracking.
    """
    obj = self
    if do_ensure_nilpotency:
        for curve in curves:
            obj = obj.ensure_nilpotency(curve, **kwargs)

    new_gvs = obj.copy()

    for curve in curves:
        neg_tuple = tuple(-np.asarray(curve))
        if neg_tuple in new_gvs.flop_curves:
            new_gvs.flop_curves.remove(neg_tuple)
        else:
            new_gvs.flop_curves.append(tuple(curve))

    return new_gvs


def _invariants_gv_incl_flop(self, curve, check_deg=True):
    """Look up GV invariant accounting for flop sign flips and basis change.

    Translates the original ``gv_incl_flop`` (lines 2672-2684):

    1. For each tracked flop curve, if the query curve is aligned
       (parallel or antiparallel), negate the curve (sign flip).
    2. Apply the ``precompose`` basis change.
    3. Look up via ``self.gv()``.

    Parameters
    ----------
    curve : array_like
        Curve class in the current (possibly flopped) basis.
    check_deg : bool, optional
        Whether to check degree bounds (passed to ``self.gv``).

    Returns
    -------
    int or None
        The GV invariant, or None if outside computed range.
    """
    curve = np.asarray(curve)

    # Flip sign for flopped curves (original lines 2675-2677)
    for flop_curve in self.flop_curves:
        if _is_aligned(curve, flop_curve):
            curve = -curve

    # Basis change to original GV computation basis (line 2680)
    curve = self.precompose @ curve

    return self.gv(curve, check_deg=check_deg)


def _invariants_gv_series_cybir(self, curve, do_ensure_nilpotency=False,
                                **kwargs):
    """Extract GV series using flop-aware lookup.

    Returns ``[GV(C), GV(2C), GV(3C), ...]`` using
    ``gv_incl_flop``, stopping when a lookup returns ``None``.

    This is a faithful translation of the original ``gv_series``
    method (lines 2594-2612).

    Parameters
    ----------
    curve : array_like
        Curve class in the current basis.
    do_ensure_nilpotency : bool, optional
        If True, ensure nilpotency first.

    Returns
    -------
    list[int]
        GV series for multiples of the curve.
    """
    gv_obj = self.copy()

    if do_ensure_nilpotency:
        gv_obj = gv_obj.ensure_nilpotency(curve, **kwargs)

    gvs = []
    gv = gv_obj.gv_incl_flop(curve, check_deg=True)
    n = 1

    while gv is not None:
        gvs.append(int(gv))
        n += 1
        gv = gv_obj.gv_incl_flop(n * np.asarray(curve), check_deg=True)

    return gvs


def _invariants_ensure_nilpotency(self, curve, verbose=True, quit_length=3):
    """Recompute GVs to higher degree until the series terminates.

    If the GV series for *curve* does not end in zero at the current
    cutoff, recomputes GVs with a higher ``max_deg`` until termination
    is achieved or ``quit_length`` is exceeded.

    This is a faithful translation of the original
    ``ensure_nilpotency`` (lines 2530-2590).

    Parameters
    ----------
    curve : array_like
        Curve class in the current (possibly flopped) basis.
    verbose : bool, optional
        Print progress.
    quit_length : int, optional
        Maximum degree multiplier before giving up.

    Returns
    -------
    Invariants
        An Invariants object (possibly recomputed) whose series
        terminates in zero.

    Raises
    ------
    Exception
        If a GV value that should have been computed is None.
    """
    from .types import InsufficientGVError

    # Determine sign correction for flopped curves
    flop_sign_correction = 1
    for flop_curve in self.flop_curves:
        if _is_antiparallel(curve, flop_curve):
            flop_sign_correction = -1

    curve = np.asarray(curve)

    # Check the furthest computed GV along the ray
    n_orig = int(self.cutoff // (
        flop_sign_correction * (self.precompose @ curve) @ self.grading_vec
    ))
    last = self.gv_incl_flop(n_orig * curve, check_deg=True)

    n = 0
    if last == 0:
        return self

    if last is None:
        raise Exception(
            "This one was supposed to have been computed: "
            f"curve {n_orig * curve}, grading_vec {self.grading_vec}, "
            f"cutoff {self.cutoff}"
        )

    # Recompute to higher degree until we get 0
    while last != 0 and (n + n_orig) <= quit_length:
        n += 1

        if verbose:
            print(
                f"n = {n_orig + n} (vs {quit_length}), "
                f"last entry is {last}, going to {n_orig + n + 1}"
            )

        max_deg = int(
            (n_orig + n) * (flop_sign_correction * curve) @ self.grading_vec
            + 1
        )
        gvs = self._cy.compute_gvs(
            grading_vec=self.grading_vec, max_deg=max_deg
        )
        gvs.flop_curves = []
        gvs.precompose = self.precompose
        gvs = gvs.flop_gvs(self.flop_curves)
        last = gvs.gv_incl_flop((n_orig + n) * curve, check_deg=True)

        if last is None:
            raise Exception(
                "This one was supposed to have been computed: "
                f"curve {(n_orig + n) * curve}, "
                f"grading_vec {gvs.grading_vec}, cutoff {gvs.cutoff}"
            )

    if n <= quit_length:
        assert last is not None

    return gvs


def _invariants_cone_incl_flop(self):
    """Return the Mori cone with flop-curve signs corrected.

    Transforms the charge vectors through the inverse of
    ``precompose`` and flips generators aligned with flop curves.

    This is a faithful translation of the original
    ``cone_incl_flop`` (lines 2686-2692).

    Returns
    -------
    cytools.Cone
        Mori cone in the current (flopped) basis.
    """
    import cytools

    charges = (
        np.array(list(self.charges()))
        @ np.linalg.inv(self.precompose).T
    )
    return cytools.Cone(np.vstack([
        x if np.all([not _is_parallel(x, f) for f in self.flop_curves])
        else -x
        for x in charges
    ]))


# ---------------------------------------------------------------------------
# Entry-point patches
# ---------------------------------------------------------------------------

def _cy_birational_class(self, **kwargs):
    """Construct the birational class (extended Kahler cone) from this CY3.

    Returns
    -------
    CYBirationalClass
    """
    from cybir.core.ekc import CYBirationalClass

    return CYBirationalClass.from_gv(self, **kwargs)


def _poly_birational_class(self, **kwargs):
    """Construct the birational class from this polytope.

    Triangulates, extracts a CY, then constructs the EKC.

    Returns
    -------
    CYBirationalClass
    """
    return self.triangulate().get_cy().birational_class(**kwargs)


# ---------------------------------------------------------------------------
# Main patch function
# ---------------------------------------------------------------------------

def patch_cytools():
    """Apply cybir monkey-patches to CYTools classes.

    Patches the following onto ``cytools.calabiyau.Invariants``:

    - ``copy``: deep-copy with flop-tracking attributes
    - ``flop_gvs``: clone with updated flop-curve tracking
    - ``gv_incl_flop``: GV lookup with sign flips and basis change
    - ``gv_series_cybir``: extract GV series via ``gv_incl_flop``
    - ``ensure_nilpotency``: recompute GVs to higher degree
    - ``cone_incl_flop``: Mori cone with flop corrections

    Also patches entry points:

    - ``CalabiYau.birational_class(**kwargs)``
    - ``Polytope.birational_class(**kwargs)``

    This function is idempotent and safe to call multiple times.
    If CYTools is not importable, a warning is issued and the
    function returns without error.

    Version guards (INTG-04, D-17) check that ``Invariants`` has the
    expected ``gv`` method and that ``__init__`` accepts the required
    parameters before patching.
    """
    global _patched
    if _patched:
        return

    # --- Import CYTools ---
    try:
        from cytools.calabiyau import CalabiYau
        # Invariants lives in cytools.calabiyau
        Invariants = CalabiYau._Invariants if hasattr(CalabiYau, "_Invariants") else None
    except ImportError:
        warnings.warn("CYTools not available; skipping cybir monkey-patches")
        return

    # Try to get Invariants from the calabiyau module directly
    try:
        from cytools.calabiyau import Invariants
    except ImportError:
        try:
            import cytools.calabiyau as _cb_mod
            Invariants = getattr(_cb_mod, "Invariants", None)
        except Exception:
            Invariants = None

    if Invariants is None:
        warnings.warn(
            "Could not find CYTools Invariants class; skipping patches"
        )
        return

    try:
        from cytools.polytope import Polytope
    except ImportError:
        Polytope = None
        logger.info("cytools.polytope not available; Polytope patch skipped")

    # --- Version guards (INTG-04, D-17) ---
    if not hasattr(Invariants, "gv"):
        warnings.warn(
            "CYTools Invariants missing 'gv' method; "
            "skipping cybir monkey-patches"
        )
        return

    sig = inspect.signature(Invariants.__init__)
    required_params = {"invariant_type", "charge2invariant"}
    if not required_params.issubset(sig.parameters.keys()):
        warnings.warn(
            "CYTools Invariants.__init__ signature incompatible; "
            "skipping cybir monkey-patches"
        )
        return

    # --- Apply Invariants patches ---
    Invariants.copy = _invariants_copy
    Invariants.flop_gvs = _invariants_flop_gvs
    Invariants.gv_incl_flop = _invariants_gv_incl_flop
    Invariants.gv_series_cybir = _invariants_gv_series_cybir
    Invariants.ensure_nilpotency = _invariants_ensure_nilpotency
    Invariants.cone_incl_flop = _invariants_cone_incl_flop

    # --- Apply entry-point patches ---
    CalabiYau.birational_class = _cy_birational_class
    if Polytope is not None:
        Polytope.birational_class = _poly_birational_class

    _patched = True
    logger.debug("cybir monkey-patches applied to CYTools")

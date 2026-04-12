"""Core data types and algorithms for cybir."""

from .classify import (
    classify_contraction,
    find_zero_vol_divisor,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
)
from .flop import flop_phase, wall_cross_c2, wall_cross_intnums
from .graph import PhaseGraph
from .gv import compute_gv_eff, compute_gv_series, is_nilpotent, is_potent
from .types import (
    CalabiYauLite,
    ContractionType,
    ExtremalContraction,
    InsufficientGVError,
)
from .util import (
    charge_matrix_hsnf,
    coxeter_matrix,
    find_minimal_N,
    get_coxeter_reflection,
    matrix_period,
    moving_cone,
    normalize_curve,
    projected_int_nums,
    projection_matrix,
    sympy_number_clean,
    tuplify,
)

__all__ = [
    # Types
    "CalabiYauLite",
    "ContractionType",
    "ExtremalContraction",
    "InsufficientGVError",
    "PhaseGraph",
    # Flop
    "wall_cross_intnums",
    "wall_cross_c2",
    "flop_phase",
    # GV
    "compute_gv_series",
    "compute_gv_eff",
    "is_potent",
    "is_nilpotent",
    # Classify
    "classify_contraction",
    "is_asymptotic",
    "is_cft",
    "find_zero_vol_divisor",
    "is_symmetric_flop",
    # Utilities
    "charge_matrix_hsnf",
    "coxeter_matrix",
    "find_minimal_N",
    "get_coxeter_reflection",
    "matrix_period",
    "moving_cone",
    "normalize_curve",
    "projected_int_nums",
    "projection_matrix",
    "sympy_number_clean",
    "tuplify",
]

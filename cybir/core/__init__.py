"""Core data types and algorithms for cybir."""

from .classify import (
    classify_contraction,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
    zero_vol_divisor,
)
from .ekc import CYBirationalClass
from .flop import flop_phase, wall_cross_c2, wall_cross_intnums
from .graph import CYGraph
from .gv import gv_eff, gv_series, is_nilpotent, is_potent
from .patch import patch_cytools
from .types import (
    CalabiYauLite,
    ContractionType,
    CoxeterGroup,
    ExtremalContraction,
    InsufficientGVError,
)
from .coxeter import (
    classify_coxeter_type,
    coxeter_element,
    coxeter_order_matrix,
    coxeter_reflection,
    is_finite_type,
    matrix_period,
)
from .util import (
    charge_matrix_hsnf,
    minimal_N,
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
    "CoxeterGroup",
    "ExtremalContraction",
    "InsufficientGVError",
    "CYGraph",
    # Pipeline
    "CYBirationalClass",
    "patch_cytools",
    # Flop
    "wall_cross_intnums",
    "wall_cross_c2",
    "flop_phase",
    # GV
    "gv_series",
    "gv_eff",
    "is_potent",
    "is_nilpotent",
    # Classify
    "classify_contraction",
    "is_asymptotic",
    "is_cft",
    "zero_vol_divisor",
    "is_symmetric_flop",
    # Coxeter
    "classify_coxeter_type",
    "coxeter_element",
    "coxeter_order_matrix",
    "coxeter_reflection",
    "is_finite_type",
    "matrix_period",
    # Utilities
    "charge_matrix_hsnf",
    "minimal_N",
    "moving_cone",
    "normalize_curve",
    "projected_int_nums",
    "projection_matrix",
    "sympy_number_clean",
    "tuplify",
]

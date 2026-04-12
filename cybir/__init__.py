"""cybir -- GV-based extended Kahler cone construction for Calabi-Yau threefolds."""

__version__ = "0.1.0"

from cybir.core.classify import (
    classify_contraction,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
    zero_vol_divisor,
)
from cybir.core.flop import flop_phase, wall_cross_c2, wall_cross_intnums
from cybir.core.graph import CYGraph
from cybir.core.gv import gv_eff, gv_series, is_nilpotent, is_potent
from cybir.core.types import (
    CalabiYauLite,
    ContractionType,
    ExtremalContraction,
    InsufficientGVError,
)
from cybir.core.util import (
    charge_matrix_hsnf,
    coxeter_matrix,
    coxeter_reflection,
    matrix_period,
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
    "ExtremalContraction",
    "InsufficientGVError",
    "CYGraph",
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
    # Utilities
    "charge_matrix_hsnf",
    "coxeter_matrix",
    "coxeter_reflection",
    "matrix_period",
    "minimal_N",
    "moving_cone",
    "normalize_curve",
    "projected_int_nums",
    "projection_matrix",
    "sympy_number_clean",
    "tuplify",
]

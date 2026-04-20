"""cybir -- GV-based extended Kahler cone construction for Calabi-Yau threefolds."""

__version__ = "0.1.0"

from cybir.core.classify import (
    classify_contraction,
    is_asymptotic,
    is_cft,
    is_symmetric_flop,
    zero_vol_divisor,
)
from cybir.core.ekc import CYBirationalClass
from cybir.core.flop import flop_phase, wall_cross_c2, wall_cross_intnums
from cybir.core.graph import CYGraph
from cybir.core.gv import gv_eff, gv_series, is_nilpotent, is_potent
from cybir.core.patch import patch_cytools
from cybir.core.types import (
    CalabiYauLite,
    ContractionType,
    CoxeterGroup,
    ExtremalContraction,
    InsufficientGVError,
)
from cybir.core.toric_curves import ToricCurveData
from cybir.core.ekc import diagnose_curve
from cybir.core.coxeter import (
    classify_coxeter_type,
    coxeter_element,
    coxeter_order_matrix,
    coxeter_reflection,
    is_finite_type,
    matrix_period,
)
from cybir.core.util import (
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
    "ToricCurveData",
    "diagnose_curve",
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

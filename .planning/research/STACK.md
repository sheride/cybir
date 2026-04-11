# Technology Stack

**Project:** cybir
**Researched:** 2026-04-11

## Recommended Stack

### Runtime Environment

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12 | Runtime | Matches existing cytools conda env (3.12.12). Do not target 3.13+ until CYTools/python-flint wheels are confirmed there. | HIGH |
| conda (cytools env) | existing | Environment | CYTools is distributed via Docker/conda with compiled deps (CGAL, PPL, FLINT). Do not create a separate env; install cybir into the existing cytools env via `pip install -e .` | HIGH |

### Build System

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| hatchling | >=1.21 | Build backend | Modern PEP 621 standard, minimal config, no setup.py needed. dbrane-tools has no pyproject.toml (it is path-imported), but cybir should be a proper installable package. Hatchling over setuptools because this is pure Python with no C extensions. | HIGH |
| pyproject.toml | PEP 621 | Package metadata | Single source of truth for metadata, deps, and build config. No setup.py, no setup.cfg. | HIGH |

### Core Dependencies (Runtime)

| Library | Version | Purpose | Why | Confidence |
|---------|---------|---------|-----|------------|
| numpy | >=1.24,<3 | Dense array ops, linear algebra | Already used throughout. Pin floor to ensure modern API; allow numpy 2.x (cytools env has 2.3.5). | HIGH |
| scipy | >=1.10 | Sparse matrices, optimization, spatial | Used for ConvexHull fallback, linear algebra. Already in env (1.17.0). | HIGH |
| python-flint | >=0.7,<0.9 | Exact integer/rational arithmetic | Critical for exact HNF, SNF, LLL, nullspace. CYTools depends on this. Env has 0.8.0. Import as `flint`. | HIGH |
| hsnf | >=0.3 | Hermite/Smith normal form | Used for lattice computations (sublattice indices, coordinate transforms). Lightweight, MIT license. | HIGH |
| sympy | >=1.12 | Symbolic intersection numbers, Chern class cleanup | Used for `sympy_number_clean` style operations on intersection numbers. Env has 1.14.0. | HIGH |
| cytools | (local) | CY3 geometry pipeline | The package this extends. Not a PyPI dep -- declare as an "extra" or document as a prerequisite. Do NOT list in `[project.dependencies]`; list in `[project.optional-dependencies.cytools]` or simply document. | HIGH |

### Dev Dependencies

| Library | Version | Purpose | Why | Confidence |
|---------|---------|---------|-----|------------|
| pytest | >=8.0 | Testing | Already in env (9.0.2). Standard for scientific Python. | HIGH |
| pytest-cov | >=5.0 | Coverage | Already in env. Track coverage of the wall-crossing and classification logic -- these are the correctness-critical paths. | HIGH |
| ruff | >=0.4 | Linting + formatting | Already in env (0.15.10). Replaces flake8+isort+black in a single fast tool. Use for both linting and formatting. | HIGH |
| mypy | >=1.8 | Type checking | Not currently in env, but recommended. The structured data types (Phase, Wall, Facet, Circuit) benefit from static checking. Add gradually -- do not block initial development on full type coverage. | MEDIUM |

### Documentation

| Library | Version | Purpose | Why | Confidence |
|---------|---------|---------|-----|------------|
| Sphinx | >=7.0 | Doc generation | Matches dbrane-tools pattern. Already in env (9.1.0). | HIGH |
| sphinx-book-theme | >=1.0 | Theme | Same as dbrane-tools. Clean, readable. | HIGH |
| sphinx-autodoc-typehints | >=2.0 | Auto type hints in docs | Already in env. Renders type annotations in API docs. | HIGH |
| sphinx-copybutton | >=0.5 | Copy button on code blocks | Already in env. UX nicety. | HIGH |
| sphinx_design | >=0.5 | Admonitions, cards | Already in env. Useful for math callouts. | HIGH |
| sphinx-togglebutton | >=0.3 | Collapsible sections | Already in env. Good for long derivations. | HIGH |
| myst-nb | >=1.0 | Notebook integration | Already in env. Render Jupyter notebooks as doc pages. | HIGH |
| sphinx.ext.mathjax | (builtin) | LaTeX rendering | Essential -- this package is math-heavy. Every docstring should reference equations from 2212.10573 and 2303.00757. | HIGH |
| sphinx.ext.napoleon | (builtin) | NumPy/Google docstrings | Parse NumPy-style docstrings. Matches CYTools convention. | HIGH |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| poetry | Overkill for a scientific package in a conda env. Conflicts with conda dependency resolution. Hatchling is lighter. |
| setuptools + setup.py | Legacy. pyproject.toml with hatchling is cleaner for pure Python. |
| black / isort / flake8 | Ruff replaces all three, faster, already installed. |
| pydantic | Heavyweight for structured data types. Use `dataclasses` or `NamedTuple` -- this is a numerics package, not a web API. Pydantic's validation overhead is unwanted in tight loops. |
| attrs | Unnecessary when stdlib `dataclasses` suffice. Fewer deps = better for conda env. |
| pandas | Not needed. Data is numpy arrays (intersection numbers, charge matrices, GV tables), not tabular. |
| SageMath | CYTools already wraps what it needs from Sage. Do not introduce a direct Sage dependency -- it is enormous and conflicts with conda envs. |
| jupyter-book | myst-nb + Sphinx is the established pattern in dbrane-tools. Jupyter Book is a different build system. |

## Structured Data Types Strategy

Use Python `dataclasses` for the core domain objects:

```python
from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray

@dataclass
class Phase:
    """A Kahler cone phase in the extended Kahler cone."""
    index: int
    kahler_cone: ...  # cytools Cone
    mori_cone: ...    # cytools Cone
    walls: list["Wall"] = field(default_factory=list)
    # etc.

@dataclass
class Wall:
    """A wall between two phases."""
    curve: NDArray[np.int64]
    phase_indices: tuple[int, int]
    wall_type: str  # "flop", "symmetric_flop", "cft", "su2", "asymptotic"
    # etc.
```

Use `numpy.typing.NDArray` for array type hints. This gives static checking without runtime cost.

## Package Layout

```
cybir/
    pyproject.toml
    cybir/
        __init__.py
        core/
            __init__.py
            types.py          # Phase, Wall, Facet, Circuit dataclasses
            gv.py             # GV invariant manipulation
            cones.py          # Cone operations, Mori/Kahler
            lattice.py        # Lattice utilities (from lib.util.lattice + misc)
            wallcrossing.py   # Wall-crossing formula
            classification.py # Wall type diagnosis
            weyl.py           # Weyl reflections, Coxeter matrices
            pipeline.py       # construct_phases main orchestration
        analysis/
            __init__.py
            # Future: visualization, statistics, etc.
        _monkeypatch.py       # CYTools monkey-patching
    tests/
        ...
    documentation/
        source/
            conf.py
            ...
    notebooks/
        ...
```

## Installation

```bash
# In the cytools conda environment:
conda activate cytools

# Development install (editable)
pip install -e ".[dev,docs]"
```

### pyproject.toml skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "cybir"
version = "0.1.0"
description = "Birational geometry of Calabi-Yau threefold hypersurfaces in toric varieties"
requires-python = ">=3.11"
license = "MIT"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "python-flint>=0.7,<0.9",
    "hsnf>=0.3",
    "sympy>=1.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.8",
]
docs = [
    "sphinx>=7.0",
    "sphinx-book-theme>=1.0",
    "sphinx-autodoc-typehints>=2.0",
    "sphinx-copybutton>=0.5",
    "sphinx_design>=0.5",
    "sphinx-togglebutton>=0.3",
    "myst-nb>=1.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
```

## Sources

- [python-flint on PyPI](https://pypi.org/project/python-flint/) -- v0.8.0 confirmed current
- [hsnf on PyPI](https://pypi.org/project/hsnf/) -- Hermite/Smith normal form
- [hsnf documentation](https://hsnf.readthedocs.io/en/latest/)
- [Python Packaging Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Scientific Python Development Guide - Simple packaging](https://learn.scientific-python.org/development/guides/packaging-simple/)
- CYTools conda env inspection (numpy 2.3.5, scipy 1.17.0, sympy 1.14.0, python-flint 0.8.0, Python 3.12.12)
- dbrane-tools Sphinx conf.py (local reference for documentation patterns)

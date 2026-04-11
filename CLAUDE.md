<!-- GSD:project-start source:PROJECT.md -->
## Project

**cybir**

A Python package for studying the birational geometry of Calabi-Yau threefold hypersurfaces in toric varieties. The initial scope is reconstructing the extended Kahler cone (EKC) of a CY3 from its genus-zero Gopakumar-Vafa invariants, following the methods of arXiv:2212.10573 (Gendler, Heidenreich, McAllister, Moritz, Rudelius) and arXiv:2303.00757 (Demirtas, Kim, McAllister, Moritz, Rios-Tascon). Built to integrate cleanly with CYTools.

**Core Value:** A clean, well-documented, modular implementation of GV-based EKC construction that is easy to use, extend, and understand — structured as a proper Python package with Sphinx documentation and CYTools monkey-patching.

### Constraints

- **Mathematical correctness**: All algorithms must remain bit-for-bit equivalent to the original — wall-crossing formula, potent/nilpotent classification, asymptotic/CFT/su(2)/symmetric-flop/flop diagnosis, Weyl orbit expansion, Coxeter matrix computation, etc.
- **CYTools compatibility**: Must work with the CYTools version in the `cytools` conda environment on this machine
- **Package structure**: Follow the dbrane-tools model — `cybir/core/`, Sphinx docs in `documentation/`, notebooks for examples
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
## Package Layout
## Installation
# In the cytools conda environment:
# Development install (editable)
### pyproject.toml skeleton
## Sources
- [python-flint on PyPI](https://pypi.org/project/python-flint/) -- v0.8.0 confirmed current
- [hsnf on PyPI](https://pypi.org/project/hsnf/) -- Hermite/Smith normal form
- [hsnf documentation](https://hsnf.readthedocs.io/en/latest/)
- [Python Packaging Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Scientific Python Development Guide - Simple packaging](https://learn.scientific-python.org/development/guides/packaging-simple/)
- CYTools conda env inspection (numpy 2.3.5, scipy 1.17.0, sympy 1.14.0, python-flint 0.8.0, Python 3.12.12)
- dbrane-tools Sphinx conf.py (local reference for documentation patterns)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

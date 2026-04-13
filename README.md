# cybir

Birational geometry of Calabi-Yau threefold hypersurfaces in toric varieties.

**cybir** reconstructs the extended Kahler cone (EKC) from genus-zero Gopakumar-Vafa invariants, following the methods of [arXiv:2212.10573](https://arxiv.org/abs/2212.10573) (Gendler, Heidenreich, McAllister, Moritz, Rudelius) and [arXiv:2303.00757](https://arxiv.org/abs/2303.00757) (Demirtas, Kim, McAllister, Moritz, Rios-Tascon). Built to integrate cleanly with [CYTools](https://cytools.liagre.fr/).

## Features

- **BFS-based EKC construction** with adaptive GV degree (starts low, bumps automatically if needed)
- **Classification of extremal contractions**: asymptotic, CFT, su(2) enhancement, symmetric flop, generic flop
- **Coxeter group construction** from symmetric-flop reflections with finite-type classification (A_n through I_2(m)) and streaming BFS enumeration
- **Orbit expansion** for the full birational geometry beyond the fundamental domain
- **CYTools integration** via monkey-patching — call `cy.birational_class()` directly
- **On-demand GV reconstruction** for any phase via curve-sign comparison
- **Fundamental domain mapping** — map any point in Kahler/Mori space back to the fundamental chamber

## Installation

Requires the [CYTools](https://cytools.liagre.fr/) conda environment.

```bash
# In the cytools conda environment:
conda activate cytools
cd /path/to/cybir
pip install -e .
```

## Quick start

```python
from cybir import CYBirationalClass, patch_cytools
import cytools

# Activate CYTools integration
patch_cytools()

# Load a Calabi-Yau
p = cytools.fetch_polytopes(h11=2, limit=1)[0]
cy = p.triangulate().get_cy()

# Construct the extended Kahler cone
ekc = CYBirationalClass.from_gv(cy)

# Inspect results
print(f"Phases: {len(ekc.phases)}")
print(f"Contractions: {len(ekc.contractions)}")
for c in ekc.contractions:
    print(f"  {c.contraction_type.display_name()}: {c.contraction_curve}")

# Coxeter orbit expansion (if symmetric flops exist)
ekc.apply_coxeter_orbit()
print(f"After orbit expansion: {len(ekc.phases)} phases")
if ekc.coxeter_type:
    print(f"Coxeter type: {ekc.coxeter_type}, |W| = {ekc.coxeter_order}")
```

## API overview

### Main entry points

| Method | Description |
|--------|-------------|
| `CYBirationalClass.from_gv(cy)` | Full pipeline: setup root, BFS, return result |
| `ekc.apply_coxeter_orbit()` | Expand fundamental domain via Coxeter group |
| `ekc.invariants_for(label)` | GV invariants oriented for a specific phase |
| `ekc.to_fundamental_domain(point)` | Map a point back to the fundamental chamber |
| `patch_cytools()` | Enable `cy.birational_class()` on CYTools objects |

### Result properties

| Property | Description |
|----------|-------------|
| `ekc.phases` | All CalabiYauLite phase objects |
| `ekc.contractions` | All ExtremalContraction objects |
| `ekc.graph` | Phase adjacency graph (CYGraph) |
| `ekc.infinity_cone_gens` | Infinity cone generators (curve tuples) |
| `ekc.eff_cone_gens` | Effective cone generators (divisor tuples) |
| `ekc.coxeter_type` | Coxeter group classification |
| `ekc.coxeter_order` | Order of the Coxeter group |
| `ekc.coxeter_matrix` | Coxeter element (product of reflections) |
| `ekc.build_log` | BFS construction log |

## Module structure

```
cybir/
  core/
    ekc.py        — CYBirationalClass orchestrator and result API
    build_gv.py   — BFS pipeline builder with adaptive GV degree
    coxeter.py    — Coxeter group construction and orbit expansion
    classify.py   — Contraction classification algorithm
    flop.py       — Wall-crossing formulas and flop construction
    gv.py         — Gopakumar-Vafa invariant utilities
    types.py      — CalabiYauLite, ExtremalContraction, ContractionType
    graph.py      — Phase adjacency graph (MultiGraph)
    patch.py      — CYTools monkey-patching
    util.py       — Projection, normalization, lattice utilities
```

## Documentation

Build the Sphinx docs locally:

```bash
cd documentation
make html
open build/html/index.html
```

Example notebooks in `notebooks/`:
- `h11_2_survey.ipynb` — Survey of all 36 h11=2 polytopes
- `h11_2_walkthrough.ipynb` — Step-by-step h11=2 example
- `h11_3_walkthrough.ipynb` — h11=3 example with richer structure

## Tests

```bash
conda activate cytools
pytest tests/ -q
```

## References

- N. Gendler, B. Heidenreich, L. McAllister, J. Moritz, T. Rudelius, *Counting Calabi-Yau Threefolds*, [arXiv:2212.10573](https://arxiv.org/abs/2212.10573)
- M. Demirtas, N. Gendler, C. Kim, L. McAllister, J. Moritz, A. Rios-Tascon, *Computational Mirror Symmetry*, [arXiv:2303.00757](https://arxiv.org/abs/2303.00757)

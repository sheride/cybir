# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------

project = "cybir"
copyright = "2026, Elijah Sheridan"
author = "Elijah Sheridan"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "sphinx_togglebutton",
    "sphinx_design",
    "myst_nb",
]

autodoc_mock_imports = ["cytools", "regfans"]

templates_path = ["_templates"]

source_suffix = [".rst", ".ipynb", ".md"]

exclude_patterns = ["_build"]

pygments_style = None

autodoc_default_flags = ["members"]
autosummary_generate = True
napoleon_use_rtype = False
napoleon_custom_sections = [('Returns', 'params_style')]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"

html_static_path = ["_static"]

# -- Options for myst / notebooks --------------------------------------------

nb_execution_mode = "off"  # don't execute notebooks during build
myst_enable_extensions = ["dollarmath"]
myst_dmath_double_inline = True

# Clean up module paths in docs
add_module_names = False
toc_object_entries_show_parents = "hide"

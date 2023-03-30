# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from brainglobe_sphinx_config import *

project = "cellfinder-core"
copyright = "2023, cellfinder-core contributors"
author = "cellfinder-core contributors"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_automodapi.automodapi",
    # napoleon has to come before autodoc_typehints
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
]
# automodapi config
numpydoc_show_class_members = False
automodapi_toctreedirnm = "_automodapi"

# Configure type hints and docstrings
autodoc_typehints = "description"
typehints_defaults = "comma"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = True

# Links between sphinx projects
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

# Don't allow broken internal links
nitpicky = True

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

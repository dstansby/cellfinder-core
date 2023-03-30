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

extensions = ["sphinx_automodapi.automodapi"]
# automodapi config
numpydoc_show_class_members = False
automodapi_toctreedirnm = "_automodapi"

# Don't allow broken internal links
nitpicky = True

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

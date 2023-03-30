# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cellfinder-core'
copyright = '2023, cellfinder-core contributors'
author = 'cellfinder-core contributors'


from brainglobe_sphinx_config import *

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

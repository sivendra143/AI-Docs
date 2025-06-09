# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'AI Document Chat'
copyright = f'{datetime.now().year}, Your Name'
author = 'Your Name'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings
# See: https://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    'sphinx.ext.autodoc',        # Auto-generate documentation from docstrings
    'sphinx.ext.napoleon',       # Support for NumPy and Google style docstrings
    'sphinx.ext.viewcode',       # Add links to source code
    'sphinx.ext.intersphinx',    # Link to other projects' documentation
    'sphinx.ext.autosummary',    # Generate autodoc summaries
    'sphinx.ext.coverage',       # Documentation coverage checker
    'sphinx.ext.mathjax',        # MathJax support
    'sphinx_rtd_theme',          # Read the Docs theme
    'myst_parser',              # Markdown support
]

# Add any paths that contain templates here, relative to this directory
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix of source filenames
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# The master toctree document
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'

# Theme options
html_theme_options = {
    'navigation_depth': 3,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'logo_only': False,
    'display_version': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS
html_css_files = [
    'custom.css',
]

# -- Extension configuration -------------------------------------------------

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'flask': ('https://flask.palletsprojects.com/en/2.0.x/', None),
    'websockets': ('https://websockets.readthedocs.io/en/stable/', None),
}

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = True

# -- Options for MyST Parser ------------------------------------------------
# Enable MyST extensions
myst_enable_extensions = [
    "dollarmath",  # Support for $ and $$ math
    "amsmath",     # Additional math support
    "deflist",     # Definition lists
    "fieldlist",   # Field lists
    "html_admonition",  # HTML admonitions
    "html_image",  # HTML images
    "replacements",  # Text replacements
    "smartquotes",  # Smart quotes and dashes
    "strikethrough",  # Strikethrough text
    "substitution",  # Substitutions
    "tasklist",  # Task lists
]

# -- Custom configuration ---------------------------------------------------

# Add any custom configuration here

# Set the default role for reStructuredText
# This allows you to use `text` instead of ``text`` for inline code
def setup(app):
    app.add_css_file('custom.css')  # Add custom CSS
    app.add_js_file('custom.js')    # Add custom JavaScript

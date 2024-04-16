# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Grid Data Models"
copyright = (
    "2024, Kapil Duwadi, Tarek Elgindy, Aadil Latif, Daniel Thom, Pedro Andres Sanchez Perez"
)
author = "Kapil Duwadi, Tarek Elgindy, Aadil Latif, Daniel Thom Pedro Andres Sanchez Perez"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.autodoc_pydantic",
    "sphinxcontrib.mermaid",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_field_summary = False
autodoc_inherit_docstrings = False
autodoc_pydantic_field_show_constraints = False
autodoc_pydantic_settings_show_validator_summary = False
autodoc_pydantic_settings_show_validator_members = False
autodoc_pydantic_validator_list_fields = False
autodoc_pydantic_field_list_validators = False
autodoc_pydantic_model_show_validator_summary = False
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
# html_static_path = ["_static"]
# html_css_files = [
#     "css/custom.css",
# ]

source_suffix = [".md"]

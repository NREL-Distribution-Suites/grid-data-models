# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Grid Data Models"
copyright = "2024, Kapil Duwadi, Tarek Elgindy, Aadil Latif, Daniel Thom"
author = "Kapil Duwadi, Tarek Elgindy, Aadil Latif, Daniel Thom"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_immaterial",
]
extensions.append("sphinx_immaterial.apidoc.python.apigen")
# templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_immaterial"
# html_static_path = ["_static"]

source_suffix = [".md"]
html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "site_url": "https://github.nrel.gov/CADET/grid-data-models.git",
    "repo_url": "https://github.nrel.gov/CADET/grid-data-models.git",
    "repo_name": "Grid Data Models",
    "globaltoc_collapse": True,
    "toc_title_is_page_title": True,
    "font": False,
    "features": [
        "navigation.expand",
        "navigation.tabs",
        "navigation.top",
        "navigation.footer",
        "navigation.tabs.sticky",
        "navigation.sections",
        "search.share",
        "search.highlight",
        # "toc.integrate",
        "toc.follow",
        "toc.sticky",
        "content.tabs",
        "content.tooltips",
        "announce.dismiss",
        "toc.follow",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "deep-orange",
            "accent": "lime",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "deep-orange",
            "accent": "lime",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to light mode",
            },
        },
    ],
}

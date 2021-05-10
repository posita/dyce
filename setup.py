#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop


# ---- Imports -------------------------------------------------------------------------


import codecs
import inspect
import os
import setuptools


# ---- Data ----------------------------------------------------------------------------


__all__ = ()

_MY_DIR = os.path.abspath(os.path.dirname(inspect.stack()[0][1]))

# ---- Initialization ------------------------------------------------------------------


vers_info = {
    "__path__": os.path.join(_MY_DIR, "dyce", "version.py"),
}

if os.path.isfile(vers_info["__path__"]):
    with open(vers_info["__path__"]) as _version_file:
        exec(  # pylint: disable=exec-used
            compile(_version_file.read(), vers_info["__path__"], "exec"),
            vers_info,
            vers_info,
        )

with codecs.open(os.path.join(_MY_DIR, "README.md"), encoding="utf-8") as readme_file:
    README = readme_file.read()

__version__ = vers_info.get("__version__", (0, 0, 0))
__vers_str__ = vers_info.get("__vers_str__")

SETUP_ARGS = {
    "name": "dycelib",
    "version": __vers_str__,
    "author": "Matt Bogosian",
    "author_email": "matt@bogosian.net",
    "url": "https://posita.github.io/dyce/{}/".format(
        __vers_str__ if __vers_str__ and __version__ != (0, 0, 0) else "master"
    ),
    "license": "MIT License",
    "description": "Simple Python tools for dice-based probabilities",
    "long_description": README,
    "long_description_content_type": "text/markdown",
    # From <https://pypi.python.org/pypi?%3Aaction=list_classifiers>
    "classifiers": [
        "Topic :: Education",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    "packages": setuptools.find_packages(exclude=("tests",)),
    "include_package_data": True,
    "install_requires": ["typing", "typing_extensions"],
    "extras_require": {
        "dev": [
            "black",
            "debug",
            "flake8",
            "jedi",
            "mypy",
            "pylint",
            "pytest",
            "tox",
            "twine",
        ],
        "doc": [
            "mike",
            "mkdocs-exclude",
            "mkdocs-material",
            "mkdocstrings",
        ],
    },
}

if __name__ == "__main__":
    setuptools.setup(**SETUP_ARGS)

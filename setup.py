#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import codecs
import inspect
import os

import setuptools

__all__ = ()


# ---- Initialization ------------------------------------------------------------------


my_dir = os.path.abspath(os.path.dirname(inspect.stack()[0][1]))
vers_info_path = os.path.join(my_dir, "dyce", "version.py")
vers_info = {}  # type: ignore

if os.path.isfile(vers_info_path):
    with open(vers_info_path) as version_file:
        exec(
            compile(version_file.read(), vers_info_path, "exec"),
            vers_info,
            vers_info,
        )

with codecs.open(os.path.join(my_dir, "README.md"), encoding="utf-8") as readme_file:
    README = readme_file.read()

__version__ = vers_info.get("__version__", (0, 0, 0))
__vers_str__ = vers_info.get("__vers_str__")
vers_major_minor_str = f"{__version__[0]}.{__version__[1]}"

SETUP_ARGS = {
    "name": "dycelib",
    "version": __vers_str__,
    "author": "Matt Bogosian",
    "author_email": "matt@bogosian.net",
    "url": f"https://posita.github.io/dyce/{vers_major_minor_str if __version__ > (0, 0, 0) else 'latest'}/",
    "license": "MIT License",
    "description": "Simple Python tools for exploring dice outcomes and other finite discrete probabilities",
    "long_description": README,
    "long_description_content_type": "text/markdown",
    # From <https://pypi.python.org/pypi?%3Aaction=list_classifiers>
    "classifiers": [
        "Topic :: Education",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    "packages": setuptools.find_packages(exclude=("tests",)),
    "include_package_data": True,
    "install_requires": ["typing-extensions>=3.10;python_version<'3.9'"],
    "extras_require": {
        "dev": [
            "beartype>=0.8",
            "mike",
            # See:
            # * <https://github.com/mkdocs/mkdocs/issues/2448>
            # * <https://github.com/mkdocstrings/mkdocstrings/issues/295>
            "mkdocs!=1.2",
            "mkdocs-exclude",
            "mkdocs-material",
            "mkdocstrings",
            "mypy",
            "numpy",
            "pre-commit",
            "pytest-gitignore",
            "sympy",
            "tox",
            "twine",
        ],
    },
}


if __name__ == "__main__":
    setuptools.setup(**SETUP_ARGS)

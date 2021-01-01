#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If that file is missing or appears to be
modified from its original, then please contact the author before viewing or using this
software in any capacity.
"""
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
    "__path__": os.path.join(_MY_DIR, "_skel", "version.py"),
}

if os.path.isfile(vers_info["__path__"]):
    with open(vers_info["__path__"]) as _version_file:
        exec(  # pylint: disable=exec-used
            compile(_version_file.read(), vers_info["__path__"], "exec"),
            vers_info,
            vers_info,
        )

with codecs.open(os.path.join(_MY_DIR, "README.rst"), encoding="utf-8") as readme_file:
    README = readme_file.read()

__vers_str__ = vers_info.get("__vers_str__")
__release__ = vers_info.get("__release__", __vers_str__)

SETUP_ARGS = {
    "name": "py_skel",
    "version": __vers_str__,
    "author": "Matt Bogosian",
    "author_email": "matt@bogosian.net",
    "url": "https://_skel.readthedocs.org/en/{}/".format(__release__),
    "license": "MIT License",
    "description": "Python Project Skeleton",
    "long_description": README,
    # From <https://pypi.python.org/pypi?%3Aaction=list_classifiers>
    "classifiers": (
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ),
    "packages": setuptools.find_packages(exclude=("tests",)),
    "include_package_data": True,
    "install_requires": ["typing"],
    "entry_points": {"console_scripts": ("_skel = _skel.main:main",)},
}

if __name__ == "__main__":
    setuptools.setup(**SETUP_ARGS)

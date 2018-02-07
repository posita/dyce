# -*- encoding: utf-8; grammar-ext: py; mode: python -*-

# ========================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not expressly
waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before
viewing or using this software in any capacity.
"""
# ========================================================================

from __future__ import absolute_import, division, print_function, unicode_literals

TYPE_CHECKING = False  # from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing  # noqa: E501,F401 # pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import six
import unittest

from _skel.main import _configlogging

# ---- Constants ---------------------------------------------------------

__all__ = ()

# ---- Initialization ----------------------------------------------------

# Python 3 complains that the assert*Regexp* methods are deprecated in
# favor of the analogous assert*Regex methods, which Python 2's unittest
# doesn't have; this monkey patch fixes all that nonsense
if not hasattr(unittest.TestCase, 'assertCountEqual'):
    setattr(unittest.TestCase, 'assertCountEqual', six.assertCountEqual)

if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    setattr(unittest.TestCase, 'assertRaisesRegex', six.assertRaisesRegex)

if not hasattr(unittest.TestCase, 'assertRegex'):
    setattr(unittest.TestCase, 'assertRegex', six.assertRegex)

# TODO: Add this back if six ever supports assertNotRegex
if hasattr(unittest.TestCase, 'assertNotRegex'):
    delattr(unittest.TestCase, 'assertNotRegex')

if hasattr(unittest.TestCase, 'assertNotRegexpMatches'):
    delattr(unittest.TestCase, 'assertNotRegexpMatches')

_configlogging()

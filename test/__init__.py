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
    import typing  # noqa: E501,F401; pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403; pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403; pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import unittest

from _skel.main import _configlogging

# ---- Constants ---------------------------------------------------------

__all__ = ()

# ---- Initialization ----------------------------------------------------

# Python 3 complains that the assert*Regexp* methods are deprecated in
# favor of the analogous assert*Regex methods, which Python 2's unittest
# doesn't have; this monkey patch fixes all that nonsense
if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp  # type: ignore

if not hasattr(unittest.TestCase, 'assertRegex'):
    unittest.TestCase.assertRegex = unittest.TestCase.assertRegexpMatches  # type: ignore

if not hasattr(unittest.TestCase, 'assertNotRegex'):
    unittest.TestCase.assertNotRegex = unittest.TestCase.assertNotRegexpMatches  # type: ignore

_configlogging()

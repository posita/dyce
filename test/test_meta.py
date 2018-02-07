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

import re
import unittest

# ---- Constants ---------------------------------------------------------

__all__ = ()

# ---- Initialization ----------------------------------------------------

# ========================================================================
class MetaTestData(unittest.TestCase):
    """
    Makes sure our environment is sane.
    """

    # ---- Methods -------------------------------------------------------

    def test_shims(self):
        assert hasattr(unittest.TestCase, 'assertCountEqual')
        assert hasattr(unittest.TestCase, 'assertRaisesRegex')
        assert hasattr(unittest.TestCase, 'assertRegex')
        assert not hasattr(unittest.TestCase, 'assertNotRegex')
        assert not hasattr(unittest.TestCase, 'assertNotRegexpMatches')

        with self.assertRaisesRegex(AssertionError, re.compile(r'\AElement counts were not equal:.*First has [^,]+, Second has ', re.DOTALL)):
            self.assertCountEqual([1, 2, 1], [2, 1, 2])

        with self.assertRaisesRegex(AssertionError, r"^Regexp? didn't match: .* not found in "):
            self.assertRegex('spam', r'^ham$')

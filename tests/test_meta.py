#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ======================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not
expressly waived or licensed are reserved. If those files are missing or
appear to be modified from their originals, then please contact the
author before viewing or using this software in any capacity.
"""
# ======================================================================

from __future__ import absolute_import, division, print_function

TYPE_CHECKING = False  # from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports ---------------------------------------------------------

import logging
import re
import unittest

# ---- Data ------------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

# ---- Classes ---------------------------------------------------------

# ======================================================================
class MetaTestCase(unittest.TestCase):
    """
    Makes sure our environment is sane.
    """

    # ---- Methods -----------------------------------------------------

    def test_long_message(self):
        assert hasattr(self, 'longMessage')

        with self.assertRaises(AttributeError):
            del self.longMessage

        msg = 'Scooby Scooby Doo, where are you?'
        self.longMessage = False

        with self.assertRaisesRegex(AssertionError, re.compile(r'\A{}\Z'.format(re.escape(msg)), re.DOTALL)):
            self.assertTrue(False, msg=msg)  # pylint: disable=redundant-unittest-assert

        del self.longMessage
        assert self.longMessage

        with self.assertRaisesRegex(AssertionError, re.compile(r'\AFalse is not true : {}\Z'.format(re.escape(msg)), re.DOTALL)):
            self.assertTrue(False, msg=msg)  # pylint: disable=redundant-unittest-assert

    def test_shims(self):
        assert hasattr(unittest.TestCase, 'assertCountEqual')
        assert hasattr(unittest.TestCase, 'assertRaisesRegex')
        assert hasattr(unittest.TestCase, 'assertRegex')

        with self.assertRaisesRegex(AssertionError, re.compile(r'\AElement counts were not equal:.*First has [^,]+, Second has ', re.DOTALL)):
            self.assertCountEqual([1, 2, 1], [2, 1, 2])

        with self.assertRaisesRegex(AssertionError, r"\ARegexp? didn't match: .* not found in "):
            self.assertRegex('spam', r'\Aham\Z')

# ---- Initialization --------------------------------------------------

if __name__ == '__main__':
    import tests  # noqa: F401 # pylint: disable=unused-import
    unittest.main()

#!/usr/bin/env python
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

from __future__ import (
    absolute_import, division, print_function, unicode_literals,
)
from builtins import *  # noqa: F401,F403; pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403; pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import logging
import unittest

import test  # noqa: F401; pylint: disable=unused-import
# from test.symmetries import mock

# ---- Constants ---------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

# ---- Classes -----------------------------------------------------------

# ========================================================================
class MainTestCase(unittest.TestCase):

    longMessage = True

    # ---- Public hooks --------------------------------------------------

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_main(self):
        pass

# ---- Initialization ----------------------------------------------------

if __name__ == '__main__':
    unittest.main()

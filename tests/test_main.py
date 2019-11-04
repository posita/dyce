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

# from __future__ import generator_stop

from typing import *  # noqa: F401,F403 # pylint: disable=unused-wildcard-import,wildcard-import

# ---- Imports ---------------------------------------------------------

import logging
import unittest

# ---- Data ------------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

# ---- Classes ---------------------------------------------------------

# ======================================================================
class MainTestCase(unittest.TestCase):

    # ---- Methods -----------------------------------------------------

    def test_main(self):
        # type: (...) -> None
        pass

# ---- Initialization --------------------------------------------------

if __name__ == '__main__':
    import tests  # noqa: F401 # pylint: disable=unused-import
    unittest.main()

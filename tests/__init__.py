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


import unittest

from _skel.main import configlogging


# ---- Data ----------------------------------------------------------------------------


__all__ = ()


# ---- Initialization ------------------------------------------------------------------


unittest.TestCase.longMessage = True
configlogging()

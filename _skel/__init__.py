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

import logging as _logging

from .main import *  # noqa: F401,F403 # pylint: disable=wildcard-import
from .version import __version__  # noqa: F401

# ---- Data ------------------------------------------------------------

__all__ = ()

LOGGER = _logging.getLogger(__name__)

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

import logging as _logging

from .main import *  # noqa: F401,F403 # pylint: disable=useless-suppression,wildcard-import
from .version import __version__  # noqa: F401

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


LOGGER = _logging.getLogger(__name__)

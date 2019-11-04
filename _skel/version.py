# -*- encoding: utf-8 -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before viewing or using
this software in any capacity.
"""
# ======================================================================================

# from __future__ import generator_stop
from typing import *  # noqa: F401,F403 # pylint: disable=unused-wildcard-import,wildcard-import


# ---- Data ----------------------------------------------------------------------------


__all__ = ()

__version__: Tuple[int, int, int] = (0, 0, 0)  # noqa: F405
__vers_str__ = ".".join(str(_) for _ in __version__)
__release__ = "v" + __vers_str__

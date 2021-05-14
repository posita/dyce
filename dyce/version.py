# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop
from typing import Tuple

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


__version__: Tuple[int, int, int] = (0, 1, 1)
__vers_str__ = ".".join(str(_) for _ in __version__)
__release__ = "v" + __vers_str__

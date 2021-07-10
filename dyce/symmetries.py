# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import sys

__all__ = ("gcd",)


# ---- Functions -----------------------------------------------------------------------


if sys.version_info >= (3, 9):
    from math import gcd
else:
    from functools import reduce
    from math import gcd as _gcd

    def gcd(*integers: int) -> int:
        return reduce(_gcd, integers, 0)

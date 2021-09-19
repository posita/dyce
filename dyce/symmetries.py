# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import sys

__all__ = (
    "comb",
    "gcd",
)


# ---- Functions -----------------------------------------------------------------------


if sys.version_info >= (3, 9):
    from math import gcd
else:
    from functools import reduce
    from math import gcd as _gcd

    def gcd(*integers: int) -> int:
        return reduce(_gcd, integers, 0)


if sys.version_info >= (3, 8):
    from math import comb
else:
    from fractions import Fraction
    from math import factorial

    def comb(__n: int, __k: int) -> int:
        return int(
            Fraction(Fraction(factorial(__n), factorial(__k)), factorial(__n - __k))
        )

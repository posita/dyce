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
from typing import Iterable, TypeVar, Union, overload

__all__ = (
    "comb",
    "gcd",
    "sum_w_start",
)


# ---- Types ---------------------------------------------------------------------------


_S = TypeVar("_S")
_T = TypeVar("_T")


# ---- Functions -----------------------------------------------------------------------


if sys.version_info >= (3, 8):
    from math import (  # noqa: F401 # pylint: disable=no-name-in-module,unused-import
        comb,
    )

    sum_w_start = sum
else:
    from fractions import Fraction
    from itertools import chain
    from math import factorial

    def comb(__n: int, __k: int) -> int:
        return int(
            Fraction(Fraction(factorial(__n), factorial(__k)), factorial(__n - __k))
        )

    @overload
    def sum_w_start(__iterable: Iterable[_T]) -> Union[_T, int]:
        ...

    @overload
    def sum_w_start(__iterable: Iterable[_T], start: _S) -> Union[_T, _S]:
        ...

    def sum_w_start(__iterable, start=0):
        return sum(chain((start,), __iterable))


if sys.version_info >= (3, 9):
    from math import gcd
else:
    from functools import reduce
    from math import gcd as _gcd

    def gcd(*integers: int) -> int:
        return reduce(_gcd, integers, 0)

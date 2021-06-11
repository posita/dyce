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
from typing import TypeVar

__all__ = (
    "comb",
    "gcd",
)


# ---- Types ---------------------------------------------------------------------------


_S = TypeVar("_S")
_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)


# ---- Functions -----------------------------------------------------------------------


if sys.version_info >= (3, 8):
    from math import comb
    from typing import (
        Protocol,
        SupportsAbs,
        SupportsFloat,
        SupportsIndex,
        SupportsInt,
        runtime_checkable,
    )
else:
    from abc import abstractmethod
    from fractions import Fraction
    from math import factorial

    from typing_extensions import Protocol, runtime_checkable

    @runtime_checkable
    class SupportsAbs(Protocol[_T_co]):
        __slots__ = ()

        @abstractmethod
        def __abs__(self) -> _T_co:
            pass

    @runtime_checkable
    class SupportsFloat(Protocol):
        __slots__ = ()

        @abstractmethod
        def __float__(self) -> float:
            pass

    @runtime_checkable
    class SupportsIndex(Protocol):
        __slots__ = ()

        @abstractmethod
        def __index__(self) -> int:
            pass

    @runtime_checkable
    class SupportsInt(Protocol):
        __slots__ = ()

        @abstractmethod
        def __int__(self) -> int:
            pass

    def comb(__n: int, __k: int) -> int:
        return int(
            Fraction(Fraction(factorial(__n), factorial(__k)), factorial(__n - __k))
        )


if sys.version_info >= (3, 9):
    from math import gcd
    from typing import Annotated
else:
    from functools import reduce
    from math import gcd as _gcd

    from typing_extensions import Annotated  # noqa: F401

    def gcd(*integers: int) -> int:
        return reduce(_gcd, integers, 0)

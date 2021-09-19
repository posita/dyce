# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import math
import operator

from .numberwang import Numberwang, Wangernumb

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_numberwang() -> None:
    for binop in (
        operator.__add__,
        operator.__and__,
        operator.__eq__,
        operator.__floordiv__,
        operator.__ge__,
        operator.__gt__,
        operator.__le__,
        operator.__lshift__,
        operator.__lt__,
        operator.__mod__,
        operator.__mul__,
        operator.__ne__,
        operator.__or__,
        operator.__pow__,
        operator.__rshift__,
        operator.__sub__,
        operator.__truediv__,
        operator.__xor__,
    ):
        assert binop(Numberwang(-273), Numberwang(42)) == binop(
            -273, 42
        ), f"op: {binop}"

    for unop in (
        complex,
        int,
        float,
        round,
        math.ceil,
        math.floor,
        math.trunc,
        operator.__abs__,
        operator.__index__,
        operator.__invert__,
        operator.__neg__,
        operator.__pos__,
    ):
        assert unop(Numberwang(-273)) == unop(-273), f"op: {unop}"  # type: ignore


def test_wangernum() -> None:
    for binop in (
        operator.__add__,
        operator.__eq__,
        operator.__floordiv__,
        operator.__ge__,
        operator.__gt__,
        operator.__le__,
        operator.__lt__,
        operator.__mod__,
        operator.__mul__,
        operator.__ne__,
        operator.__pow__,
        operator.__sub__,
        operator.__truediv__,
    ):
        assert binop(Wangernumb(-273.15), Wangernumb(1.618)) == binop(
            -273.15, 1.618
        ), f"op: {binop}"

    for unop in (
        complex,
        int,
        float,
        round,
        math.ceil,
        math.floor,
        math.trunc,
        operator.__abs__,
        operator.__neg__,
        operator.__pos__,
    ):
        assert unop(Wangernumb(-273.15)) == unop(-273.15), f"op: {unop}"  # type: ignore

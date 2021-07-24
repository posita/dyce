# -*- encoding: utf-8 -*-
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
from decimal import Decimal
from fractions import Fraction

from dyce.numtypes import BitwiseCs, OutcomeCs

from .numberwang import Numberwang, Wangernumb

__all__ = ()


try:
    import numpy
except ImportError:
    numpy = None  # type: ignore

try:
    import sympy
except ImportError:
    sympy = None


# ---- Tests ---------------------------------------------------------------------------


def test_outcome_proto() -> None:
    assert isinstance(-273.15, OutcomeCs)
    assert isinstance(-273, OutcomeCs)
    assert isinstance(Fraction(-27315, 100), OutcomeCs)
    assert isinstance(Decimal("-273.15"), OutcomeCs)
    assert isinstance(Wangernumb(-273.15), OutcomeCs)
    assert isinstance(Numberwang(-273), OutcomeCs)

    if numpy is not None:
        assert isinstance(numpy.float128(-273.15), OutcomeCs)
        assert isinstance(numpy.int64(-273), OutcomeCs)

    if sympy is not None:
        assert isinstance(sympy.Float(-273.15), OutcomeCs)
        assert isinstance(sympy.Rational(-27315, 100), OutcomeCs)
        assert isinstance(sympy.Integer(-273), OutcomeCs)
        assert isinstance(sympy.symbols("x"), OutcomeCs)

    assert not isinstance("-273.15", OutcomeCs)


def test_supports_bitwise_proto() -> None:
    assert isinstance(-273, BitwiseCs)
    assert isinstance(Numberwang(-273), BitwiseCs)

    if numpy is not None:
        assert isinstance(numpy.int64(-273), BitwiseCs)

    # TODO: See <https://github.com/sympy/sympy/issues/19311>
    # if sympy is not None:
    #     assert isinstance(sympy.Integer(-273), BitwiseCs)
    #     assert isinstance(sympy.symbols("x"), BitwiseCs)

    assert not isinstance("-273", BitwiseCs)


def test_numberwang() -> None:
    for binop in (
        operator.add,
        operator.and_,
        operator.eq,
        operator.floordiv,
        operator.ge,
        operator.gt,
        operator.le,
        operator.lshift,
        operator.lt,
        operator.mod,
        operator.mul,
        operator.ne,
        operator.or_,
        operator.pow,
        operator.rshift,
        operator.sub,
        operator.truediv,
        operator.xor,
    ):
        assert binop(Numberwang(-273), Numberwang(42)) == binop(
            -273, 42
        ), "op: {}".format(binop)

    for unop in (
        complex,
        int,
        float,
        round,
        math.ceil,
        math.floor,
        math.trunc,
        operator.abs,
        operator.index,
        operator.invert,
        operator.neg,
        operator.pos,
    ):
        assert unop(Numberwang(-273)) == unop(-273), "op: {}".format(unop)  # type: ignore


def test_wangernum() -> None:
    for binop in (
        operator.add,
        operator.eq,
        operator.floordiv,
        operator.ge,
        operator.gt,
        operator.le,
        operator.lt,
        operator.mod,
        operator.mul,
        operator.ne,
        operator.pow,
        operator.sub,
        operator.truediv,
    ):
        assert binop(Wangernumb(-273.15), Wangernumb(1.618)) == binop(
            -273.15, 1.618
        ), "op: {}".format(binop)

    for unop in (
        complex,
        int,
        float,
        round,
        math.ceil,
        math.floor,
        math.trunc,
        operator.abs,
        operator.neg,
        operator.pos,
    ):
        assert unop(Wangernumb(-273.15)) == unop(-273.15), "op: {}".format(unop)  # type: ignore

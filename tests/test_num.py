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

import pytest

from dyce.types import _BitwiseCs, _OutcomeCs

from .numberwang import Numberwang, Wangernumb

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_outcome_proto() -> None:
    assert isinstance(-273.15, _OutcomeCs)
    assert isinstance(-273, _OutcomeCs)
    assert isinstance(Fraction(-27315, 100), _OutcomeCs)
    assert isinstance(Decimal("-273.15"), _OutcomeCs)
    assert isinstance(Wangernumb(-273.15), _OutcomeCs)
    assert isinstance(Numberwang(-273), _OutcomeCs)

    assert not isinstance("-273.15", _OutcomeCs)


def test_outcome_proto_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert isinstance(numpy.float128(-273.15), _OutcomeCs)
    assert isinstance(numpy.int64(-273), _OutcomeCs)


def test_outcome_proto_sympy() -> None:
    sympy = pytest.importorskip("sympy", reason="requires numpy")
    assert isinstance(sympy.Float(-273.15), _OutcomeCs)
    assert isinstance(sympy.Rational(-27315, 100), _OutcomeCs)
    assert isinstance(sympy.Integer(-273), _OutcomeCs)
    assert isinstance(sympy.symbols("x"), _OutcomeCs)


def test_supports_bitwise_proto() -> None:
    assert isinstance(-273, _BitwiseCs)
    assert isinstance(Numberwang(-273), _BitwiseCs)

    assert not isinstance("-273", _BitwiseCs)


def test_supports_bitwise_proto_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert isinstance(numpy.int64(-273), _BitwiseCs)


def test_supports_bitwise_proto_sympy() -> None:
    pytest.importorskip("sympy", reason="requires numpy")
    # TODO(posita): See <https://github.com/sympy/sympy/issues/19311>
    # assert isinstance(sympy.Integer(-273), _BitwiseCs)
    # assert isinstance(sympy.symbols("x"), _BitwiseCs)


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
        ), "op: {}".format(binop)

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
        assert unop(Numberwang(-273)) == unop(-273), "op: {}".format(unop)  # type: ignore


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
        ), "op: {}".format(binop)

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
        assert unop(Wangernumb(-273.15)) == unop(-273.15), "op: {}".format(unop)  # type: ignore

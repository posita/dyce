# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Tuple

import pytest

from dyce.types import OutcomeT, _BitwiseCs, _OutcomeCs, is_even, is_odd
from tests.numberwang import Numberwang, Wangernumb

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_beartype_detection() -> None:
    roar = pytest.importorskip("beartype.roar", reason="requires beartype")
    from dyce.bt import beartype

    @beartype
    def _outcome_identity(arg: OutcomeT) -> OutcomeT:
        return arg

    with pytest.raises(roar.BeartypeException):
        _outcome_identity("-273")  # type: ignore

    @beartype
    def _lies_all_lies(arg: OutcomeT) -> Tuple[str]:
        return (arg,)  # type: ignore

    with pytest.raises(roar.BeartypeException):
        _lies_all_lies(-273)


def test_beartype_validators() -> None:
    roar = pytest.importorskip("beartype.roar", reason="requires beartype")
    from beartype.vale import Is

    from dyce.bt import beartype
    from dyce.types import Annotated

    NonZero = Annotated[int, Is[lambda x: x != 0]]

    @beartype
    def _divide_it(n: int, d: NonZero) -> float:
        return n / d

    with pytest.raises(roar.BeartypeException):
        _divide_it(0, 0)

    If = Annotated[
        Tuple[str, ...],
        Is[
            lambda x: x
            == (
                "If you can dream—and not make dreams your master;",
                "If you can think—and not make thoughts your aim;",
            )
        ],
    ]

    @beartype
    def _if(lines: If) -> Tuple[str, ...]:
        return (
            "If you can meet with Triumph and Disaster",
            "And treat those two impostors just the same;",
        )

    with pytest.raises(roar.BeartypeException):
        _if(())


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


def test_is_even() -> None:
    assert is_even(0)
    assert is_even(Numberwang(0))
    assert not is_even(1)
    assert not is_even(Numberwang(1))


def test_is_even_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert is_even(numpy.int64(0))
    assert not is_even(numpy.int64(1))


def test_is_odd() -> None:
    assert is_odd(1)
    assert is_odd(Numberwang(1))
    assert not is_odd(0)
    assert not is_odd(Numberwang(0))


def test_is_odd_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert is_odd(numpy.int64(1))
    assert not is_odd(numpy.int64(0))

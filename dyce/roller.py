# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

r"""
Experimental traceable rollers.

Interfaces may change substantially or disappear.
"""

import operator
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import reduce
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
    final,
    overload,
)

import optype as ot

from .h import H, HableT, _HableOpsOptOut
from .lifecycle import experimental
from .p import P
from .types import GetItemT, getitems, natural_key

__all__ = (
    "HRoller",
    "HableRoller",
    "LiteralRoller",
    "PRoller",
    "Roll",
    "RollError",
    "Roller",
    "RollerPool",
    "SingleOutcomeRoll",
    "SingleOutcomeRoller",
    "trace",
)

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")
_NodeT = TypeVar("_NodeT")
_CanAddSameT = TypeVar("_CanAddSameT", bound=ot.CanAddSame)


@dataclass(frozen=True, slots=True)
class _RollFormat:
    text: str
    precedence: int
    has_result_suffix: bool = False


@dataclass(frozen=True, slots=True)
class _BinaryOperation:
    name: str
    function: Callable[[object, object], object]
    symbol: str
    precedence: int
    associativity: Literal["left", "right", "none"] = "left"

    @classmethod
    def create(
        cls,
        name: str,
        function: Callable[..., object],
        symbol: str,
        precedence: int,
        associativity: Literal["left", "right", "none"] = "left",
    ) -> "_BinaryOperation":
        return cls(
            name,
            cast("Callable[[object, object], object]", function),
            symbol,
            precedence,
            associativity,
        )

    def __call__(self, lhs: object, rhs: object) -> object:
        return self.function(lhs, rhs)

    def format(self, left: _RollFormat, right: _RollFormat) -> _RollFormat:
        left_text = self._format_child(left, right=False)
        right_text = self._format_child(right, right=True)
        return _RollFormat(f"{left_text} {self.symbol} {right_text}", self.precedence)

    def _format_child(self, child: _RollFormat, *, right: bool) -> str:
        parenthesize = right and child.has_result_suffix
        parenthesize |= child.precedence < self.precedence
        if child.precedence == self.precedence:
            if self.associativity == "none":
                parenthesize = True
            elif right:
                parenthesize |= self.associativity != "right"
            else:
                parenthesize |= self.associativity == "right"
        return f"({child.text})" if parenthesize else child.text


@dataclass(frozen=True, slots=True)
class _UnaryOperation:
    name: str
    function: Callable[[object], object]
    symbol: str | None
    precedence: int

    @classmethod
    def create(
        cls,
        name: str,
        function: Callable[..., object],
        symbol: str | None,
        precedence: int,
    ) -> "_UnaryOperation":
        return cls(
            name,
            cast("Callable[[object], object]", function),
            symbol,
            precedence,
        )

    def __call__(self, operand: object) -> object:
        return self.function(operand)

    def format(self, operand: _RollFormat) -> _RollFormat:
        if self.symbol is None:
            return _RollFormat(f"{self.name}({operand.text})", self.precedence)
        operand_text = (
            f"({operand.text})"
            if operand.has_result_suffix or operand.precedence < self.precedence
            else operand.text
        )
        return _RollFormat(f"{self.symbol}{operand_text}", self.precedence)


_ADD = _BinaryOperation.create("add", operator.add, "+", 60)
_SUB = _BinaryOperation.create("sub", operator.sub, "-", 60)
_MUL = _BinaryOperation.create("mul", operator.mul, "*", 70)
_TRUEDIV = _BinaryOperation.create("truediv", operator.truediv, "/", 70)
_FLOORDIV = _BinaryOperation.create("floordiv", operator.floordiv, "//", 70)
_MOD = _BinaryOperation.create("mod", operator.mod, "%", 70)
_POW = _BinaryOperation.create("pow", operator.pow, "**", 90, "right")
_LSHIFT = _BinaryOperation.create("lshift", operator.lshift, "<<", 50)
_RSHIFT = _BinaryOperation.create("rshift", operator.rshift, ">>", 50)
_AND = _BinaryOperation.create("and", operator.and_, "&", 40)
_OR = _BinaryOperation.create("or", operator.or_, "|", 20)
_XOR = _BinaryOperation.create("xor", operator.xor, "^", 30)
_LT = _BinaryOperation.create("lt", operator.lt, "<", 10, "none")
_LE = _BinaryOperation.create("le", operator.le, "<=", 10, "none")
_EQ = _BinaryOperation.create("eq", operator.eq, "==", 10, "none")
_NE = _BinaryOperation.create("ne", operator.ne, "!=", 10, "none")
_GE = _BinaryOperation.create("ge", operator.ge, ">=", 10, "none")
_GT = _BinaryOperation.create("gt", operator.gt, ">", 10, "none")
_NEG = _UnaryOperation.create("neg", operator.neg, "-", 80)
_POS = _UnaryOperation.create("pos", operator.pos, "+", 80)
_ABS = _UnaryOperation.create("abs", operator.abs, None, 100)
_INVERT = _UnaryOperation.create("invert", operator.invert, "~", 80)

_CALL_PRECEDENCE = 100
_ATOM_PRECEDENCE = 110


class RollError(Exception):
    r"""
    A failure during rolling, with the original exception in `__cause__`.

    *path* contains the participating rollers from the outermost call to the failing call.
    """

    def __init__(
        self,
        message: str,
        path: tuple["Roller[Any]", ...],
    ) -> None:
        super().__init__(message)
        self.path = path

    def __str__(self) -> str:
        labels = []
        for roller in self.path:
            label = repr(roller.metadata())
            labels.append(label)
        return super().__str__() + "\nRoller path:\n  " + "\n  → ".join(labels)


class Roller(_HableOpsOptOut, ABC, Generic[_T_co]):
    r"""A computation capable of producing a nonempty tuple of traceable outcomes."""

    __slots__ = ()

    # An operation with a Roll returns a Roll. These runtime methods return
    # NotImplemented so the Roll operand handles it.
    @overload
    def __add__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __add__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _ADD)

    @overload
    def __sub__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __sub__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _SUB)

    @overload
    def __mul__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mul__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MUL)

    @overload
    def __truediv__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __truediv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _TRUEDIV)

    @overload
    def __floordiv__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _FLOORDIV)

    @overload
    def __mod__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mod__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MOD)

    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "Roller[_T_co]",
        rhs: "Roll[ot.CanRPow[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __pow__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _POW)

    @overload
    def __lshift__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __lshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _LSHIFT)

    @overload
    def __rshift__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _RSHIFT)

    @overload
    def __and__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __and__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _AND)

    @overload
    def __or__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __or__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _OR)

    @overload
    def __xor__(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __xor__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "Roller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "Roller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __radd__(
        self: "Roller[ot.CanRAdd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __radd__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _ADD)

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "Roller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "Roller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rsub__(
        self: "Roller[ot.CanRSub[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rsub__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _SUB)

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "Roller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "Roller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmul__(
        self: "Roller[ot.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmul__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MUL)

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "Roller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "Roller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "Roller[ot.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _TRUEDIV)

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "Roller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "Roller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "Roller[ot.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _FLOORDIV)

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "Roller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "Roller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmod__(
        self: "Roller[ot.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmod__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MOD)

    @overload
    def __rpow__(  # type: ignore[overload-overlap]
        self: "Roller[_T_co]",
        lhs: "Roll[ot.CanPow2[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(  # type: ignore[misc]
        self: "Roller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "Roller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rpow__(
        self: "Roller[ot.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rpow__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _POW)

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "Roller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "Roller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "Roller[ot.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _LSHIFT)

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "Roller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "Roller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "Roller[ot.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _RSHIFT)

    @overload
    def __rand__(  # type: ignore[misc]
        self: "Roller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "Roller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rand__(
        self: "Roller[ot.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rand__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _AND)

    @overload
    def __ror__(  # type: ignore[misc]
        self: "Roller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "Roller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __ror__(
        self: "Roller[ot.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __ror__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _OR)

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "Roller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "Roller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rxor__(
        self: "Roller[ot.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rxor__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _XOR)

    @overload
    def lt(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanLt[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def lt(
        self: "Roller[ot.CanLt[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def lt(
        self: "Roller[ot.CanLt[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def lt(
        self: "Roller[ot.CanLt[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def lt(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is less than *rhs*."""
        return self._compare(rhs, _LT)

    @overload
    def le(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanLe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def le(
        self: "Roller[ot.CanLe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def le(
        self: "Roller[ot.CanLe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def le(
        self: "Roller[ot.CanLe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def le(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is less than or equal to *rhs*."""
        return self._compare(rhs, _LE)

    @overload
    def eq(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanEq[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def eq(
        self: "Roller[ot.CanEq[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def eq(
        self: "Roller[ot.CanEq[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def eq(
        self: "Roller[ot.CanEq[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def eq(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is equal to *rhs*."""
        return self._compare(rhs, _EQ)

    @overload
    def ne(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanNe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ne(
        self: "Roller[ot.CanNe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def ne(
        self: "Roller[ot.CanNe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def ne(
        self: "Roller[ot.CanNe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def ne(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is not equal to *rhs*."""
        return self._compare(rhs, _NE)

    @overload
    def ge(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanGe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ge(
        self: "Roller[ot.CanGe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def ge(
        self: "Roller[ot.CanGe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def ge(
        self: "Roller[ot.CanGe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def ge(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is greater than or equal to *rhs*."""
        return self._compare(rhs, _GE)

    @overload
    def gt(  # type: ignore[overload-overlap]
        self: "Roller[ot.CanGt[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def gt(
        self: "Roller[ot.CanGt[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def gt(
        self: "Roller[ot.CanGt[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoller[bool]": ...
    @overload
    def gt(
        self: "Roller[ot.CanGt[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[bool]": ...
    def gt(self, rhs: object) -> object:
        r"""Returns a roller or roll testing whether this roller’s summed outcome is greater than *rhs*."""
        return self._compare(rhs, _GT)

    def _compare(self, rhs: object, comparison: _BinaryOperation) -> object:
        if isinstance(rhs, Roll):
            return self.roll()._compare(  # ruff: ignore[private-member-access]
                rhs, comparison
            )
        return _binary_roller(self, rhs, comparison)

    @staticmethod
    @overload
    def from_value(  # type: ignore[overload-overlap]
        value: "SingleOutcomeRoller[_T]", *, label: str | None = None
    ) -> "SingleOutcomeRoller[_T]": ...
    @staticmethod
    @overload
    def from_value(  # type: ignore[overload-overlap]
        value: "Roller[_T]", *, label: str | None = None
    ) -> "Roller[_T]": ...
    @staticmethod
    @overload
    def from_value(  # type: ignore[overload-overlap]
        value: H[_T], *, label: str | None = None
    ) -> "HRoller[_T]": ...
    @staticmethod
    @overload
    def from_value(  # type: ignore[overload-overlap]
        value: P[_T], *, label: str | None = None
    ) -> "PRoller[_T]": ...
    @staticmethod
    @overload
    def from_value(  # type: ignore[overload-overlap]
        value: HableT[_T], *, label: str | None = None
    ) -> "HableRoller[_T]": ...
    @staticmethod
    @overload
    def from_value(value: _T, *, label: str | None = None) -> "LiteralRoller[_T]": ...
    @experimental
    @staticmethod
    def from_value(value: object, *, label: str | None = None) -> "Roller[Any]":
        r"""Returns a roller for *value*, optionally labeled with *label*."""
        if isinstance(value, Roller):
            return value if label is None else value.label(label)
        elif isinstance(value, H):
            return HRoller(value, label=label)  # type: ignore[no-any-return]
        elif isinstance(value, P):
            return PRoller(value, label=label)  # type: ignore[no-any-return]
        elif isinstance(value, HableT):
            return HableRoller(value, label=label)  # type: ignore[no-any-return]
        else:
            return LiteralRoller(value, label=label)  # type: ignore[no-any-return]

    def label(self, label: str) -> "Roller[_T_co]":
        r"""Returns a roller that labels this roller without changing it."""
        return _LabeledRoller(self, label)

    def __neg__(
        self: "Roller[ot.CanNeg[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]",
            _UnaryRoller(_as_single_outcome_roller(self), _NEG),
        )

    def __pos__(
        self: "Roller[ot.CanPos[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]",
            _UnaryRoller(_as_single_outcome_roller(self), _POS),
        )

    def __abs__(
        self: "Roller[ot.CanAbs[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]",
            _UnaryRoller(_as_single_outcome_roller(self), _ABS),
        )

    def __invert__(
        self: "Roller[ot.CanInvert[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]",
            _UnaryRoller(_as_single_outcome_roller(self), _INVERT),
        )

    @abstractmethod
    def metadata(self) -> dict[str, object]:
        r"""
        Returns JSON-compatible metadata describing this roller.

        The metadata must contain a nonempty string `kind`.
        Dyce kinds use the `dyce.` prefix.
        Custom kinds should use a prefix controlled by their author to avoid collisions.
        Metadata describes only this roller.
        """

    def _format_roll(self, roll: "Roll[object]") -> _RollFormat:
        metadata = self.metadata()
        label = metadata.get("label", metadata.get("kind"))
        relationships = roll._trace_relationships()  # ruff: ignore[private-member-access]
        related_rolls: tuple[Roll[object], ...] = ()
        for value in relationships.values():
            related_rolls += value if isinstance(value, tuple) else (value,)
        if related_rolls:
            arguments = ", ".join(
                related._format_expression().text  # ruff: ignore[private-member-access]
                for related in related_rolls
            )
            text = f"{label}({arguments}) => {roll._format_result()}"  # ruff: ignore[private-member-access]
            has_result_suffix = True
        else:
            text = f"{roll._format_result()} [{label}]"  # ruff: ignore[private-member-access]
            has_result_suffix = False
        return _RollFormat(text, _ATOM_PRECEDENCE, has_result_suffix)

    def at(
        self: "Roller[_CanAddSameT]", which: GetItemT, *more: GetItemT
    ) -> "SingleOutcomeRoller[_CanAddSameT]":
        r"""Returns a roller summing the outcomes at the selected positions."""
        return self.select(which, *more).sum()

    def roll(self) -> "Roll[_T_co]":
        r"""
        Produces a sample outcome collection trace, reporting failures as [`RollError`][dyce.roller.RollError].

        Subclasses implement the [`_roll` method][dyce.roller.Roller._roll] instead of overriding this method.
        """
        try:
            return self._roll()
        except RollError as exc:
            exc.path = (self, *exc.path)
            raise
        except Exception as exc:
            raise RollError(str(exc), (self,)) from exc

    def select(self, which: GetItemT, *more: GetItemT) -> "Roller[_T_co]":
        r"""
        Returns a roller selecting the specified positions.

        Selectors are resolved against each tuple produced when rolling.
        Invalid indices raise at that time rather than during construction.
        """
        return _PoolSelectionRoller(self, (which, *more))

    def sum(
        self: "Roller[_CanAddSameT]",
    ) -> "SingleOutcomeRoller[_CanAddSameT]":
        r"""Returns a roller summing every outcome."""
        if isinstance(self, SingleOutcomeRoller):
            return self
        return _PoolSumRoller(self)

    @abstractmethod
    def _roll(self) -> "Roll[_T_co]":
        r"""
        Subclass implementation hook for producing a nonempty sample outcome collection trace.

        Raises `ValueError` if no outcomes can be produced.
        Child rollers should be called via their public [`roll` methods][dyce.roller.Roller.roll].
        """

    def _trace_relationships(
        self,
    ) -> "dict[str, Roller[object] | tuple[Roller[object], ...]]":
        return {}


class SingleOutcomeRoller(Roller[_T_co], ABC):
    r"""A roller that always produces one outcome."""

    __slots__ = ()

    @final
    def roll(self) -> "SingleOutcomeRoll[_T_co]":
        return cast("SingleOutcomeRoll[_T_co]", super().roll())

    def label(self, label: str) -> "SingleOutcomeRoller[_T_co]":
        return _LabeledSingleOutcomeRoller(self, label)

    @abstractmethod
    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        r"""
        Subclass implementation hook for producing a one-outcome roll.

        Child rollers should be called through their public [`roll` methods][dyce.roller.Roller.roll].
        """


class HRoller(SingleOutcomeRoller[_T_co]):
    r"""A roller backed by [`H.roll`][dyce.H.roll]."""

    __slots__ = ("_h", "_label")

    @experimental
    def __init__(self, h: H[_T_co], *, label: str | None = None) -> None:
        if not isinstance(h, H):
            raise TypeError("h must be an instance of H")
        if label is not None and not isinstance(label, str):
            raise TypeError("label must be a str or None")
        self._h = h
        self._label = label if label is not None else str(h)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._h!r}, label={self._label!r})"

    @property
    def h(self) -> H[_T_co]:
        r"""Returns this roller’s [`H`][dyce.H] source object."""
        return self._h

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "dyce.source",
            "label": self._label,
        }

    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        return SingleOutcomeRoll(self._h.roll(), self)


class HableRoller(SingleOutcomeRoller[_T_co]):
    r"""A roller backed by a [`HableT`][dyce.HableT]."""

    __slots__ = ("_hable", "_label")

    @experimental
    def __init__(self, hable: HableT[_T_co], *, label: str | None = None) -> None:
        if not isinstance(hable, HableT):
            raise TypeError("hable must be an instance of HableT")
        if label is not None and not isinstance(label, str):
            raise TypeError("label must be a str or None")
        self._hable = hable
        self._label = label if label is not None else str(hable)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._hable!r}, label={self._label!r})"

    @property
    def hable(self) -> HableT[_T_co]:
        r"""Returns this roller’s [`HableT`][dyce.HableT] source object."""
        return self._hable

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "dyce.source",
            "label": self._label,
        }

    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        return SingleOutcomeRoll(self._hable.h().roll(), self)


class LiteralRoller(SingleOutcomeRoller[_T_co]):
    r"""A deterministic roller for a single, literal value."""

    __slots__ = ("_label", "_value")

    @experimental
    def __init__(self, value: _T_co, *, label: str | None = None) -> None:
        if label is not None and not isinstance(label, str):
            raise TypeError("label must be a str or None")
        self._value = value
        self._label = label

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value!r}, label={self._label!r})"

    @property
    def value(self) -> _T_co:
        r"""Returns this roller’s source value."""
        return self._value

    def metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {"kind": "dyce.literal", "value": self._value}
        if self._label is not None:
            metadata["label"] = self._label
        return metadata

    def _format_roll(self, roll: "Roll[object]") -> _RollFormat:
        text = roll._format_result()  # ruff: ignore[private-member-access]
        if self._label is not None:
            text += f" [{self._label}]"
        return _RollFormat(
            text,
            _ATOM_PRECEDENCE,
        )

    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        return SingleOutcomeRoll(self._value, self)


class PRoller(Roller[_T_co]):
    r"""A roller backed by a [`P`][dyce.P]."""

    __slots__ = ("_label", "_p")

    @experimental
    def __init__(self, p: P[_T_co], *, label: str | None = None) -> None:
        if not isinstance(p, P):
            raise TypeError("p must be an instance of P")
        if label is not None and not isinstance(label, str):
            raise TypeError("label must be a str or None")
        self._p = p
        self._label = label if label is not None else str(p)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._p!r}, label={self._label!r})"

    def __len__(self) -> int:
        return len(self._p)

    @property
    def p(self) -> P[_T_co]:
        r"""Returns this roller’s [`P`][dyce.P] source object."""
        return self._p

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "dyce.pool-source",
            "label": self._label,
        }

    def _roll(self) -> "Roll[_T_co]":
        outcomes = self._p.roll()
        return Roll(outcomes, self)


class RollerPool(Roller[_T_co]):
    r"""A roller backed by one or more [`SingleOutcomeRoller`][dyce.roller.SingleOutcomeRoller] objects."""

    __slots__ = ("_rollers",)

    @experimental
    def __init__(self, *rollers: SingleOutcomeRoller[_T_co]) -> None:
        if any(not isinstance(roller, SingleOutcomeRoller) for roller in rollers):
            raise TypeError("rollers must be SingleOutcomeRoller instances")
        self._rollers = rollers

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join(repr(roller) for roller in self._rollers)})"

    def __len__(self) -> int:
        return len(self._rollers)

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[_T_co], ...]:
        r"""This roller’s [`SingleOutcomeRoller`][dyce.roller.SingleOutcomeRoller] operands."""
        return self._rollers

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.pool"}

    def _format_roll(self, roll: "Roll[object]") -> _RollFormat:
        operands = cast("_OperandRoll[object]", roll).operands
        items = ", ".join(
            operand._format_expression().text  # ruff: ignore[private-member-access]
            for operand in operands
        )
        if len(operands) == 1:
            items += ","
        return _RollFormat(f"({items})", _ATOM_PRECEDENCE)

    def _roll(self) -> "Roll[_T_co]":
        if not self._rollers:
            raise ValueError("no outcomes from an empty pool")
        rolls = [roller.roll() for roller in self._rollers]
        try:
            rolls.sort(
                key=cast(
                    "Callable[[SingleOutcomeRoll[_T_co]], Any]",
                    lambda roll: roll.outcome,
                )
            )
        except TypeError:
            rolls.sort(key=lambda roll: natural_key(roll.outcome))
        outcomes = tuple(roll.outcome for roll in rolls)
        operands = cast(
            "tuple[Roll[object], ...]",
            tuple(rolls),
        )
        return _OperandRoll(outcomes, self, operands)

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"operands": self.operands}


@dataclass(frozen=True, slots=True, eq=False)
class Roll(_HableOpsOptOut, Generic[_T_co]):
    r"""An immutable trace of one or more outcomes."""

    outcomes: tuple[_T_co, ...]
    roller: Roller[_T_co] = field(repr=False)

    def __post_init__(self) -> None:
        if not self.outcomes:
            raise ValueError("a roll must contain at least one outcome")

    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __add__(
        self,
        rhs: object,
    ) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _ADD)

    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __sub__(
        self,
        rhs: object,
    ) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _SUB)

    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __mul__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _MUL)

    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __truediv__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(
            rhs, _TRUEDIV
        )

    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(
            rhs, _FLOORDIV
        )

    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __mod__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _MOD)

    @overload
    def __pow__(
        self: "Roll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __pow__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _POW)

    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __lshift__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(
            rhs, _LSHIFT
        )

    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rshift__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(
            rhs, _RSHIFT
        )

    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __and__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _AND)

    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __or__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _OR)

    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __xor__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._binary_operator(rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "Roll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "Roll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "Roll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __radd__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _ADD
        )

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "Roll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "Roll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "Roll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rsub__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _SUB
        )

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "Roll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "Roll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "Roll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rmul__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _MUL
        )

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "Roll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "Roll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "Roll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _TRUEDIV
        )

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "Roll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "Roll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "Roll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _FLOORDIV
        )

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "Roll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "Roll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "Roll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rmod__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _MOD
        )

    @overload
    def __rpow__(  # type: ignore[misc]
        self: "Roll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "Roll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "Roll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rpow__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _POW
        )

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "Roll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "Roll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "Roll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _LSHIFT
        )

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "Roll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "Roll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "Roll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _RSHIFT
        )

    @overload
    def __rand__(  # type: ignore[misc]
        self: "Roll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "Roll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "Roll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rand__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _AND
        )

    @overload
    def __ror__(  # type: ignore[misc]
        self: "Roll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "Roll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "Roll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __ror__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _OR
        )

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "Roll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "Roll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "Roll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "Roll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rxor__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return _as_single_outcome_roll(cast("object", self))._reflected_binary_operator(
            lhs, _XOR
        )

    @overload
    def lt(
        self: "Roll[ot.CanLt[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def lt(
        self: "Roll[ot.CanLt[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def lt(
        self: "Roll[ot.CanLt[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def lt(
        self: "Roll[ot.CanLt[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def lt(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is less than *rhs*."""
        return self._compare(rhs, _LT)

    @overload
    def le(
        self: "Roll[ot.CanLe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def le(
        self: "Roll[ot.CanLe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def le(
        self: "Roll[ot.CanLe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def le(
        self: "Roll[ot.CanLe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def le(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is less than or equal to *rhs*."""
        return self._compare(rhs, _LE)

    @overload
    def eq(
        self: "Roll[ot.CanEq[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def eq(
        self: "Roll[ot.CanEq[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def eq(
        self: "Roll[ot.CanEq[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def eq(
        self: "Roll[ot.CanEq[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def eq(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is equal to *rhs*."""
        return self._compare(rhs, _EQ)

    @overload
    def ne(
        self: "Roll[ot.CanNe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ne(
        self: "Roll[ot.CanNe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ne(
        self: "Roll[ot.CanNe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ne(
        self: "Roll[ot.CanNe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def ne(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is not equal to *rhs*."""
        return self._compare(rhs, _NE)

    @overload
    def ge(
        self: "Roll[ot.CanGe[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ge(
        self: "Roll[ot.CanGe[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ge(
        self: "Roll[ot.CanGe[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def ge(
        self: "Roll[ot.CanGe[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def ge(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is greater than or equal to *rhs*."""
        return self._compare(rhs, _GE)

    @overload
    def gt(
        self: "Roll[ot.CanGt[_OtherT, bool]]", rhs: "Roller[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def gt(
        self: "Roll[ot.CanGt[_OtherT, bool]]", rhs: "Roll[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def gt(
        self: "Roll[ot.CanGt[_OtherT, bool]]", rhs: "HableT[_OtherT]"
    ) -> "SingleOutcomeRoll[bool]": ...
    @overload
    def gt(
        self: "Roll[ot.CanGt[_OtherT, bool]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[bool]": ...
    def gt(self, rhs: object) -> "SingleOutcomeRoll[bool]":
        r"""Tests whether this roll’s summed outcome is greater than *rhs*."""
        return self._compare(rhs, _GT)

    def format(self) -> str:
        r"""Formats this roll as a compact expression followed by its outcome or outcomes."""
        return self._format_expression().text

    def sum(self: "Roll[_CanAddSameT]") -> "SingleOutcomeRoll[_CanAddSameT]":
        r"""
        Returns the sum of this roll’s outcomes.

        Raises `ValueError` if there are no outcomes.
        """
        if isinstance(self, SingleOutcomeRoll):
            return self
        roller = self.roller.sum()
        outcome = _sum_outcomes(self.outcomes)
        return _SingleOutcomeOperandRoll(outcome, roller, (cast("Roll[object]", self),))

    def trace(self) -> dict[str, object]:  # ruff: ignore[complex-structure]
        r"""
        Returns the execution trace rooted at this roll, composed of JSON-compatible containers.

        The `format` and `version` entries identify the trace format.
        The `root` entry identifies a record in `rolls`.
        Each roller record contains its roller’s metadata and, when applicable, its named relationships to other rollers.
        Each roll’s `roller` entry identifies its producing roller in `rollers`.
        Roll records contain named relationships to other rolls when applicable.
        A singular relationship contains one ID.
        A plural relationship contains a list of IDs.
        Outcomes and literal values must themselves be JSON-compatible for the complete trace to be serializable as JSON.
        """
        roller_ids: dict[int, str] = {}
        rollers: dict[str, dict[str, object]] = {}
        roll_ids: dict[int, str] = {}
        rolls: dict[str, dict[str, object]] = {}

        def relationship_ids(
            relationships: dict[str, _NodeT | tuple[_NodeT, ...]],
            visit: Callable[[_NodeT], str],
        ) -> dict[str, object]:
            ids: dict[str, object] = {}
            for relationship, value in relationships.items():
                if isinstance(value, tuple):
                    ids[relationship] = [visit(related) for related in value]
                else:
                    ids[relationship] = visit(value)
            return ids

        def visit_roller(roller: Roller[object]) -> str:
            key = id(roller)
            if key in roller_ids:
                return roller_ids[key]

            roller_id = f"roller{len(roller_ids)}"
            roller_ids[key] = roller_id
            rollers[roller_id] = {}
            relationships = roller._trace_relationships()  # ruff: ignore[private-member-access]
            related_ids = relationship_ids(relationships, visit_roller)
            rollers[roller_id] = {"metadata": roller.metadata()}
            if related_ids:
                rollers[roller_id]["relationships"] = related_ids
            return roller_id

        def visit_roll(roll: Roll[object]) -> str:
            key = id(roll)
            if key in roll_ids:
                return roll_ids[key]

            roll_id = f"roll{len(roll_ids)}"
            roll_ids[key] = roll_id
            rolls[roll_id] = {}
            roller_id = visit_roller(roll.roller)
            relationships = roll._trace_relationships()
            related_ids = relationship_ids(relationships, visit_roll)
            roll_data: dict[str, object]
            if isinstance(roll, SingleOutcomeRoll):
                roll_data = {"outcome": roll.outcome}
            else:
                roll_data = {"outcomes": list(roll.outcomes)}
            rolls[roll_id] = {"roller": roller_id, **roll_data}
            if related_ids:
                rolls[roll_id]["relationships"] = related_ids
            return roll_id

        root = visit_roll(cast("Roll[object]", self))
        return {
            "format": "dyce.roll-trace",
            "version": 1,
            "root": root,
            "rollers": rollers,
            "rolls": rolls,
        }

    def _compare(
        self, rhs: object, comparison: _BinaryOperation
    ) -> "SingleOutcomeRoll[bool]":
        lhs_roll: SingleOutcomeRoll[Any] = _as_single_outcome_roll(cast("Any", self))
        if isinstance(rhs, Roller):
            rhs = rhs.roll()
        elif isinstance(rhs, HableT):
            rhs = _as_single_outcome_roller(rhs).roll()
        rhs_roll = _as_single_outcome_roll(rhs)
        roller: SingleOutcomeRoller[bool] = _BinaryRoller(
            lhs_roll.roller, rhs_roll.roller, comparison
        )
        outcome = comparison(lhs_roll.outcome, rhs_roll.outcome)
        return _SingleOutcomeOperandRoll(
            cast("bool", outcome), roller, (lhs_roll, rhs_roll)
        )

    def _format_expression(self) -> _RollFormat:
        return self.roller._format_roll(cast("Roll[object]", self))  # ruff: ignore[private-member-access]

    def _format_result(self) -> str:
        return repr(self.outcomes)

    def _trace_relationships(
        self,
    ) -> "dict[str, Roll[object] | tuple[Roll[object], ...]]":
        return {}


@dataclass(frozen=True, slots=True, eq=False, init=False)
class SingleOutcomeRoll(Roll[_T_co]):
    r"""An immutable trace containing one outcome."""

    roller: SingleOutcomeRoller[_T_co] = field(repr=False)

    def __init__(
        self,
        outcome: _T_co,
        roller: SingleOutcomeRoller[_T_co],
    ) -> None:
        super(SingleOutcomeRoll, self).__init__((outcome,), roller)

    @property
    def outcome(self) -> _T_co:
        return self.outcomes[0]

    def _format_result(self) -> str:
        return repr(self.outcome)

    def __neg__(
        self: "SingleOutcomeRoll[ot.CanNeg[_ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]":
        return cast("SingleOutcomeRoll[_ResultT]", self._unary_operator(_NEG))

    def __pos__(
        self: "SingleOutcomeRoll[ot.CanPos[_ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]":
        return cast("SingleOutcomeRoll[_ResultT]", self._unary_operator(_POS))

    def __abs__(
        self: "SingleOutcomeRoll[ot.CanAbs[_ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]":
        return cast("SingleOutcomeRoll[_ResultT]", self._unary_operator(_ABS))

    def __invert__(
        self: "SingleOutcomeRoll[ot.CanInvert[_ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]":
        return cast("SingleOutcomeRoll[_ResultT]", self._unary_operator(_INVERT))

    def _binary_operator(
        self, rhs: object, operation: _BinaryOperation
    ) -> "SingleOutcomeRoll[object]":
        if isinstance(rhs, Roller):
            rhs = rhs.roll()
        elif isinstance(rhs, HableT):
            rhs = _as_single_outcome_roller(rhs).roll()
        rhs_roll = _as_single_outcome_roll(rhs)
        roller: SingleOutcomeRoller[object] = _BinaryRoller(
            self.roller, rhs_roll.roller, operation
        )
        outcome = operation(self.outcome, rhs_roll.outcome)
        return _SingleOutcomeOperandRoll(outcome, roller, (self, rhs_roll))

    def _reflected_binary_operator(
        self, lhs: object, operation: _BinaryOperation
    ) -> "SingleOutcomeRoll[object]":
        if isinstance(lhs, Roller):
            lhs = lhs.roll()
        elif isinstance(lhs, HableT):
            lhs = _as_single_outcome_roller(lhs).roll()
        lhs_roll = _as_single_outcome_roll(lhs)
        roller: SingleOutcomeRoller[object] = _BinaryRoller(
            lhs_roll.roller, self.roller, operation
        )
        outcome = operation(lhs_roll.outcome, self.outcome)
        return _SingleOutcomeOperandRoll(outcome, roller, (lhs_roll, self))

    def _unary_operator(
        self, operation: _UnaryOperation
    ) -> "SingleOutcomeRoll[object]":
        roller: SingleOutcomeRoller[object] = _UnaryRoller(self.roller, operation)
        outcome = operation(self.outcome)
        return _SingleOutcomeOperandRoll(outcome, roller, (self,))


class _LabeledRoller(Roller[_T_co]):
    def __init__(self, roller: Roller[_T_co], label: str) -> None:
        self._roller = roller
        self._label = label

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._roller!r}, label={self._label!r})"

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.label", "label": self._label}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        result = cast("_LabeledRoll[object]", roll).result
        expression = result._format_expression()  # ruff: ignore[private-member-access]
        return _RollFormat(
            f"{self._label}({expression.text}) => {roll._format_result()}",  # ruff: ignore[private-member-access]
            _CALL_PRECEDENCE,
            has_result_suffix=True,
        )

    def _roll(self) -> Roll[_T_co]:
        result = self._roller.roll()
        return _LabeledRoll(result.outcomes, self, result)

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"roller": cast("Roller[object]", self._roller)}


class _LabeledSingleOutcomeRoller(SingleOutcomeRoller[_T_co]):
    def __init__(self, roller: SingleOutcomeRoller[_T_co], label: str) -> None:
        self._roller = roller
        self._label = label

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._roller!r}, label={self._label!r})"

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.label", "label": self._label}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        result = cast("_LabeledSingleOutcomeRoll[object]", roll).result
        expression = result._format_expression()  # ruff: ignore[private-member-access]
        return _RollFormat(
            f"{self._label}({expression.text}) => {roll._format_result()}",  # ruff: ignore[private-member-access]
            _CALL_PRECEDENCE,
            has_result_suffix=True,
        )

    def _roll(self) -> SingleOutcomeRoll[_T_co]:
        result = self._roller.roll()
        return _LabeledSingleOutcomeRoll(result.outcome, self, result)

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"roller": cast("Roller[object]", self._roller)}


class _BinaryRoller(SingleOutcomeRoller[_ResultT]):
    __slots__ = ("_left", "_operation", "_right")

    def __init__(
        self,
        left: SingleOutcomeRoller[object],
        right: SingleOutcomeRoller[object],
        operation: _BinaryOperation,
    ) -> None:
        self._left = left
        self._right = right
        self._operation = operation

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._left!r}, {self._right!r}, {self._operation!r})"

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[object], ...]:
        return (self._left, self._right)

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.binary", "operator": self._operation.name}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        left, right = cast("_SingleOutcomeOperandRoll[object]", roll).operands
        expression = self._operation.format(
            left._format_expression(),  # ruff: ignore[private-member-access]
            right._format_expression(),  # ruff: ignore[private-member-access]
        )
        return _RollFormat(
            f"{expression.text} => {roll._format_result()}",  # ruff: ignore[private-member-access]
            expression.precedence,
            has_result_suffix=True,
        )

    def _roll(self) -> SingleOutcomeRoll[_ResultT]:
        left_roll = self._left.roll()
        right_roll = self._right.roll()
        outcome = self._operation(left_roll.outcome, right_roll.outcome)
        return _SingleOutcomeOperandRoll(
            cast("_ResultT", outcome), self, (left_roll, right_roll)
        )

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"operands": self.operands}


class _UnaryRoller(SingleOutcomeRoller[_ResultT]):
    __slots__ = ("_operand", "_operation")

    def __init__(
        self, operand: SingleOutcomeRoller[object], operation: _UnaryOperation
    ) -> None:
        self._operand = operand
        self._operation = operation

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._operand!r}, {self._operation!r})"

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[object], ...]:
        return (self._operand,)

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.unary", "operator": self._operation.name}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        (operand,) = cast("_SingleOutcomeOperandRoll[object]", roll).operands
        expression = self._operation.format(
            operand._format_expression()  # ruff: ignore[private-member-access]
        )
        return _RollFormat(
            f"{expression.text} => {roll._format_result()}",  # ruff: ignore[private-member-access]
            expression.precedence,
            has_result_suffix=True,
        )

    def _roll(self) -> SingleOutcomeRoll[_ResultT]:
        operand_roll = self._operand.roll()
        outcome = self._operation(operand_roll.outcome)
        return _SingleOutcomeOperandRoll(
            cast("_ResultT", outcome), self, (operand_roll,)
        )

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"operands": self.operands}


class _PoolSelectionRoller(Roller[_T_co]):
    __slots__ = ("_parent", "_selectors")

    def __init__(
        self,
        parent: Roller[_T_co],
        selectors: tuple[GetItemT, ...],
    ) -> None:
        self._parent = parent
        self._selectors = selectors

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._parent!r}, {self._selectors!r})"

    @property
    def operands(
        self,
    ) -> tuple[Roller[object], ...]:
        return (cast("Roller[object]", self._parent),)

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "dyce.pool-selection",
            "selectors": [
                {"start": key.start, "stop": key.stop, "step": key.step}
                if isinstance(key, slice)
                else operator.index(key)
                for key in self._selectors
            ],
        }

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        (operand,) = cast("_OperandRoll[object]", roll).operands
        expression = operand._format_expression()  # ruff: ignore[private-member-access]
        selectors = ", ".join(repr(selector) for selector in self._selectors)
        suffix = f", {selectors}" if selectors else ""
        return _RollFormat(
            f"select({expression.text}{suffix}) => {roll._format_result()}",  # ruff: ignore[private-member-access]
            _CALL_PRECEDENCE,
            has_result_suffix=True,
        )

    def _roll(self) -> Roll[_T_co]:
        parent_roll = self._parent.roll()
        outcomes = tuple(getitems(parent_roll.outcomes, self._selectors))
        if not outcomes:
            raise ValueError("no outcomes from an empty selection")
        operands = (cast("Roll[object]", parent_roll),)
        return _OperandRoll(outcomes, self, operands)

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"operands": self.operands}


class _PoolSumRoller(SingleOutcomeRoller[_CanAddSameT]):
    __slots__ = ("_pool_roller",)

    def __init__(
        self,
        pool_roller: Roller[_CanAddSameT],
    ) -> None:
        self._pool_roller = pool_roller

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._pool_roller!r})"

    @property
    def operands(
        self,
    ) -> tuple[Roller[object], ...]:
        return (cast("Roller[object]", self._pool_roller),)

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.pool-sum"}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        (operand,) = cast("_SingleOutcomeOperandRoll[object]", roll).operands
        expression = operand._format_expression()  # ruff: ignore[private-member-access]
        return _RollFormat(
            f"sum({expression.text}) => {roll._format_result()}",  # ruff: ignore[private-member-access]
            _CALL_PRECEDENCE,
            has_result_suffix=True,
        )

    def _roll(self) -> SingleOutcomeRoll[_CanAddSameT]:
        pool_roll = self._pool_roller.roll()
        outcome = _sum_outcomes(pool_roll.outcomes)
        return _SingleOutcomeOperandRoll(
            outcome, self, (cast("Roll[object]", pool_roll),)
        )

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"operands": self.operands}


class _TraceRoller(Roller[_T_co]):
    def __init__(
        self,
        callback: Callable[..., object],
        sources: tuple[Roller[Any], ...],
        label: str,
        state: dict[str, Any],
    ) -> None:
        self._callback = callback
        self._sources = sources
        self._label = label
        self._state = state

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._callback!r}, {self._sources!r}, {self._label!r}, {self._state!r})"

    @property
    def sources(self) -> tuple[Roller[Any], ...]:
        return self._sources

    def metadata(self) -> dict[str, object]:
        return {"kind": "dyce.trace", "label": self._label, "state": self._state}

    def _format_roll(self, roll: Roll[object]) -> _RollFormat:
        trace_roll = cast("_TraceRoll[object]", roll)
        arguments = ", ".join(
            argument._format_expression().text  # ruff: ignore[private-member-access]
            for argument in trace_roll.arguments
        )
        result = trace_roll.result
        expression = result._format_expression()  # ruff: ignore[private-member-access]
        return _RollFormat(
            f"{self._label}({arguments}) -> {expression.text}"
            f" => {roll._format_result()}",  # ruff: ignore[private-member-access]
            _CALL_PRECEDENCE,
            has_result_suffix=True,
        )

    def _roll(self) -> Roll[_T_co]:
        if any(not isinstance(source, Roller) for source in self._sources):
            raise TypeError("trace sources must be rollers")
        arguments = tuple(source.roll() for source in self._sources)
        result = self._callback(*arguments, **self._state)
        if isinstance(result, Roller):
            result = result.roll()
        elif not isinstance(result, Roll):
            result = LiteralRoller(result).roll()
        result_roll = cast("Roll[_T_co]", result)
        return _TraceRoll(
            result_roll.outcomes,
            self,
            cast("tuple[Roll[object], ...]", arguments),
            result_roll,
        )

    def _trace_relationships(
        self,
    ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
        return {"sources": cast("tuple[Roller[object], ...]", self.sources)}


class _OperandRoll(Roll[_T_co]):
    __slots__ = ("operands",)
    operands: tuple[Roll[object], ...]

    def __init__(
        self,
        outcomes: tuple[_T_co, ...],
        roller: Roller[_T_co],
        operands: tuple[Roll[object], ...],
    ) -> None:
        super().__init__(outcomes, roller)
        object.__setattr__(self, "operands", operands)

    def _trace_relationships(
        self,
    ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
        return {"operands": self.operands}


class _SingleOutcomeOperandRoll(SingleOutcomeRoll[_T_co]):
    __slots__ = ("operands",)
    operands: tuple[Roll[object], ...]

    def __init__(
        self,
        outcome: _T_co,
        roller: SingleOutcomeRoller[_T_co],
        operands: tuple[Roll[object], ...],
    ) -> None:
        super().__init__(outcome, roller)
        object.__setattr__(self, "operands", operands)

    def _trace_relationships(
        self,
    ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
        return {"operands": self.operands}


class _TraceRoll(Roll[_T_co]):
    __slots__ = ("arguments", "result")
    arguments: tuple[Roll[object], ...]
    result: Roll[_T_co]

    def __init__(
        self,
        outcomes: tuple[_T_co, ...],
        roller: Roller[_T_co],
        arguments: tuple[Roll[object], ...],
        result: Roll[_T_co],
    ) -> None:
        super().__init__(outcomes, roller)
        object.__setattr__(self, "arguments", arguments)
        object.__setattr__(self, "result", result)

    def _trace_relationships(
        self,
    ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
        return {
            "arguments": self.arguments,
            "result": cast("Roll[object]", self.result),
        }


class _LabeledRoll(Roll[_T_co]):
    __slots__ = ("result",)
    result: Roll[object]

    def __init__(
        self,
        outcomes: tuple[_T_co, ...],
        roller: Roller[_T_co],
        result: Roll[object],
    ) -> None:
        super().__init__(outcomes, roller)
        object.__setattr__(self, "result", result)

    def _trace_relationships(
        self,
    ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
        return {"result": self.result}


class _LabeledSingleOutcomeRoll(SingleOutcomeRoll[_T_co]):
    __slots__ = ("result",)
    result: SingleOutcomeRoll[_T_co]

    def __init__(
        self,
        outcome: _T_co,
        roller: SingleOutcomeRoller[_T_co],
        result: SingleOutcomeRoll[_T_co],
    ) -> None:
        super().__init__(outcome, roller)
        object.__setattr__(self, "result", result)

    def _trace_relationships(
        self,
    ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
        return {"result": cast("Roll[object]", self.result)}


@overload
def trace(
    callback: Callable[[], Roll[_ResultT] | Roller[_ResultT]],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[], _ResultT | Roll[_ResultT] | Roller[_ResultT]],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2], SingleOutcomeRoll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2], SingleOutcomeRoll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], Roll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], Roll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2], Roll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], SingleOutcomeRoll[_T2], Roll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2], Roll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], Roll[_T2], Roll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: Roller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2], Roll[_T3]],
        Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [Roll[_T1], Roll[_T2], Roll[_T3]],
        _ResultT | Roll[_ResultT] | Roller[_ResultT],
    ],
    source1: Roller[_T1],
    source2: Roller[_T2],
    source3: Roller[_T3],
    *,
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
@overload
def trace(
    callback: Callable[..., _ResultT | Roll[_ResultT] | Roller[_ResultT]],
    *sources: Roller[Any],
    label: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> Roll[_ResultT]: ...
def trace(
    callback: Callable[..., object],
    *sources: Roller[Any],
    label: str | None = None,
    **state: Any,
) -> Roll[Any]:
    r"""
    <!-- BEGIN MONKEY PATCH --
    For deterministic outcomes.

    >>> import random
    >>> from dyce import rng
    >>> rng.RNG = random.Random(1789600491)

      -- END MONKEY PATCH -->

    Rolls *sources*, calls *callback* with those rolls and *state*, and returns a named outcome trace.

    A returned roller is rolled, a returned roll is retained, and any other return value is wrapped in a roll from a [`LiteralRoller`][dyce.roller.LiteralRoller].
    The enclosing roll records the source rolls as arguments and the callback return as its result.
    Supplied *state* is included unchanged in the callback metadata.
    Its values must be JSON-compatible for JSON serialization of the trace.
    *label* defaults to the callback’s `__name__` or its type’s `__name__`.
    Exceptions are reported as [`RollError`][dyce.roller.RollError] with the original exception as their cause.

    Explode a d6 once, retaining both the initial roll and any additional roll:

        >>> from dyce import H
        >>> from dyce.roller import (
        ...     HRoller,
        ...     SingleOutcomeRoll,
        ...     SingleOutcomeRoller,
        ...     trace,
        ... )
        >>> d6 = HRoller(H(6), label="d6")
        >>> def explode_once(
        ...     roll: SingleOutcomeRoll[int],
        ... ) -> SingleOutcomeRoll[int] | SingleOutcomeRoller[int]:
        ...     return roll + roll.roller if roll.outcome == 6 else roll
        >>> result = trace(explode_once, d6)
        >>> result.outcomes
        (10,)
        >>> print(result.format())
        explode_once(6 [d6]) -> 6 [d6] + 4 [d6] => 10 => (10,)
    """
    trace_roller = _TraceRoller[Any](
        callback,
        sources,
        label
        if label is not None
        else getattr(callback, "__name__", type(callback).__name__),
        state,
    )
    return trace_roller.roll()


def _as_single_outcome_roller(
    value: _T | HableT[_T] | Roller[_T],
) -> SingleOutcomeRoller[_T]:
    if isinstance(value, Roller):
        return cast("SingleOutcomeRoller[_T]", cast("Roller[Any]", value).sum())
    elif isinstance(value, H):
        return HRoller(value)
    elif isinstance(value, P):
        pool_roller = PRoller(value)
        return cast(
            "SingleOutcomeRoller[_T]",
            cast("Roller[Any]", pool_roller).sum(),
        )
    elif isinstance(value, HableT):
        return HableRoller(value)
    else:
        return LiteralRoller(value)


def _as_single_outcome_roll(
    value: _T | Roll[_T],
) -> SingleOutcomeRoll[_T]:
    if isinstance(value, Roll):
        return cast("SingleOutcomeRoll[_T]", cast("Roll[Any]", value).sum())
    else:
        return LiteralRoller(value).roll()


def _binary_roller(
    lhs: object,
    rhs: object,
    operation: _BinaryOperation,
) -> object:
    if isinstance(lhs, Roll) or isinstance(rhs, Roll):
        return NotImplemented
    return _BinaryRoller(
        _as_single_outcome_roller(lhs),
        _as_single_outcome_roller(rhs),
        operation,
    )


def _sum_outcomes(outcomes: tuple[_CanAddSameT, ...]) -> _CanAddSameT:
    return reduce(operator.add, outcomes[1:], outcomes[0])

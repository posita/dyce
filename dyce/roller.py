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
from abc import abstractmethod
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from functools import reduce, wraps
from typing import Any, Generic, ParamSpec, Protocol, TypeVar, cast, final, overload

import optype as ot

from .h import H, HableT
from .lifecycle import experimental
from .p import P
from .types import GetItemT, getitems, natural_key

__all__ = (
    "HRoller",
    "HableRoller",
    "LiteralRoller",
    "MultiOutcomeRoll",
    "MultiOutcomeRoller",
    "PRoller",
    "RollError",
    "RollerPool",
    "SingleOutcomeRoll",
    "SingleOutcomeRoller",
    "roller_factory",
    "trace",
)

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")
_CanAddSameT = TypeVar("_CanAddSameT", bound=ot.CanAddSame)
_ParamsT = ParamSpec("_ParamsT")


class RollError(Exception):
    r"""
    A failure during rolling, with the original exception in `__cause__`.

    *path* contains the participating rollers from the outermost call to the failing call.
    """

    def __init__(
        self,
        message: str,
        path: tuple[
            "SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any] | _TraceCall", ...
        ],
    ) -> None:
        super().__init__(message)
        self.path = path

    def __str__(self) -> str:
        labels = []
        for roller in self.path:
            label = repr(roller.metadata())
            labels.append(label)
        return super().__str__() + "\nRoller path:\n  " + "\n  → ".join(labels)


@dataclass(frozen=True, slots=True)
class _BinaryOperator:
    name: str
    function: Callable[[object, object], object]

    def __call__(self, lhs: object, rhs: object) -> object:
        return self.function(lhs, rhs)


@dataclass(frozen=True, slots=True)
class _UnaryOperator:
    name: str
    function: Callable[[object], object]

    def __call__(self, operand: object) -> object:
        return self.function(operand)


def _sum_outcomes(outcomes: Iterable[_CanAddSameT]) -> _CanAddSameT:
    iterator = iter(outcomes)
    try:
        first = next(iterator)
    except StopIteration:
        raise ValueError("no outcomes to sum") from None
    return reduce(operator.add, iterator, first)


_ADD = _BinaryOperator("add", cast("Callable[[object, object], object]", operator.add))
_SUB = _BinaryOperator("sub", cast("Callable[[object, object], object]", operator.sub))
_MUL = _BinaryOperator("mul", cast("Callable[[object, object], object]", operator.mul))
_TRUEDIV = _BinaryOperator(
    "truediv", cast("Callable[[object, object], object]", operator.truediv)
)
_FLOORDIV = _BinaryOperator(
    "floordiv", cast("Callable[[object, object], object]", operator.floordiv)
)
_MOD = _BinaryOperator("mod", cast("Callable[[object, object], object]", operator.mod))
_POW = _BinaryOperator("pow", cast("Callable[[object, object], object]", operator.pow))
_LSHIFT = _BinaryOperator(
    "lshift", cast("Callable[[object, object], object]", operator.lshift)
)
_RSHIFT = _BinaryOperator(
    "rshift", cast("Callable[[object, object], object]", operator.rshift)
)
_AND = _BinaryOperator("and", cast("Callable[[object, object], object]", operator.and_))
_OR = _BinaryOperator("or", cast("Callable[[object, object], object]", operator.or_))
_XOR = _BinaryOperator("xor", cast("Callable[[object, object], object]", operator.xor))
_NEG = _UnaryOperator("neg", cast("Callable[[object], object]", operator.neg))
_POS = _UnaryOperator("pos", cast("Callable[[object], object]", operator.pos))
_ABS = _UnaryOperator("abs", cast("Callable[[object], object]", operator.abs))
_INVERT = _UnaryOperator("invert", cast("Callable[[object], object]", operator.invert))


class SingleOutcomeRoller(HableT[_T_co]):
    r"""A computation capable of producing deferred, traceable samples."""

    __slots__ = ()

    # Roll-aware overloads preserve asymmetric expression typing for static checkers
    @overload
    def __add__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "SingleOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "SingleOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "SingleOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __add__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _ADD)

    @overload
    def __sub__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "SingleOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "SingleOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "SingleOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __sub__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _SUB)

    @overload
    def __mul__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "SingleOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "SingleOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "SingleOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mul__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MUL)

    @overload
    def __truediv__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "SingleOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "SingleOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "SingleOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __truediv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _TRUEDIV)

    @overload
    def __floordiv__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "SingleOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "SingleOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "SingleOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _FLOORDIV)

    @overload
    def __mod__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "SingleOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "SingleOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "SingleOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mod__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MOD)

    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[_T_co]",
        rhs: "SingleOutcomeRoll[ot.CanRPow[_T_co, _ResultT]] | MultiOutcomeRoll[ot.CanRPow[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "SingleOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "SingleOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "SingleOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __pow__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _POW)

    @overload
    def __lshift__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "SingleOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "SingleOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "SingleOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __lshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _LSHIFT)

    @overload
    def __rshift__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "SingleOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "SingleOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "SingleOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _RSHIFT)

    @overload
    def __and__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "SingleOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "SingleOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "SingleOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __and__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _AND)

    @overload
    def __or__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "SingleOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "SingleOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "SingleOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __or__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _OR)

    @overload
    def __xor__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "SingleOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "SingleOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "SingleOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __xor__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "SingleOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __radd__(
        self: "SingleOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __radd__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _ADD)

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "SingleOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rsub__(
        self: "SingleOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rsub__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _SUB)

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "SingleOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmul__(
        self: "SingleOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmul__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MUL)

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "SingleOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "SingleOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _TRUEDIV)

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "SingleOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "SingleOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _FLOORDIV)

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "SingleOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmod__(
        self: "SingleOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmod__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MOD)

    @overload
    def __rpow__(  # type: ignore[overload-overlap]
        self: "SingleOutcomeRoller[_T_co]",
        lhs: "SingleOutcomeRoll[ot.CanPow2[_T_co, _ResultT]] | MultiOutcomeRoll[ot.CanPow2[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "SingleOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rpow__(
        self: "SingleOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rpow__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _POW)

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "SingleOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "SingleOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _LSHIFT)

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "SingleOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "SingleOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _RSHIFT)

    @overload
    def __rand__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "SingleOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rand__(
        self: "SingleOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rand__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _AND)

    @overload
    def __ror__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "SingleOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __ror__(
        self: "SingleOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __ror__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _OR)

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "SingleOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "SingleOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rxor__(
        self: "SingleOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rxor__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _XOR)

    def __neg__(
        self: "SingleOutcomeRoller[ot.CanNeg[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast("SingleOutcomeRoller[_ResultT]", _UnaryRoller(self, _NEG))

    def __pos__(
        self: "SingleOutcomeRoller[ot.CanPos[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast("SingleOutcomeRoller[_ResultT]", _UnaryRoller(self, _POS))

    def __abs__(
        self: "SingleOutcomeRoller[ot.CanAbs[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast("SingleOutcomeRoller[_ResultT]", _UnaryRoller(self, _ABS))

    def __invert__(
        self: "SingleOutcomeRoller[ot.CanInvert[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast("SingleOutcomeRoller[_ResultT]", _UnaryRoller(self, _INVERT))

    @property
    def operands(
        self,
    ) -> tuple["MultiOutcomeRoller[object] | SingleOutcomeRoller[object]", ...]:
        r"""The immediate rollers consumed by this roller, if any."""
        return ()

    @abstractmethod
    def metadata(self) -> dict[str, object]:
        r"""Returns JSON-compatible metadata describing this roller."""

    @final
    def roll(self) -> "SingleOutcomeRoll[_T_co]":
        r"""
        Produces a sample outcome trace, reporting failures as [`RollError`][dyce.roller.RollError].

        Subclasses implement the [`_roll` method][dyce.roller.SingleOutcomeRoller._roll] instead of overriding this method.
        """
        try:
            return self._roll()
        except RollError as exc:
            exc.path = (self, *exc.path)
            raise
        except Exception as exc:
            raise RollError(str(exc), (self,)) from exc

    @abstractmethod
    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        r"""
        Subclass implementation hook for producing a sample outcome trace.

        Child rollers should be called via their public [`roll` methods][dyce.roller.SingleOutcomeRoller.roll].
        """


class HRoller(SingleOutcomeRoller[_T_co]):
    r"""A roller backed by [`H.roll`][dyce.H.roll]."""

    __slots__ = ("_h", "_name")

    @experimental
    def __init__(self, h: H[_T_co], *, name: str | None = None) -> None:
        self._h = h
        self._name = name if name is not None else str(h)

    def h(self) -> H[_T_co]:
        r"""Returns this roller’s [`H`][dyce.H] source object."""
        return self._h

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "source",
            "name": self._name,
        }

    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        return SingleOutcomeRoll(self._h.roll(), self)


class HableRoller(SingleOutcomeRoller[_T_co]):
    r"""A roller backed by a [`HableT`][dyce.HableT]."""

    __slots__ = ("_hable", "_name")

    @experimental
    def __init__(self, hable: HableT[_T_co], *, name: str | None = None) -> None:
        self._hable = hable
        self._name = name if name is not None else str(hable)

    @property
    def hable(self) -> HableT[_T_co]:
        r"""Returns this roller’s [`HableT`][dyce.HableT] source object."""
        return self._hable

    def h(self) -> H[_T_co]:
        return self._hable.h()

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "source",
            "name": self._name,
        }

    def _roll(self) -> "SingleOutcomeRoll[_T_co]":
        return SingleOutcomeRoll(self.h().roll(), self)


class LiteralRoller(SingleOutcomeRoller[_T]):
    r"""A deterministic roller for a single, literal value."""

    __slots__ = ("_value",)

    @experimental
    def __init__(self, value: _T) -> None:
        self._value = value

    @property
    def value(self) -> _T:
        r"""Returns this roller’s source value."""
        return self._value

    def h(self) -> H[_T]:
        return H({self._value: 1})

    def metadata(self) -> dict[str, object]:
        return {"kind": "literal", "value": self._value}

    def _roll(self) -> "SingleOutcomeRoll[_T]":
        return SingleOutcomeRoll(self._value, self)


class MultiOutcomeRoller(HableT[_T_co]):
    r"""
    A deferred, traceable computation producing a tuple of outcomes.
    “Multi” describes the collection result, which may contain just one outcome.
    """

    __slots__ = ()

    # This and the other Roll-aware overloads preserve asymmetric expression typing
    # for static checkers; runtime implementations defer Roll operands via NotImplemented.
    @overload
    def __add__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "MultiOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "MultiOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "MultiOutcomeRoller[ot.CanAdd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __add__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _ADD)

    @overload
    def __sub__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "MultiOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "MultiOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __sub__(
        self: "MultiOutcomeRoller[ot.CanSub[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __sub__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _SUB)

    @overload
    def __mul__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "MultiOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "MultiOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mul__(
        self: "MultiOutcomeRoller[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mul__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MUL)

    @overload
    def __truediv__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "MultiOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "MultiOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "MultiOutcomeRoller[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __truediv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _TRUEDIV)

    @overload
    def __floordiv__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "MultiOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "MultiOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "MultiOutcomeRoller[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _FLOORDIV)

    @overload
    def __mod__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "MultiOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "MultiOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __mod__(
        self: "MultiOutcomeRoller[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __mod__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _MOD)

    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[_T_co]",
        rhs: "SingleOutcomeRoll[ot.CanRPow[_T_co, _ResultT]] | MultiOutcomeRoll[ot.CanRPow[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "MultiOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "MultiOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __pow__(
        self: "MultiOutcomeRoller[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __pow__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _POW)

    @overload
    def __lshift__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "MultiOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "MultiOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "MultiOutcomeRoller[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __lshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _LSHIFT)

    @overload
    def __rshift__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "MultiOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "MultiOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "MultiOutcomeRoller[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rshift__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _RSHIFT)

    @overload
    def __and__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "MultiOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "MultiOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __and__(
        self: "MultiOutcomeRoller[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __and__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _AND)

    @overload
    def __or__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "MultiOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "MultiOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __or__(
        self: "MultiOutcomeRoller[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __or__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _OR)

    @overload
    def __xor__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "MultiOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "MultiOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __xor__(
        self: "MultiOutcomeRoller[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __xor__(self, rhs: object) -> object:
        return _binary_roller(self, rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "MultiOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __radd__(
        self: "MultiOutcomeRoller[ot.CanRAdd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __radd__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _ADD)

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "MultiOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rsub__(
        self: "MultiOutcomeRoller[ot.CanRSub[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rsub__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _SUB)

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "MultiOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmul__(
        self: "MultiOutcomeRoller[ot.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmul__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MUL)

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "MultiOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "MultiOutcomeRoller[ot.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _TRUEDIV)

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "MultiOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "MultiOutcomeRoller[ot.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _FLOORDIV)

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "MultiOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rmod__(
        self: "MultiOutcomeRoller[ot.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rmod__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _MOD)

    @overload
    def __rpow__(  # type: ignore[overload-overlap]
        self: "MultiOutcomeRoller[_T_co]",
        lhs: "SingleOutcomeRoll[ot.CanPow2[_T_co, _ResultT]] | MultiOutcomeRoll[ot.CanPow2[_T_co, _ResultT]]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "MultiOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rpow__(
        self: "MultiOutcomeRoller[ot.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rpow__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _POW)

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "MultiOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "MultiOutcomeRoller[ot.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _LSHIFT)

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "MultiOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "MultiOutcomeRoller[ot.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _RSHIFT)

    @overload
    def __rand__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "MultiOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rand__(
        self: "MultiOutcomeRoller[ot.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rand__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _AND)

    @overload
    def __ror__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "MultiOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __ror__(
        self: "MultiOutcomeRoller[ot.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __ror__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _OR)

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "MultiOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "MultiOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    @overload
    def __rxor__(
        self: "MultiOutcomeRoller[ot.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "SingleOutcomeRoller[_ResultT]": ...
    def __rxor__(self, lhs: object) -> object:
        return _binary_roller(lhs, self, _XOR)

    def __neg__(
        self: "MultiOutcomeRoller[ot.CanNeg[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]", _UnaryRoller(_as_roller(self), _NEG)
        )

    def __pos__(
        self: "MultiOutcomeRoller[ot.CanPos[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]", _UnaryRoller(_as_roller(self), _POS)
        )

    def __abs__(
        self: "MultiOutcomeRoller[ot.CanAbs[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]", _UnaryRoller(_as_roller(self), _ABS)
        )

    def __invert__(
        self: "MultiOutcomeRoller[ot.CanInvert[_ResultT]]",
    ) -> "SingleOutcomeRoller[_ResultT]":
        return cast(
            "SingleOutcomeRoller[_ResultT]", _UnaryRoller(_as_roller(self), _INVERT)
        )

    @property
    def operands(
        self,
    ) -> tuple["MultiOutcomeRoller[object] | SingleOutcomeRoller[object]", ...]:
        r"""The immediate rollers consumed by this multi roller, if any."""
        return ()

    def at(
        self: "MultiOutcomeRoller[_CanAddSameT]", which: GetItemT, *more: GetItemT
    ) -> SingleOutcomeRoller[_CanAddSameT]:
        r"""Returns a roller summing the outcomes at the selected positions."""
        return self.select(which, *more).sum()

    def h(self) -> H[_T_co]:
        r"""Returns the distribution of the sum of this multi roller's outcomes."""
        return cast(
            "H[_T_co]",
            H.from_counts(
                (
                    (_sum_outcomes(cast("Iterable[Any]", roll)), count)
                    for roll, count in self.rolls_with_counts()
                    if roll
                )
            ),
        )

    @abstractmethod
    def metadata(self) -> dict[str, object]:
        r"""Returns JSON-compatible metadata describing this multi roller."""

    @final
    def roll(self) -> "MultiOutcomeRoll[_T_co]":
        r"""
        Produces a sample outcome collection trace, reporting failures as [`RollError`][dyce.roller.RollError].

        Subclasses implement the [`_roll` method][dyce.roller.MultiOutcomeRoller._roll] instead of overriding this method.
        """
        try:
            return self._roll()
        except RollError as exc:
            exc.path = (self, *exc.path)
            raise
        except Exception as exc:
            raise RollError(str(exc), (self,)) from exc

    @abstractmethod
    def _roll(self) -> "MultiOutcomeRoll[_T_co]":
        r"""
        Subclass implementation hook for producing a nonempty sample outcome collection trace.

        Raises `ValueError` if no outcomes can be produced.
        Child rollers should be called via their public [`roll` methods][dyce.roller.MultiOutcomeRoller.roll].
        """

    @abstractmethod
    def rolls_with_counts(self) -> Iterator[tuple[tuple[_T_co, ...], int]]:
        r"""Yields the possible pool outcomes and their weights."""

    def select(self, which: GetItemT, *more: GetItemT) -> "MultiOutcomeRoller[_T_co]":
        r"""
        Returns a multi roller selecting the specified positions.

        Selectors are resolved against each tuple produced when rolling or enumerating outcomes.
        Invalid indices raise at that time rather than during construction.
        """
        return _SelectedPoolRoller(self, (which, *more))

    def sum(
        self: "MultiOutcomeRoller[_CanAddSameT]",
    ) -> SingleOutcomeRoller[_CanAddSameT]:
        r"""
        Returns a roller summing every outcome.

        An empty pool or selection has an empty sum distribution and raises `ValueError` when rolled.
        """
        return _PoolSumRoller(self)


class PRoller(MultiOutcomeRoller[_T_co]):
    r"""A multi roller backed by a [`P`][dyce.P]."""

    __slots__ = ("_name", "_p")

    @experimental
    def __init__(self, p: P[_T_co], *, name: str | None = None) -> None:
        self._p = p
        self._name = name if name is not None else str(p)

    def __len__(self) -> int:
        return len(self._p)

    @property
    def p(self) -> P[_T_co]:
        r"""Returns this multi roller’s [`P`][dyce.P] source object."""
        return self._p

    def h(self) -> H[_T_co]:
        return self._p.h()

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "pool-source",
            "name": self._name,
        }

    def _roll(self) -> "MultiOutcomeRoll[_T_co]":
        outcomes = self._p.roll()
        return MultiOutcomeRoll(outcomes, self)

    def rolls_with_counts(self) -> Iterator[tuple[tuple[_T_co, ...], int]]:
        if not self._p:
            yield (), 1
        else:
            yield from self._p.rolls_with_counts()


class RollerPool(MultiOutcomeRoller[_T_co]):
    r"""A multi roller backed by one or more [`SingleOutcomeRoller`][dyce.roller.SingleOutcomeRoller] objects."""

    __slots__ = ("_name", "_rollers")

    @experimental
    def __init__(
        self, *rollers: SingleOutcomeRoller[_T_co], name: str | None = None
    ) -> None:
        self._rollers = rollers
        self._name = name

    def __len__(self) -> int:
        return len(self._rollers)

    @property
    def operands(
        self,
    ) -> tuple["MultiOutcomeRoller[object] | SingleOutcomeRoller[object]", ...]:
        return cast(
            "tuple[MultiOutcomeRoller[object] | SingleOutcomeRoller[object], ...]",
            self._rollers,
        )

    @property
    def rollers(self) -> tuple[SingleOutcomeRoller[_T_co], ...]:
        r"""This multi roller’s [`SingleOutcomeRoller`][dyce.roller.SingleOutcomeRoller] source objects."""
        return self._rollers

    def h(self) -> H[_T_co]:
        return P(*(roller.h() for roller in self._rollers)).h()

    def metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {"kind": "pool"}
        if self._name is not None:
            metadata["name"] = self._name
        return metadata

    def _roll(self) -> "MultiOutcomeRoll[_T_co]":
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
            "tuple[MultiOutcomeRoll[object] | SingleOutcomeRoll[object], ...]",
            tuple(rolls),
        )
        return MultiOutcomeRoll(outcomes, self, operands)

    def rolls_with_counts(self) -> Iterator[tuple[tuple[_T_co, ...], int]]:
        if not self._rollers:
            yield (), 1
        else:
            yield from P(*(roller.h() for roller in self._rollers)).rolls_with_counts()


@dataclass(frozen=True, slots=True, eq=False)
class SingleOutcomeRoll(Generic[_T_co]):
    r"""
    An immutable outcome trace.
    """

    outcome: _T_co
    roller: SingleOutcomeRoller[_T_co] = field(repr=False)
    operands: tuple["MultiOutcomeRoll[object] | SingleOutcomeRoll[object]", ...] = (
        field(default=(), repr=False)
    )

    @overload
    def __add__(
        self: "SingleOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "SingleOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __add__(
        self: "SingleOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __add__(
        self,
        rhs: object,
    ) -> "SingleOutcomeRoll[object]":
        if isinstance(rhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            rhs = rhs.roll()
        return self._binary_operator(rhs, _ADD)

    @overload
    def __sub__(
        self: "SingleOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "SingleOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __sub__(
        self: "SingleOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __sub__(
        self,
        rhs: object,
    ) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _SUB)

    @overload
    def __mul__(
        self: "SingleOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "SingleOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mul__(
        self: "SingleOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __mul__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _MUL)

    @overload
    def __truediv__(
        self: "SingleOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "SingleOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "SingleOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __truediv__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _TRUEDIV)

    @overload
    def __floordiv__(
        self: "SingleOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "SingleOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "SingleOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _FLOORDIV)

    @overload
    def __mod__(
        self: "SingleOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "SingleOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __mod__(
        self: "SingleOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __mod__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _MOD)

    @overload
    def __pow__(
        self: "SingleOutcomeRoll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __pow__(
        self: "SingleOutcomeRoll[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __pow__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _POW)

    @overload
    def __lshift__(
        self: "SingleOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "SingleOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "SingleOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __lshift__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _LSHIFT)

    @overload
    def __rshift__(
        self: "SingleOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "SingleOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "SingleOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rshift__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _RSHIFT)

    @overload
    def __and__(
        self: "SingleOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "SingleOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __and__(
        self: "SingleOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __and__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _AND)

    @overload
    def __or__(
        self: "SingleOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "SingleOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __or__(
        self: "SingleOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __or__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _OR)

    @overload
    def __xor__(
        self: "SingleOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "SingleOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __xor__(
        self: "SingleOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __xor__(self, rhs: object) -> "SingleOutcomeRoll[object]":
        return self._binary_operator(rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __radd__(
        self: "SingleOutcomeRoll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __radd__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        if isinstance(lhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            lhs = lhs.roll()
        return self._reflected_binary_operator(lhs, _ADD)

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rsub__(
        self: "SingleOutcomeRoll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rsub__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _SUB)

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmul__(
        self: "SingleOutcomeRoll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rmul__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _MUL)

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "SingleOutcomeRoll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _TRUEDIV)

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "SingleOutcomeRoll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _FLOORDIV)

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rmod__(
        self: "SingleOutcomeRoll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rmod__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _MOD)

    @overload
    def __rpow__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rpow__(
        self: "SingleOutcomeRoll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rpow__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _POW)

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "SingleOutcomeRoll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _LSHIFT)

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "SingleOutcomeRoll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _RSHIFT)

    @overload
    def __rand__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rand__(
        self: "SingleOutcomeRoll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rand__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _AND)

    @overload
    def __ror__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __ror__(
        self: "SingleOutcomeRoll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __ror__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _OR)

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "SingleOutcomeRoll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    @overload
    def __rxor__(
        self: "SingleOutcomeRoll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "SingleOutcomeRoll[_ResultT]": ...
    def __rxor__(self, lhs: object) -> "SingleOutcomeRoll[object]":
        return self._reflected_binary_operator(lhs, _XOR)

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

    def trace(self) -> dict[str, object]:
        r"""
        Returns the execution trace rooted at this roll, composed of JSON-compatible containers.

        The `root` entry identifies a record in `rolls`.
        Each roll’s `roller` entry identifies its producing roller in `rollers`.
        Outcomes and literal values must themselves be JSON-compatible for the complete trace to be serializable as JSON.
        """
        return _trace_from_root_roll(cast("SingleOutcomeRoll[object]", self))

    def _binary_operator(
        self, rhs: object, operator: _BinaryOperator
    ) -> "SingleOutcomeRoll[object]":
        if isinstance(rhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            rhs = rhs.roll()
        rhs_roll = _as_roll(rhs)
        roller: SingleOutcomeRoller[object] = _BinaryRoller(
            self.roller, rhs_roll.roller, operator
        )
        outcome = operator(self.outcome, rhs_roll.outcome)
        return SingleOutcomeRoll(outcome, roller, (self, rhs_roll))

    def _reflected_binary_operator(
        self, lhs: object, operator: _BinaryOperator
    ) -> "SingleOutcomeRoll[object]":
        if isinstance(lhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            lhs = lhs.roll()
        lhs_roll = _as_roll(lhs)
        roller: SingleOutcomeRoller[object] = _BinaryRoller(
            lhs_roll.roller, self.roller, operator
        )
        outcome = operator(lhs_roll.outcome, self.outcome)
        return SingleOutcomeRoll(outcome, roller, (lhs_roll, self))

    def _unary_operator(self, operator: _UnaryOperator) -> "SingleOutcomeRoll[object]":
        roller: SingleOutcomeRoller[object] = _UnaryRoller(self.roller, operator)
        outcome = operator(self.outcome)
        return SingleOutcomeRoll(outcome, roller, (self,))


@dataclass(frozen=True, slots=True, eq=False)
class MultiOutcomeRoll(Generic[_T_co]):
    r"""An immutable trace of a collection of outcomes."""

    outcomes: tuple[_T_co, ...]
    roller: MultiOutcomeRoller[_T_co] = field(repr=False)
    operands: tuple["MultiOutcomeRoll[object] | SingleOutcomeRoll[object]", ...] = (
        field(default=(), repr=False)
    )

    @overload
    def __add__(
        self: "MultiOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __add__(
        self: "MultiOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __add__(
        self: "MultiOutcomeRoll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __add__(
        self,
        rhs: object,
    ) -> SingleOutcomeRoll[object]:
        if isinstance(rhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            rhs = rhs.roll()
        return _as_roll(cast("object", self))._binary_operator(rhs, _ADD)

    @overload
    def __sub__(
        self: "MultiOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __sub__(
        self: "MultiOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __sub__(
        self: "MultiOutcomeRoll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __sub__(
        self,
        rhs: object,
    ) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _SUB)

    @overload
    def __mul__(
        self: "MultiOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __mul__(
        self: "MultiOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __mul__(
        self: "MultiOutcomeRoll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __mul__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _MUL)

    @overload
    def __truediv__(
        self: "MultiOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __truediv__(
        self: "MultiOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __truediv__(
        self: "MultiOutcomeRoll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __truediv__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _TRUEDIV)

    @overload
    def __floordiv__(
        self: "MultiOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __floordiv__(
        self: "MultiOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __floordiv__(
        self: "MultiOutcomeRoll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __floordiv__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _FLOORDIV)

    @overload
    def __mod__(
        self: "MultiOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __mod__(
        self: "MultiOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __mod__(
        self: "MultiOutcomeRoll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __mod__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _MOD)

    @overload
    def __pow__(
        self: "MultiOutcomeRoll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __pow__(
        self: "MultiOutcomeRoll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __pow__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _POW)

    @overload
    def __lshift__(
        self: "MultiOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __lshift__(
        self: "MultiOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __lshift__(
        self: "MultiOutcomeRoll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __lshift__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _LSHIFT)

    @overload
    def __rshift__(
        self: "MultiOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rshift__(
        self: "MultiOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rshift__(
        self: "MultiOutcomeRoll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rshift__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _RSHIFT)

    @overload
    def __and__(
        self: "MultiOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __and__(
        self: "MultiOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __and__(
        self: "MultiOutcomeRoll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __and__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _AND)

    @overload
    def __or__(
        self: "MultiOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __or__(
        self: "MultiOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __or__(
        self: "MultiOutcomeRoll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __or__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _OR)

    @overload
    def __xor__(
        self: "MultiOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoller[_OtherT] | MultiOutcomeRoller[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __xor__(
        self: "MultiOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __xor__(
        self: "MultiOutcomeRoll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __xor__(self, rhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._binary_operator(rhs, _XOR)

    @overload
    def __radd__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __radd__(
        self: "MultiOutcomeRoll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __radd__(self, lhs: object) -> SingleOutcomeRoll[object]:
        if isinstance(lhs, (SingleOutcomeRoller, MultiOutcomeRoller)):
            lhs = lhs.roll()
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _ADD)

    @overload
    def __rsub__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rsub__(
        self: "MultiOutcomeRoll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rsub__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _SUB)

    @overload
    def __rmul__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rmul__(
        self: "MultiOutcomeRoll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rmul__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _MUL)

    @overload
    def __rtruediv__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rtruediv__(
        self: "MultiOutcomeRoll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rtruediv__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _TRUEDIV)

    @overload
    def __rfloordiv__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rfloordiv__(
        self: "MultiOutcomeRoll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rfloordiv__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _FLOORDIV)

    @overload
    def __rmod__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rmod__(
        self: "MultiOutcomeRoll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rmod__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _MOD)

    @overload
    def __rpow__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rpow__(
        self: "MultiOutcomeRoll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rpow__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _POW)

    @overload
    def __rlshift__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rlshift__(
        self: "MultiOutcomeRoll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rlshift__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _LSHIFT)

    @overload
    def __rrshift__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rrshift__(
        self: "MultiOutcomeRoll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rrshift__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _RSHIFT)

    @overload
    def __rand__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rand__(
        self: "MultiOutcomeRoll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rand__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _AND)

    @overload
    def __ror__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __ror__(
        self: "MultiOutcomeRoll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __ror__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _OR)

    @overload
    def __rxor__(  # type: ignore[misc]
        self: "MultiOutcomeRoll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "SingleOutcomeRoll[_OtherT] | MultiOutcomeRoll[_OtherT]",
    ) -> SingleOutcomeRoll[_ResultT]: ...
    @overload
    def __rxor__(
        self: "MultiOutcomeRoll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> SingleOutcomeRoll[_ResultT]: ...
    def __rxor__(self, lhs: object) -> SingleOutcomeRoll[object]:
        return _as_roll(cast("object", self))._reflected_binary_operator(lhs, _XOR)

    def sum(self: "MultiOutcomeRoll[_CanAddSameT]") -> SingleOutcomeRoll[_CanAddSameT]:
        r"""
        Returns the sum of this multi roll’s outcomes.

        Raises `ValueError` if there are no outcomes.
        """
        roller = self.roller.sum()
        outcome = _sum_outcomes(self.outcomes)
        return SingleOutcomeRoll(
            outcome, roller, (cast("MultiOutcomeRoll[object]", self),)
        )

    def trace(self) -> dict[str, object]:
        r"""
        Returns the execution trace rooted at this roll, composed of JSON-compatible containers.

        The `root` entry identifies a record in `rolls`.
        Each roll’s `roller` entry identifies its producing roller in `rollers`.
        Outcomes and literal values must themselves be JSON-compatible for the complete trace to be serializable as JSON.
        """
        return _trace_from_root_roll(cast("MultiOutcomeRoll[object]", self))


class _BinaryRoller(SingleOutcomeRoller[_ResultT]):
    __slots__ = ("_left", "_operator", "_right")

    def __init__(
        self,
        left: SingleOutcomeRoller[object],
        right: SingleOutcomeRoller[object],
        operator: _BinaryOperator,
    ) -> None:
        self._left = left
        self._right = right
        self._operator = operator

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[object], ...]:
        return (self._left, self._right)

    def h(self) -> H[_ResultT]:
        return cast("H[_ResultT]", self._operator(self._left.h(), self._right.h()))

    def metadata(self) -> dict[str, object]:
        return {"kind": "binary", "operator": self._operator.name}

    def _roll(self) -> SingleOutcomeRoll[_ResultT]:
        left_roll = self._left.roll()
        right_roll = self._right.roll()
        outcome = self._operator(left_roll.outcome, right_roll.outcome)
        return SingleOutcomeRoll(
            cast("_ResultT", outcome), self, (left_roll, right_roll)
        )


class _UnaryRoller(SingleOutcomeRoller[_ResultT]):
    __slots__ = ("_operand", "_operator")

    def __init__(
        self, operand: SingleOutcomeRoller[object], operator: _UnaryOperator
    ) -> None:
        self._operand = operand
        self._operator = operator

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[object], ...]:
        return (self._operand,)

    def h(self) -> H[_ResultT]:
        return cast("H[_ResultT]", self._operator(self._operand.h()))

    def metadata(self) -> dict[str, object]:
        return {"kind": "unary", "operator": self._operator.name}

    def _roll(self) -> SingleOutcomeRoll[_ResultT]:
        operand_roll = self._operand.roll()
        outcome = self._operator(operand_roll.outcome)
        return SingleOutcomeRoll(cast("_ResultT", outcome), self, (operand_roll,))


class _PoolSumRoller(SingleOutcomeRoller[_CanAddSameT]):
    __slots__ = ("_pool_roller",)

    def __init__(
        self,
        pool_roller: MultiOutcomeRoller[_CanAddSameT],
    ) -> None:
        self._pool_roller = pool_roller

    @property
    def operands(
        self,
    ) -> tuple["MultiOutcomeRoller[object] | SingleOutcomeRoller[object]", ...]:
        return (cast("MultiOutcomeRoller[object]", self._pool_roller),)

    def h(self) -> H[_CanAddSameT]:
        return self._pool_roller.h()

    def metadata(self) -> dict[str, object]:
        return {"kind": "pool-sum"}

    def _roll(self) -> SingleOutcomeRoll[_CanAddSameT]:
        pool_roll = self._pool_roller.roll()
        outcome = _sum_outcomes(pool_roll.outcomes)
        return SingleOutcomeRoll(
            outcome, self, (cast("MultiOutcomeRoll[object]", pool_roll),)
        )


class _SelectedPoolRoller(MultiOutcomeRoller[_T_co]):
    __slots__ = ("_parent", "_selectors")

    def __init__(
        self,
        parent: MultiOutcomeRoller[_T_co],
        selectors: tuple[GetItemT, ...],
    ) -> None:
        self._parent = parent
        self._selectors = selectors

    @property
    def operands(
        self,
    ) -> tuple["MultiOutcomeRoller[object] | SingleOutcomeRoller[object]", ...]:
        return (cast("MultiOutcomeRoller[object]", self._parent),)

    def metadata(self) -> dict[str, object]:
        return {
            "kind": "pool-selection",
            "selectors": [
                {"start": key.start, "stop": key.stop, "step": key.step}
                if isinstance(key, slice)
                else operator.index(key)
                for key in self._selectors
            ],
        }

    def _roll(self) -> "MultiOutcomeRoll[_T_co]":
        parent_roll = self._parent.roll()
        outcomes = tuple(getitems(parent_roll.outcomes, self._selectors))
        if not outcomes:
            raise ValueError("no outcomes from an empty selection")
        operands = (cast("MultiOutcomeRoll[object]", parent_roll),)
        return MultiOutcomeRoll(outcomes, self, operands)

    def rolls_with_counts(self) -> Iterator[tuple[tuple[_T_co, ...], int]]:
        yield from (
            (tuple(getitems(roll, self._selectors)), count)
            for roll, count in self._parent.rolls_with_counts()
        )


@dataclass(frozen=True)
class _TraceCall:
    callback: Callable[..., object]
    sources: tuple[SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any], ...]
    name: str
    state: dict[str, Any]

    def metadata(self) -> dict[str, object]:
        return {"kind": "trace", "name": self.name, "state": self.state}


class _TraceRoller:
    def __init__(
        self,
        call: _TraceCall,
        result_roller: SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any],
    ) -> None:
        self._call = call
        self._result_roller = result_roller

    @property
    def operands(
        self,
    ) -> tuple[SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any], ...]:
        return (*self._call.sources, self._result_roller)

    def metadata(self) -> dict[str, object]:
        return self._call.metadata()

    def h(self) -> H[Any]:  # pragma: no cover
        raise NotImplementedError(
            "trace callbacks do not support distribution computation"
        )


class _SingleOutcomeTraceRoller(_TraceRoller, SingleOutcomeRoller[_T_co]):
    def _roll(self) -> SingleOutcomeRoll[_T_co]:
        result = _eval_trace_call(self._call)
        if not isinstance(result, SingleOutcomeRoll):  # pragma: no cover
            raise TypeError(
                f"trace callback did not produce a single outcome when called again ({result!r})"
            )
        return result


class _MultiOutcomeTraceRoller(_TraceRoller, MultiOutcomeRoller[_T_co]):
    def _roll(self) -> MultiOutcomeRoll[_T_co]:
        result = _eval_trace_call(self._call)
        if not isinstance(result, MultiOutcomeRoll):  # pragma: no cover
            raise TypeError(
                f"trace callback did not produce multiple outcomes when called again ({result!r})"
            )
        return result

    def rolls_with_counts(
        self,
    ) -> Iterator[tuple[tuple[_T_co, ...], int]]:  # pragma: no cover
        raise NotImplementedError(
            "trace callbacks do not support distribution computation"
        )


class _RollerFactoryDecorator(Protocol):
    @overload
    def __call__(
        self, fn: Callable[_ParamsT, SingleOutcomeRoller[_T]], /
    ) -> Callable[_ParamsT, SingleOutcomeRoller[_T]]: ...
    @overload
    def __call__(
        self, fn: Callable[_ParamsT, MultiOutcomeRoller[_T]], /
    ) -> Callable[_ParamsT, MultiOutcomeRoller[_T]]: ...


class _MultiOutcomeFactoryRoller(MultiOutcomeRoller[_T_co]):
    def __init__(self, expression: MultiOutcomeRoller[_T_co], name: str) -> None:
        self._expression = expression
        self._name = name

    @property
    def operands(self) -> tuple[MultiOutcomeRoller[_T_co], ...]:
        return (self._expression,)

    def h(self) -> H[_T_co]:
        return self._expression.h()

    def metadata(self) -> dict[str, object]:
        return {"kind": "factory", "name": self._name}

    def _roll(self) -> MultiOutcomeRoll[_T_co]:
        result = self._expression.roll()
        return MultiOutcomeRoll(result.outcomes, self, (result,))

    def rolls_with_counts(self) -> Iterator[tuple[tuple[_T_co, ...], int]]:
        yield from self._expression.rolls_with_counts()


class _SingleOutcomeFactoryRoller(SingleOutcomeRoller[_T_co]):
    def __init__(self, expression: SingleOutcomeRoller[_T_co], name: str) -> None:
        self._expression = expression
        self._name = name

    @property
    def operands(self) -> tuple[SingleOutcomeRoller[_T_co], ...]:
        return (self._expression,)

    def h(self) -> H[_T_co]:
        return self._expression.h()

    def metadata(self) -> dict[str, object]:
        return {"kind": "factory", "name": self._name}

    def _roll(self) -> SingleOutcomeRoll[_T_co]:
        result = self._expression.roll()
        return SingleOutcomeRoll(result.outcome, self, (result,))


@overload
def roller_factory(
    fn: Callable[_ParamsT, SingleOutcomeRoller[_T]], /, *, name: str | None = None
) -> Callable[_ParamsT, SingleOutcomeRoller[_T]]: ...
@overload
def roller_factory(
    fn: Callable[_ParamsT, MultiOutcomeRoller[_T]],
    /,
    *,
    name: str | None = None,
) -> Callable[_ParamsT, MultiOutcomeRoller[_T]]: ...
@overload
def roller_factory(
    fn: None = None, /, *, name: str | None = None
) -> _RollerFactoryDecorator: ...
def roller_factory(
    fn: Callable[..., object] | None = None, /, *, name: str | None = None
) -> Any:
    r"""
    Decorates *fn* to wrap its returned [`SingleOutcomeRoller`][dyce.roller.SingleOutcomeRoller] or [`MultiOutcomeRoller`][dyce.roller.MultiOutcomeRoller] so that *name* appears in [`SingleOutcomeRoll`][dyce.roller.SingleOutcomeRoll] traces.

    If not provided, *name* defaults to the *fn*’s `__name__` or its type’s `__name__`.

    Create a factory that accepts a modifier and uses it to produce a named roller:

        >>> from dyce import H
        >>> from dyce.roller import HRoller, SingleOutcomeRoller, roller_factory
        >>> d8 = HRoller(H(8), name="d8")
        >>> @roller_factory
        ... def damage(modifier: int = 0) -> SingleOutcomeRoller[int]:
        ...     return d8 + modifier
        >>> damage_3_roller = damage(modifier=3)

    Now use the roller to produce rolls:

        >>> roll = damage_3_roller.roll()
        >>> roll.roller.metadata()
        {'kind': 'factory', 'name': 'damage'}
        >>> roll.operands[0].roller.metadata()
        {'kind': 'binary', 'operator': 'add'}

    Supply *name* to better distinguish *fn*:

        >>> d20 = HRoller(H(20), name="d20")
        >>> @roller_factory(name="my_game.melee_attack")
        ... def melee_attack(modifier: int = 0) -> SingleOutcomeRoller[int]:
        ...     return d20 + modifier
        >>> melee_attack(modifier=-1).roll().roller.metadata()
        {'kind': 'factory', 'name': 'my_game.melee_attack'}
    """

    def decorate(factory: Callable[..., object]) -> Callable[..., object]:
        resolved_name = (
            name
            if name is not None
            else getattr(factory, "__name__", type(factory).__name__)
        )

        @wraps(factory)
        def wrapped(
            *args: object, **kwargs: object
        ) -> SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any]:
            expression = factory(*args, **kwargs)
            if isinstance(expression, SingleOutcomeRoller):
                return _SingleOutcomeFactoryRoller(expression, resolved_name)
            if isinstance(expression, MultiOutcomeRoller):
                return _MultiOutcomeFactoryRoller(expression, resolved_name)
            raise TypeError(
                "roller factories must return a SingleOutcomeRoller or MultiOutcomeRoller"
            )

        return wrapped

    return decorate if fn is None else decorate(fn)


@overload
def trace(
    callback: Callable[[], MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT]],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[], SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT]],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[], _ResultT],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[SingleOutcomeRoll[_T1]], _ResultT],
    source1: SingleOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[MultiOutcomeRoll[_T1]], _ResultT],
    source1: MultiOutcomeRoller[_T1],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2]], _ResultT],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2]], _ResultT],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2]], _ResultT],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[[MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2]], _ResultT],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT,
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT,
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        _ResultT,
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], SingleOutcomeRoll[_T3]], _ResultT
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: SingleOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        _ResultT,
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], SingleOutcomeRoll[_T2], MultiOutcomeRoll[_T3]], _ResultT
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: SingleOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [SingleOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]], _ResultT
    ],
    source1: SingleOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]],
        SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT],
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        [MultiOutcomeRoll[_T1], MultiOutcomeRoll[_T2], MultiOutcomeRoll[_T3]], _ResultT
    ],
    source1: MultiOutcomeRoller[_T1],
    source2: MultiOutcomeRoller[_T2],
    source3: MultiOutcomeRoller[_T3],
    *,
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[..., MultiOutcomeRoll[_ResultT] | MultiOutcomeRoller[_ResultT]],
    *sources: SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any],
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> MultiOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[
        ..., SingleOutcomeRoll[_ResultT] | SingleOutcomeRoller[_ResultT]
    ],
    *sources: SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any],
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
@overload
def trace(
    callback: Callable[..., _ResultT],
    *sources: SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any],
    name: str | None = ...,
    **state: Any,  # ruff: ignore[any-type]
) -> SingleOutcomeRoll[_ResultT]: ...
def trace(
    callback: Callable[..., object],
    *sources: SingleOutcomeRoller[Any] | MultiOutcomeRoller[Any],
    name: str | None = None,
    **state: Any,
) -> SingleOutcomeRoll[Any] | MultiOutcomeRoll[Any]:
    r"""
    Rolls *sources*, calls *callback* with those rolls and *state*, and returns a named outcome trace.

    A returned roller is rolled, a returned roll is retained, and any other return value is wrapped in a roll from a [`LiteralRoller`][dyce.roller.LiteralRoller].
    The enclosing roll has that roll as its sole operand.
    Supplied *state* is included unchanged in the callback metadata.
    Its values must be JSON-compatible for JSON serialization of the trace.
    *name* defaults to the callback’s `__name__` or its type’s `__name__`.
    Exceptions are reported as [`RollError`][dyce.roller.RollError] with the original exception as their cause.

    Explode a six once, retaining both the initial roll and any additional roll:

        >>> from dyce.roller import (
        ...     HRoller,
        ...     SingleOutcomeRoll,
        ...     SingleOutcomeRoller,
        ...     trace,
        ... )
        >>> d6 = HRoller(H(6), name="d6")
        >>> def explode_once(
        ...     roll: SingleOutcomeRoll[int],
        ... ) -> SingleOutcomeRoll[int] | SingleOutcomeRoller[int]:
        ...     return roll + roll.roller if roll.outcome == 6 else roll
        >>> result = trace(explode_once, d6)
        >>> result.roller.metadata()
        {'kind': 'trace', 'name': 'explode_once', 'state': {}}
        >>> result.operands[0].roller is d6
        True
    """
    call = _TraceCall(
        callback,
        sources,
        name
        if name is not None
        else getattr(callback, "__name__", type(callback).__name__),
        state,
    )
    try:
        return _eval_trace_call(call)
    except RollError as exc:
        exc.path = (call, *exc.path)
        raise
    except Exception as exc:
        raise RollError(str(exc), (call,)) from exc


def _as_roll(
    value: _T | SingleOutcomeRoll[_T] | MultiOutcomeRoll[_T],
) -> SingleOutcomeRoll[_T]:
    if isinstance(value, SingleOutcomeRoll):
        return value
    elif isinstance(value, MultiOutcomeRoll):
        return cast("SingleOutcomeRoll[_T]", cast("MultiOutcomeRoll[Any]", value).sum())
    else:
        return LiteralRoller(value).roll()


def _as_roller(
    value: _T | HableT[_T] | MultiOutcomeRoller[_T] | SingleOutcomeRoller[_T],
) -> SingleOutcomeRoller[_T]:
    if isinstance(value, SingleOutcomeRoller):
        return value
    elif isinstance(value, MultiOutcomeRoller):
        return cast(
            "SingleOutcomeRoller[_T]", cast("MultiOutcomeRoller[Any]", value).sum()
        )
    elif isinstance(value, H):
        return HRoller(value)
    elif isinstance(value, P):
        pool_roller = PRoller(value)
        return cast(
            "SingleOutcomeRoller[_T]",
            cast("MultiOutcomeRoller[Any]", pool_roller).sum(),
        )
    elif isinstance(value, HableT):
        return HableRoller(value)
    else:
        return LiteralRoller(value)


def _binary_roller(
    lhs: object,
    rhs: object,
    operator: _BinaryOperator,
) -> object:
    if isinstance(lhs, (SingleOutcomeRoll, MultiOutcomeRoll)) or isinstance(
        rhs, (SingleOutcomeRoll, MultiOutcomeRoll)
    ):
        return NotImplemented
    return _BinaryRoller(_as_roller(lhs), _as_roller(rhs), operator)


def _eval_trace_call(
    call: _TraceCall,
) -> SingleOutcomeRoll[Any] | MultiOutcomeRoll[Any]:
    if any(
        not isinstance(source, (SingleOutcomeRoller, MultiOutcomeRoller))
        for source in call.sources
    ):
        # TODO(@posita): # ruff: ignore[missing-todo-link] - In theory, we might be able
        # to use a generic type alias to help reduce the number of overloads
        raise TypeError("trace sources must be rollers")
    inputs = tuple(source.roll() for source in call.sources)
    result = call.callback(*inputs, **call.state)
    if isinstance(result, (SingleOutcomeRoller, MultiOutcomeRoller)):
        result = result.roll()
    elif not isinstance(result, (SingleOutcomeRoll, MultiOutcomeRoll)):
        result = LiteralRoller(result).roll()
    if isinstance(result, MultiOutcomeRoll):
        return MultiOutcomeRoll(
            result.outcomes,
            _MultiOutcomeTraceRoller(call, result.roller),
            (result,),
        )
    else:
        return SingleOutcomeRoll(
            result.outcome,
            _SingleOutcomeTraceRoller(call, result.roller),
            (result,),
        )


def _trace_from_root_roll(
    root_roll: MultiOutcomeRoll[object] | SingleOutcomeRoll[object],
) -> dict[str, object]:
    roller_ids: dict[int, str] = {}
    rollers: dict[str, dict[str, object]] = {}
    roll_ids: dict[int, str] = {}
    rolls: dict[str, dict[str, object]] = {}

    def visit_roller(
        roller: MultiOutcomeRoller[object] | SingleOutcomeRoller[object],
    ) -> str:
        key = id(roller)
        if key in roller_ids:
            return roller_ids[key]

        roller_id = f"roller{len(roller_ids)}"
        roller_ids[key] = roller_id
        rollers[roller_id] = {}
        operand_ids = [visit_roller(operand) for operand in roller.operands]
        rollers[roller_id] = {
            **roller.metadata(),
            **({"operands": operand_ids} if operand_ids else {}),
        }
        return roller_id

    def visit_roll(roll: MultiOutcomeRoll[object] | SingleOutcomeRoll[object]) -> str:
        key = id(roll)
        if key in roll_ids:
            return roll_ids[key]

        roll_id = f"roll{len(roll_ids)}"
        roll_ids[key] = roll_id
        rolls[roll_id] = {}
        roller_id = visit_roller(roll.roller)
        operand_ids = [visit_roll(operand) for operand in roll.operands]
        roll_data: dict[str, object]
        if isinstance(roll, MultiOutcomeRoll):
            roll_data = {"outcomes": list(roll.outcomes)}
        else:
            roll_data = {"outcome": roll.outcome}
        rolls[roll_id] = {
            "roller": roller_id,
            **roll_data,
            "operands": operand_ids,
        }
        return roll_id

    root = visit_roll(root_roll)
    return {"root": root, "rollers": rollers, "rolls": rolls}

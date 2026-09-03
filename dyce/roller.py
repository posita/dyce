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

This module is a deliberately narrow prototype.
Its interfaces may change substantially or disappear.
"""

import operator
import warnings
from abc import abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import reduce
from typing import Any, Generic, TypeVar, cast, overload

import optype as ot

from .h import H, HableT
from .lifecycle import ExperimentalWarning, experimental
from .p import P
from .types import GetItemT, getitems, natural_key

__all__ = (
    "HRoller",
    "HableRoller",
    "LiteralRoller",
    "PoolRoll",
    "PoolRoller",
    "Roll",
    "Roller",
)

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")
_CanAddSameT = TypeVar("_CanAddSameT", bound=ot.CanAddSame)


def _sum_outcomes(outcomes: Iterable[_CanAddSameT]) -> _CanAddSameT:
    return reduce(operator.add, outcomes)


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


class Roller(HableT[_T_co]):
    r"""
    A deferred, traceable computation.

    This prototype currently supports pointwise operations.
    """

    __slots__ = ()

    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __add__(
        self: "Roller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "Roller[_ResultT]": ...
    def __add__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _ADD)

    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roller[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "Roller[_ResultT]": ...
    def __sub__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _SUB)

    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roller[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __mul__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _MUL)

    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roller[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __truediv__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _TRUEDIV)

    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roller[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _FLOORDIV)

    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roller[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __mod__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _MOD)

    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roller[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __pow__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _POW)

    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roller[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __lshift__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _LSHIFT)

    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roller[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rshift__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _RSHIFT)

    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __and__(
        self: "Roller[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __and__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _AND)

    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __or__(
        self: "Roller[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __or__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _OR)

    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roller[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roller[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __xor__(self, rhs: object) -> "Roller[object]":
        return _BinaryRoller(self, _as_roller(rhs), _XOR)

    @overload
    def __radd__(
        self: "Roller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __radd__(
        self: "Roller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roller[_ResultT]": ...
    def __radd__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _ADD)

    @overload
    def __rsub__(
        self: "Roller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rsub__(
        self: "Roller[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roller[_ResultT]": ...
    def __rsub__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _SUB)

    @overload
    def __rmul__(
        self: "Roller[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rmul__(
        self: "Roller[ot.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rmul__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _MUL)

    @overload
    def __rtruediv__(
        self: "Roller[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "Roller[ot.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _TRUEDIV)

    @overload
    def __rfloordiv__(
        self: "Roller[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "Roller[ot.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _FLOORDIV)

    @overload
    def __rmod__(
        self: "Roller[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rmod__(
        self: "Roller[ot.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rmod__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _MOD)

    @overload
    def __rpow__(
        self: "Roller[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rpow__(
        self: "Roller[ot.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rpow__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _POW)

    @overload
    def __rlshift__(
        self: "Roller[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "Roller[ot.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _LSHIFT)

    @overload
    def __rrshift__(
        self: "Roller[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "Roller[ot.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _RSHIFT)

    @overload
    def __rand__(
        self: "Roller[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rand__(
        self: "Roller[ot.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rand__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _AND)

    @overload
    def __ror__(
        self: "Roller[ot.CanROr[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __ror__(
        self: "Roller[ot.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __ror__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _OR)

    @overload
    def __rxor__(
        self: "Roller[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: "HableT[_OtherT]",
    ) -> "Roller[_ResultT]": ...
    @overload
    def __rxor__(
        self: "Roller[ot.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "Roller[_ResultT]": ...
    def __rxor__(self, lhs: object) -> "Roller[object]":
        return _BinaryRoller(_as_roller(lhs), self, _XOR)

    def __neg__(self: "Roller[ot.CanNeg[_ResultT]]") -> "Roller[_ResultT]":
        return cast("Roller[_ResultT]", _UnaryRoller(self, _NEG))

    def __pos__(self: "Roller[ot.CanPos[_ResultT]]") -> "Roller[_ResultT]":
        return cast("Roller[_ResultT]", _UnaryRoller(self, _POS))

    def __abs__(self: "Roller[ot.CanAbs[_ResultT]]") -> "Roller[_ResultT]":
        return cast("Roller[_ResultT]", _UnaryRoller(self, _ABS))

    def __invert__(self: "Roller[ot.CanInvert[_ResultT]]") -> "Roller[_ResultT]":
        return cast("Roller[_ResultT]", _UnaryRoller(self, _INVERT))

    @property
    def operands(self) -> tuple["PoolRoller[object] | Roller[object]", ...]:
        r"""The immediate rollers consumed by this roller."""
        return ()

    @abstractmethod
    def provenance(self) -> dict[str, object]:
        r"""
        Returns JSON-compatible metadata describing this roller.

        The serializer supplies the reserved `operands` field when appropriate.
        """

    @abstractmethod
    def roll(self) -> "Roll[_T_co]":
        r"""Realizes this computation and returns its outcome with provenance."""


class HRoller(Roller[_T_co]):
    r"""
    A deferred, traceable computation backed by an [`H`][dyce.H].

    This prototype currently supports pointwise operations.
    """

    __slots__ = ("_h", "_name")

    @experimental
    def __init__(self, h: H[_T_co], *, name: str | None = None) -> None:
        self._h = h
        self._name = name

    @property
    def name(self) -> str | None:
        r"""The source name supplied when this roller was created, if any."""
        return self._name

    def h(self) -> H[_T_co]:
        r"""Returns the distribution represented by this roller."""
        return self._h

    def provenance(self) -> dict[str, object]:
        return {
            "kind": "source",
            "name": self._name if self._name is not None else str(self._h),
        }

    def roll(self) -> "Roll[_T_co]":
        r"""Realizes this computation and returns its outcome with provenance."""
        return Roll(self._h.roll(), self)


class HableRoller(Roller[_T_co]):
    r"""A deferred, traceable source backed by a [`HableT`][dyce.HableT]."""

    __slots__ = ("_hable",)

    def __init__(self, hable: HableT[_T_co]) -> None:
        self._hable = hable

    @property
    def hable(self) -> HableT[_T_co]:
        r"""The source supplying this roller’s distribution."""
        return self._hable

    def h(self) -> H[_T_co]:
        return self._hable.h()

    def provenance(self) -> dict[str, object]:
        return {"kind": "source", "name": str(self._hable)}

    def roll(self) -> "Roll[_T_co]":
        return Roll(self.h().roll(), self)


class LiteralRoller(Roller[_T]):
    r"""A deterministic, traceable source for a literal outcome."""

    __slots__ = ("_value",)

    def __init__(self, value: _T) -> None:
        self._value = value

    @property
    def value(self) -> _T:
        r"""The outcome produced by this roller."""
        return self._value

    def h(self) -> H[_T]:
        return H({self._value: 1})

    def provenance(self) -> dict[str, object]:
        return {"kind": "literal", "value": self._value}

    def roll(self) -> "Roll[_T]":
        return Roll(self._value, self)


class PoolRoller(Generic[_T_co]):
    r"""A deferred, traceable pool computation backed by a [`P`][dyce.P]."""

    __slots__ = ("_die_rollers", "_name", "_p")

    @experimental
    def __init__(self, p: P[_T_co], *, name: str | None = None) -> None:
        self._p = p
        self._name = name
        die_rollers_by_h: dict[H[_T_co], HRoller[_T_co]] = {}
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            self._die_rollers = tuple(
                die_rollers_by_h.setdefault(h, HRoller(h)) for h in p
            )

    @property
    def name(self) -> str | None:
        r"""The source name supplied when this pool roller was created, if any."""
        return self._name

    @property
    def operands(self) -> tuple["PoolRoller[object] | Roller[object]", ...]:
        r"""The immediate rollers consumed by this pool roller."""
        return cast(
            "tuple[PoolRoller[object] | Roller[object], ...]", self._die_rollers
        )

    @property
    def p(self) -> P[_T_co]:
        r"""The pool supplying this roller's outcomes."""
        return self._p

    def at(
        self: "PoolRoller[_CanAddSameT]", which: GetItemT, *more: GetItemT
    ) -> Roller[_CanAddSameT]:
        r"""Returns a scalar roller summing the outcomes at the selected positions."""
        return self.select(which, *more).sum()

    def provenance(self) -> dict[str, object]:
        r"""Returns JSON-compatible metadata describing this pool roller."""
        return {
            "kind": "pool-source",
            "name": self._name if self._name is not None else str(self._p),
        }

    def roll(self) -> "PoolRoll[_T_co]":
        r"""Realizes this pool computation and returns its outcomes with provenance."""
        rolls = [roller.roll() for roller in self._die_rollers]
        try:
            rolls.sort(
                key=cast("Callable[[Roll[_T_co]], Any]", lambda roll: roll.outcome)
            )
        except TypeError:
            rolls.sort(key=lambda roll: natural_key(roll.outcome))
        operands = cast("tuple[PoolRoll[object] | Roll[object], ...]", tuple(rolls))
        return PoolRoll(tuple(rolls), self, operands)

    def select(self, which: GetItemT, *more: GetItemT) -> "PoolRoller[_T_co]":
        r"""Returns a pool roller selecting the specified sorted positions."""
        positions = tuple(getitems(tuple(range(self._size())), (which, *more)))
        absolute_positions = self._absolute_positions()
        selected_absolute_positions = tuple(
            absolute_positions[position] for position in positions
        )
        return _SelectedPoolRoller(self, positions, selected_absolute_positions)

    def sum(
        self: "PoolRoller[_CanAddSameT]",
    ) -> Roller[_CanAddSameT]:
        r"""Returns a scalar roller summing every outcome in this pool roller."""
        return _PoolSumRoller(self, self._sum_h)

    def _absolute_positions(self) -> tuple[int, ...]:
        return tuple(range(len(self._p)))

    def _size(self) -> int:
        return len(self._p)

    def _sum_h(self: "PoolRoller[_CanAddSameT]") -> H[_CanAddSameT]:
        return cast("H[_CanAddSameT]", self._p.h())  # type: ignore[redundant-cast]


class _SelectedPoolRoller(PoolRoller[_T_co]):
    __slots__ = ("_parent", "_positions", "_root_positions")

    def __init__(
        self,
        parent: PoolRoller[_T_co],
        positions: tuple[int, ...],
        root_positions: tuple[int, ...],
    ) -> None:
        self._parent = parent
        self._positions = positions
        self._root_positions = root_positions

    @property
    def name(self) -> None:
        return None

    @property
    def operands(self) -> tuple["PoolRoller[object] | Roller[object]", ...]:
        return (cast("PoolRoller[object]", self._parent),)

    @property
    def p(self) -> P[_T_co]:
        return self._parent.p

    def provenance(self) -> dict[str, object]:
        return {"kind": "pool-selection", "positions": list(self._positions)}

    def roll(self) -> "PoolRoll[_T_co]":
        parent_roll = self._parent.roll()
        rolls = tuple(parent_roll.rolls[position] for position in self._positions)
        operands = (cast("PoolRoll[object]", parent_roll),)
        return PoolRoll(rolls, self, operands)

    def _absolute_positions(self) -> tuple[int, ...]:
        return self._root_positions

    def _size(self) -> int:
        return len(self._positions)

    def _sum_h(
        self: "_SelectedPoolRoller[_CanAddSameT]",
    ) -> H[_CanAddSameT]:
        if not self._root_positions:
            return cast("H[_CanAddSameT]", H({}))
        return H.from_counts(
            (
                (_sum_outcomes(roll), count)
                for roll, count in self.p.rolls_with_counts(*self._root_positions)
            )
        )


@dataclass(frozen=True, slots=True, eq=False)
class Roll(Generic[_T_co]):
    r"""
    An immutable realized outcome with provenance.

    Roll identity is significant.
    Reusing one `Roll` in multiple operands represents one event with fan-out, while calling [`Roller.roll`][dyce.roller.Roller.roll] repeatedly represents independent events.
    """

    outcome: _T_co
    roller: Roller[_T_co] = field(repr=False)
    operands: tuple["PoolRoll[object] | Roll[object]", ...] = field(
        default=(), repr=False
    )

    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __add__(
        self: "Roll[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "Roll[_ResultT]": ...
    def __add__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _ADD)

    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __sub__(
        self: "Roll[ot.CanSub[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "Roll[_ResultT]": ...
    def __sub__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _SUB)

    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __mul__(
        self: "Roll[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __mul__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _MUL)

    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __truediv__(
        self: "Roll[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __truediv__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _TRUEDIV)

    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "Roll[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _FLOORDIV)

    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __mod__(
        self: "Roll[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __mod__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _MOD)

    @overload
    def __pow__(
        self: "Roll[ot.CanPow2[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __pow__(
        self: "Roll[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __pow__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _POW)

    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __lshift__(
        self: "Roll[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __lshift__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _LSHIFT)

    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __rshift__(
        self: "Roll[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __rshift__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _RSHIFT)

    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __and__(
        self: "Roll[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __and__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _AND)

    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __or__(
        self: "Roll[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __or__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _OR)

    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]",
        rhs: "Roll[_OtherT]",
    ) -> "Roll[_ResultT]": ...
    @overload
    def __xor__(
        self: "Roll[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "Roll[_ResultT]": ...
    def __xor__(self, rhs: object) -> "Roll[object]":
        return self._binary_operator(rhs, _XOR)

    def __radd__(
        self: "Roll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _ADD))

    def __rsub__(
        self: "Roll[ot.CanRSub[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _SUB))

    def __rmul__(
        self: "Roll[ot.CanRMul[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _MUL))

    def __rtruediv__(
        self: "Roll[ot.CanRTruediv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _TRUEDIV))

    def __rfloordiv__(
        self: "Roll[ot.CanRFloordiv[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _FLOORDIV))

    def __rmod__(
        self: "Roll[ot.CanRMod[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _MOD))

    def __rpow__(
        self: "Roll[ot.CanRPow[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _POW))

    def __rlshift__(
        self: "Roll[ot.CanRLshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _LSHIFT))

    def __rrshift__(
        self: "Roll[ot.CanRRshift[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _RSHIFT))

    def __rand__(
        self: "Roll[ot.CanRAnd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _AND))

    def __ror__(
        self: "Roll[ot.CanROr[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _OR))

    def __rxor__(
        self: "Roll[ot.CanRXor[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._reflected_binary_operator(lhs, _XOR))

    def __neg__(self: "Roll[ot.CanNeg[_ResultT]]") -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._unary_operator(_NEG))

    def __pos__(self: "Roll[ot.CanPos[_ResultT]]") -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._unary_operator(_POS))

    def __abs__(self: "Roll[ot.CanAbs[_ResultT]]") -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._unary_operator(_ABS))

    def __invert__(self: "Roll[ot.CanInvert[_ResultT]]") -> "Roll[_ResultT]":
        return cast("Roll[_ResultT]", self._unary_operator(_INVERT))

    def to_dict(self) -> dict[str, object]:
        r"""
        Returns normalized provenance composed of JSON-compatible containers.

        Outcomes and literal values must themselves be JSON-compatible for the complete result to be serializable as JSON.
        """
        return _provenance_to_dict(cast("Roll[object]", self))

    def _binary_operator(
        self, rhs: object, operator: _BinaryOperator
    ) -> "Roll[object]":
        rhs_roll = _as_roll(rhs)
        roller: Roller[object] = _BinaryRoller(self.roller, rhs_roll.roller, operator)
        outcome = operator(self.outcome, rhs_roll.outcome)
        return Roll(outcome, roller, (self, rhs_roll))

    def _reflected_binary_operator(
        self, lhs: object, operator: _BinaryOperator
    ) -> "Roll[object]":
        lhs_roll = _as_roll(lhs)
        roller: Roller[object] = _BinaryRoller(lhs_roll.roller, self.roller, operator)
        outcome = operator(lhs_roll.outcome, self.outcome)
        return Roll(outcome, roller, (lhs_roll, self))

    def _unary_operator(self, operator: _UnaryOperator) -> "Roll[object]":
        roller: Roller[object] = _UnaryRoller(self.roller, operator)
        outcome = operator(self.outcome)
        return Roll(outcome, roller, (self,))


@dataclass(frozen=True, slots=True, eq=False)
class PoolRoll(Generic[_T_co]):
    r"""An immutable realized collection of outcomes with provenance."""

    rolls: tuple[Roll[_T_co], ...]
    roller: PoolRoller[_T_co] = field(repr=False)
    operands: tuple["PoolRoll[object] | Roll[object]", ...] = field(
        default=(), repr=False
    )

    @property
    def outcomes(self) -> tuple[_T_co, ...]:
        r"""The outcomes contained in this pool roll."""
        return tuple(roll.outcome for roll in self.rolls)

    def sum(self: "PoolRoll[_CanAddSameT]") -> Roll[_CanAddSameT]:
        r"""Returns the sum of this pool roll's outcomes with provenance."""
        roller = self.roller.sum()
        outcome = _sum_outcomes(self.outcomes)
        return Roll(outcome, roller, (cast("PoolRoll[object]", self),))

    def to_dict(self) -> dict[str, object]:
        r"""
        Returns normalized provenance composed of JSON-compatible containers.

        Outcomes and literal values must themselves be JSON-compatible for the complete result to be serializable as JSON.
        """
        return _provenance_to_dict(cast("PoolRoll[object]", self))


class _BinaryRoller(Roller[_ResultT]):
    __slots__ = ("_left", "_operator", "_right")

    def __init__(
        self,
        left: Roller[object],
        right: Roller[object],
        operator: _BinaryOperator,
    ) -> None:
        self._left = left
        self._right = right
        self._operator = operator

    @property
    def operands(self) -> tuple[Roller[object], ...]:
        return (self._left, self._right)

    def h(self) -> H[_ResultT]:
        return cast("H[_ResultT]", self._operator(self._left.h(), self._right.h()))

    def provenance(self) -> dict[str, object]:
        return {"kind": "binary", "operator": self._operator.name}

    def roll(self) -> Roll[_ResultT]:
        left_roll = self._left.roll()
        right_roll = self._right.roll()
        outcome = self._operator(left_roll.outcome, right_roll.outcome)
        return Roll(cast("_ResultT", outcome), self, (left_roll, right_roll))


class _UnaryRoller(Roller[_ResultT]):
    __slots__ = ("_operand", "_operator")

    def __init__(self, operand: Roller[object], operator: _UnaryOperator) -> None:
        self._operand = operand
        self._operator = operator

    @property
    def operands(self) -> tuple[Roller[object], ...]:
        return (self._operand,)

    def h(self) -> H[_ResultT]:
        return cast("H[_ResultT]", self._operator(self._operand.h()))

    def provenance(self) -> dict[str, object]:
        return {"kind": "unary", "operator": self._operator.name}

    def roll(self) -> Roll[_ResultT]:
        operand_roll = self._operand.roll()
        outcome = self._operator(operand_roll.outcome)
        return Roll(cast("_ResultT", outcome), self, (operand_roll,))


class _PoolSumRoller(Roller[_CanAddSameT]):
    __slots__ = ("_h", "_pool_roller")

    def __init__(
        self,
        pool_roller: PoolRoller[_CanAddSameT],
        h: Callable[[], H[_CanAddSameT]],
    ) -> None:
        self._pool_roller = pool_roller
        self._h = h

    @property
    def operands(self) -> tuple["PoolRoller[object] | Roller[object]", ...]:
        return (cast("PoolRoller[object]", self._pool_roller),)

    def h(self) -> H[_CanAddSameT]:
        return self._h()

    def provenance(self) -> dict[str, object]:
        return {"kind": "pool-sum"}

    def roll(self) -> Roll[_CanAddSameT]:
        pool_roll = self._pool_roller.roll()
        outcome = _sum_outcomes(pool_roll.outcomes)
        return Roll(outcome, self, (cast("PoolRoll[object]", pool_roll),))


def _provenance_to_dict(
    root_roll: PoolRoll[object] | Roll[object],
) -> dict[str, object]:
    definition_ids: dict[int, str] = {}
    definitions: dict[str, dict[str, object]] = {}
    event_ids: dict[int, str] = {}
    events: dict[str, dict[str, object]] = {}

    def visit_definition(roller: PoolRoller[object] | Roller[object]) -> str:
        key = id(roller)
        if key in definition_ids:
            return definition_ids[key]

        definition_id = f"d{len(definition_ids)}"
        definition_ids[key] = definition_id
        definitions[definition_id] = {}
        operand_ids = [visit_definition(operand) for operand in roller.operands]
        definitions[definition_id] = {
            **roller.provenance(),
            **({"operands": operand_ids} if operand_ids else {}),
        }
        return definition_id

    def visit_event(roll: PoolRoll[object] | Roll[object]) -> str:
        key = id(roll)
        if key in event_ids:
            return event_ids[key]

        event_id = f"e{len(event_ids)}"
        event_ids[key] = event_id
        events[event_id] = {}
        definition_id = visit_definition(roll.roller)
        operand_ids = [visit_event(operand) for operand in roll.operands]
        event_data: dict[str, object]
        if isinstance(roll, PoolRoll):
            event_data = {"outcomes": list(roll.outcomes)}
        else:
            event_data = {"outcome": roll.outcome}
        events[event_id] = {
            "definition": definition_id,
            **event_data,
            "operands": operand_ids,
        }
        return event_id

    root = visit_event(root_roll)
    return {"root": root, "definitions": definitions, "events": events}


def _as_roller(value: _T | HableT[_T] | Roller[_T]) -> Roller[_T]:
    if isinstance(value, Roller):
        return value
    if isinstance(value, H):
        return HRoller(value)
    if isinstance(value, HableT):
        return HableRoller(value)
    return LiteralRoller(value)


def _as_roll(value: _T | Roll[_T]) -> Roll[_T]:
    if isinstance(value, Roll):
        return value
    return LiteralRoller(value).roll()

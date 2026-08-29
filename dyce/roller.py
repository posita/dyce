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
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar, cast, overload

if TYPE_CHECKING:
    from collections.abc import Callable

    import optype as ot

from .h import H, HableT
from .lifecycle import experimental

__all__ = ("HRoller", "Roll")

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")
_ADD = cast("Callable[[object, object], object]", operator.add)


class HRoller(HableT[_T_co]):
    r"""
    A deferred, traceable computation backed by an [`H`][dyce.H].

    This prototype currently supports only addition.
    """

    __slots__ = ("_h", "_name")

    @experimental
    def __init__(self, h: H[_T_co], name: str | None = None) -> None:
        self._h = h
        self._name = name

    def h(self) -> H[_T_co]:
        r"""Returns the distribution represented by this roller."""
        return self._h

    @overload
    def __add__(
        self: "HRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "HRoller[_OtherT]",
    ) -> "HRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "HRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: "H[_OtherT]",
    ) -> "HRoller[_ResultT]": ...
    @overload
    def __add__(
        self: "HRoller[ot.CanAdd[_OtherT, _ResultT]]",
        rhs: _OtherT,
    ) -> "HRoller[_ResultT]": ...
    def __add__(self, rhs: object) -> "HRoller[object]":
        return _BinaryAddHRoller(self, _as_hroller(rhs))

    def __radd__(
        self: "HRoller[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "HRoller[_ResultT]":
        return cast("HRoller[_ResultT]", _BinaryAddHRoller(_as_hroller(lhs), self))

    @property
    def name(self) -> str | None:
        r"""The source name supplied when this roller was created, if any."""
        return self._name

    def roll(self) -> "Roll[_T_co]":
        r"""Realizes this computation and returns its outcome with provenance."""
        return Roll(self._h.roll(), self)

    def _definition_record(self, operand_ids: list[str]) -> dict[str, object]:
        assert not operand_ids
        return {
            "kind": "source",
            "name": self._name if self._name is not None else str(self._h),
        }

    def _operands(self) -> tuple["HRoller[object]", ...]:
        return ()


@dataclass(frozen=True, slots=True, eq=False)
class Roll(Generic[_T_co]):
    r"""
    An immutable realized outcome with provenance.

    Roll identity is significant.
    Reusing one `Roll` in multiple operands represents one event with fan-out, while calling [`HRoller.roll`][dyce.roller.HRoller.roll] repeatedly represents independent events.
    """

    outcome: _T_co
    roller: HRoller[_T_co] = field(repr=False)
    operands: tuple["Roll[object]", ...] = field(default=(), repr=False)

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
        rhs_roll = _as_roll(rhs)
        roller: HRoller[object] = _BinaryAddHRoller(self.roller, rhs_roll.roller)
        outcome = _ADD(self.outcome, rhs_roll.outcome)
        return Roll(outcome, roller, (self, rhs_roll))

    def __radd__(
        self: "Roll[ot.CanRAdd[_OtherT, _ResultT]]",
        lhs: _OtherT,
    ) -> "Roll[_ResultT]":
        lhs_roll = _as_roll(lhs)
        roller: HRoller[object] = _BinaryAddHRoller(lhs_roll.roller, self.roller)
        outcome = _ADD(lhs_roll.outcome, self.outcome)
        return cast("Roll[_ResultT]", Roll(outcome, roller, (lhs_roll, self)))

    def to_dict(self) -> dict[str, object]:
        r"""
        Returns normalized provenance composed of JSON-compatible containers.

        Outcomes and literal values must themselves be JSON-compatible for the complete result to be serializable as JSON.
        """
        definition_ids: dict[int, str] = {}
        definitions: dict[str, dict[str, object]] = {}
        event_ids: dict[int, str] = {}
        events: dict[str, dict[str, object]] = {}

        def visit_definition(roller: HRoller[object]) -> str:
            key = id(roller)
            if key in definition_ids:
                return definition_ids[key]

            definition_id = f"d{len(definition_ids)}"
            definition_ids[key] = definition_id
            definitions[definition_id] = {}
            operand_ids = [
                visit_definition(operand)
                for operand in roller._operands()  # ruff: ignore[private-member-access]
            ]
            definitions[definition_id] = roller._definition_record(  # ruff: ignore[private-member-access]
                operand_ids
            )
            return definition_id

        def visit_event(roll: Roll[object]) -> str:
            key = id(roll)
            if key in event_ids:
                return event_ids[key]

            event_id = f"e{len(event_ids)}"
            event_ids[key] = event_id
            events[event_id] = {}
            definition_id = visit_definition(roll.roller)
            operand_ids = [visit_event(operand) for operand in roll.operands]
            events[event_id] = {
                "definition": definition_id,
                "outcome": roll.outcome,
                "operands": operand_ids,
            }
            return event_id

        root = visit_event(cast("Roll[object]", self))
        return {"root": root, "definitions": definitions, "events": events}


class _BinaryAddHRoller(HRoller[_ResultT]):
    __slots__ = ("_left", "_right")

    def __init__(
        self,
        left: HRoller[object],
        right: HRoller[object],
    ) -> None:
        self._left = left
        self._right = right
        self._name = None

    def h(self) -> H[_ResultT]:
        return cast("H[_ResultT]", _ADD(self._left.h(), self._right.h()))

    def roll(self) -> Roll[_ResultT]:
        left_roll = self._left.roll()
        right_roll = self._right.roll()
        outcome = _ADD(left_roll.outcome, right_roll.outcome)
        return Roll(cast("_ResultT", outcome), self, (left_roll, right_roll))

    def _definition_record(self, operand_ids: list[str]) -> dict[str, object]:
        assert len(operand_ids) == 2
        return {"kind": "binary", "operator": "add", "operands": operand_ids}

    def _operands(self) -> tuple[HRoller[object], ...]:
        return (self._left, self._right)


class _LiteralHRoller(HRoller[_T]):
    __slots__ = ("_value",)

    def __init__(self, value: _T) -> None:
        self._value = value
        self._h = H({value: 1})
        self._name = None

    def roll(self) -> Roll[_T]:
        return Roll(self._value, self)

    def _definition_record(self, operand_ids: list[str]) -> dict[str, object]:
        assert not operand_ids
        return {"kind": "literal", "value": self._value}


def _as_hroller(value: _T | H[_T] | HRoller[_T]) -> HRoller[_T]:
    if isinstance(value, HRoller):
        return value
    if isinstance(value, H):
        return HRoller(value)
    return _LiteralHRoller(value)


def _as_roll(value: _T | Roll[_T]) -> Roll[_T]:
    if isinstance(value, Roll):
        return value
    return _LiteralHRoller(value).roll()

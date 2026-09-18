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

import json
import operator
import random
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any, Literal, Never, assert_type, cast
from unittest.mock import Mock, patch

import pytest

from dyce import H, HableT, P, rng
from dyce.roller import (
    HableRoller,
    HRoller,
    LiteralRoller,
    PRoller,
    Roll,
    Roller,
    RollerPool,
    RollError,
    SingleOutcomeRoll,
    SingleOutcomeRoller,
    _FactoryRoller,
    _SingleOutcomeFactoryRoller,
    roller_factory,
    trace,
)
from dyce.types import DYCE_IS_BEARIFIED, BeartypeCallHintViolation

__all__ = ()

_BINARY_OPERATOR_CASES: tuple[tuple[Callable[[Any, Any], Any], str, int, int], ...] = (
    (operator.add, "add", 8, 3),
    (operator.sub, "sub", 8, 3),
    (operator.mul, "mul", 8, 3),
    (operator.truediv, "truediv", 8, 2),
    (operator.floordiv, "floordiv", 8, 3),
    (operator.mod, "mod", 8, 3),
    (operator.pow, "pow", 3, 2),
    (operator.lshift, "lshift", 3, 2),
    (operator.rshift, "rshift", 12, 2),
    (operator.and_, "and", 6, 3),
    (operator.or_, "or", 4, 3),
    (operator.xor, "xor", 6, 3),
)
_COMPARISON_CASES: tuple[tuple[Callable[[Any, Any], bool], str, int, int], ...] = (
    (operator.lt, "lt", 2, 3),
    (operator.le, "le", 2, 2),
    (operator.eq, "eq", 2, 2),
    (operator.ne, "ne", 2, 3),
    (operator.ge, "ge", 3, 3),
    (operator.gt, "gt", 3, 2),
)
_UNARY_OPERATOR_CASES: tuple[tuple[Callable[[Any], Any], str, int], ...] = (
    (operator.neg, "neg", 3),
    (operator.pos, "pos", -3),
    (operator.abs, "abs", -3),
    (operator.invert, "invert", 3),
)


def _roll_operands(roll: Roll[object]) -> tuple[Roll[object], ...]:
    relationships = roll._trace_relationships()  # ruff: ignore[private-member-access]
    operands = relationships["operands"]
    assert isinstance(operands, tuple)
    return operands


def _roller_operands(roller: Roller[object]) -> tuple[Roller[object], ...]:
    relationships = roller._trace_relationships()  # ruff: ignore[private-member-access]
    operands = relationships["operands"]
    assert isinstance(operands, tuple)
    return operands


@dataclass(frozen=True)
class _AddableOutcome:
    value: int

    def __add__(self, other: "_AddableOutcome") -> "_AddableOutcome":
        return _AddableOutcome(self.value + other.value)


class _Hable(HableT[int]):
    def __init__(self, h: H[int]) -> None:
        self._h = h

    def h(self) -> H[int]:
        return self._h


@dataclass(frozen=True)
class _PowerOutcome:
    value: int

    # Needed to ensure that _PowerOutcome satisfies CanAddSame, so it can be used with
    # sum() methods from either Roller or Roll
    def __add__(self, rhs: "_PowerOutcome") -> "_PowerOutcome":
        return _PowerOutcome(self.value + rhs.value)

    def __pow__(self, rhs: int) -> "_PowerOutcome":
        return _PowerOutcome(self.value**rhs)

    def __rpow__(self, lhs: int) -> "_PowerOutcome":
        return _PowerOutcome(lhs**self.value)


class TestRollError:
    def test_parent_failure(self) -> None:
        roller = LiteralRoller(1) / 0

        with pytest.raises(RollError) as caught:
            roller.roll()
        assert caught.value.path == (roller,)

    def test_sibling_failure(self) -> None:
        damage = PRoller(P(), name="damage")

        @roller_factory
        def attack() -> SingleOutcomeRoller[int]:
            return LiteralRoller(20) + damage

        roller = attack()
        assert isinstance(roller, _SingleOutcomeFactoryRoller)

        with pytest.raises(RollError) as caught:
            roller.roll()
        assert caught.value.path[0] is roller
        assert [entry.metadata()["kind"] for entry in caught.value.path] == [
            "dyce.factory",
            "dyce.binary",
            "dyce.pool-sum",
            "dyce.pool-source",
        ]
        assert caught.value.path[-1] is damage

    def test_cause_preserved(self) -> None:
        failure = RuntimeError("source failure")
        roller = HRoller(H(6)) + 1

        with (
            patch.object(H, "roll", side_effect=failure),
            pytest.raises(RollError) as caught,
        ):
            roller.roll()
        assert caught.value.__cause__ is failure

    def test_message_formatting(self) -> None:
        source = PRoller(P(), name="damage")
        parent = source.sum()
        grandparent = RollerPool(parent)

        with pytest.raises(RollError) as caught:
            grandparent.roll()
        assert str(caught.value) == (
            "no outcomes from an empty pool\nRoller path:\n"
            "  {'kind': 'dyce.pool'}\n"
            "  → {'kind': 'dyce.pool-sum'}\n"
            "  → {'kind': 'dyce.pool-source', 'name': 'damage'}"
        )

    def test_base_exception_propagates(self) -> None:
        with (
            patch.object(H, "roll", side_effect=KeyboardInterrupt),
            pytest.raises(KeyboardInterrupt),
        ):
            HRoller(H(6)).roll()


class TestTrace:
    def test_callback_called_with_rolls_from_source_rollers_and_state(self) -> None:
        single = LiteralRoller(3)
        multi = PRoller(P(H({2: 1}), H({4: 1})))
        token = object()
        callback = Mock(return_value=0)

        trace(callback, single, multi, token=token)

        callback.assert_called_once()
        args, kwargs = callback.call_args
        assert isinstance(args[0], SingleOutcomeRoll)
        # TODO(@posita): <https://github.com/zubanls/zuban/issues/561>
        assert args[0].outcome == 3  # zuban: ignore[comparison-overlap]
        assert args[0].roller is single  # zuban: ignore[comparison-overlap]
        assert isinstance(args[1], Roll)
        assert args[1].outcomes == (2, 4)  # zuban: ignore[comparison-overlap]
        assert args[1].roller is multi
        assert kwargs == {"token": token}

    def test_callback_returns_single_roll(self) -> None:
        roll = LiteralRoller(4).roll()

        def callback() -> SingleOutcomeRoll[int]:
            return roll

        result = trace(callback)
        result_trace = result.trace()
        rolls = result_trace["rolls"]

        assert_type(result, Roll[int])
        assert result.outcomes == (4,)
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }
        assert rolls["roll1"]["outcome"] == roll.outcome

    def test_callback_returns_roll_with_multiple_outcomes(self) -> None:
        returned = PRoller(P(H({2: 1}), H({3: 1}))).roll()

        def callback() -> Roll[int]:
            return returned

        result = trace(callback)
        result_trace = result.trace()
        rolls = result_trace["rolls"]

        assert_type(result, Roll[int])
        assert result.outcomes == (2, 3)
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }
        assert rolls["roll1"]["outcomes"] == list(returned.outcomes)

    def test_callback_returns_single_roller(self) -> None:
        def callback() -> SingleOutcomeRoller[int]:
            return LiteralRoller(8)

        result = trace(callback)
        result_trace = result.trace()
        rolls = result_trace["rolls"]

        assert_type(result, Roll[int])
        assert result.outcomes == (8,)
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }
        assert rolls["roll1"]["outcome"] == 8

    def test_callback_returns_roller_with_multiple_outcomes(self) -> None:
        def callback() -> Roller[int]:
            return PRoller(P(H({2: 1}), H({3: 1})))

        result = trace(callback)
        result_trace = result.trace()
        rolls = result_trace["rolls"]

        assert_type(result, Roll[int])
        assert result.outcomes == (2, 3)
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }
        assert rolls["roll1"]["outcomes"] == [2, 3]

    def test_callback_returns_literal_string(self) -> None:
        source = LiteralRoller(3)

        def callback(roll: SingleOutcomeRoll[int]) -> str:
            return "hit" if roll.outcome == 3 else "miss"

        result = trace(callback, source)
        result_trace = result.trace()
        rolls = result_trace["rolls"]

        assert_type(result, Roll[str])
        assert result.outcomes == ("hit",)
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": ["roll1"],
            "result": "roll2",
        }
        assert rolls["roll1"]["outcome"] == 3
        assert rolls["roll2"]["outcome"] == "hit"

    @pytest.mark.skipif(DYCE_IS_BEARIFIED, reason="we are ***BEARIFIED***")
    def test_nonroller_source_raises(self) -> None:
        with pytest.raises(RollError) as caught:
            trace(Mock(), cast("Any", H(6)))

        assert isinstance(caught.value.__cause__, TypeError)
        assert str(caught.value.__cause__) == "trace sources must be rollers"

    @pytest.mark.skipif(not DYCE_IS_BEARIFIED, reason="we are ***NOT*** bearified")
    def test_nonroller_source_triggers_beartype_violation(self) -> None:
        with pytest.raises(BeartypeCallHintViolation):
            trace(Mock(), cast("Any", H(6)))

    def test_trace_separates_argument_from_unrelated_result(self) -> None:
        def callback(_roll: SingleOutcomeRoll[int]) -> SingleOutcomeRoller[int]:
            return LiteralRoller(3)

        result = trace(callback, LiteralRoller(2))
        rolls = result.trace()["rolls"]

        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": ["roll1"],
            "result": "roll2",
        }
        assert rolls["roll1"]["outcome"] == 2
        assert rolls["roll2"]["outcome"] == 3

    def test_trace_reuses_id_when_argument_is_result(self) -> None:
        def callback(roll: SingleOutcomeRoll[int]) -> SingleOutcomeRoll[int]:
            return roll

        result = trace(callback, LiteralRoller(2))
        rolls = result.trace()["rolls"]

        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": ["roll1"],
            "result": "roll1",
        }

    def test_trace_records_argument_reached_through_result(self) -> None:
        def callback(roll: SingleOutcomeRoll[int]) -> SingleOutcomeRoll[int]:
            return 1 + roll

        result = trace(callback, HRoller(H(6), name="d6"))
        rolls = result.trace()["rolls"]

        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"] == {
            "arguments": ["roll1"],
            "result": "roll2",
        }
        assert rolls["roll2"]["relationships"]["operands"] == ["roll3", "roll1"]
        assert rolls["roll3"]["outcome"] == 1
        assert rolls["roll0"]["outcomes"] == [1 + rolls["roll1"]["outcome"]]

    def test_implicit_name_uses_callback_name(self) -> None:
        def callback() -> int:
            return 4

        result = trace(callback)

        assert result.roller.metadata() == {
            "kind": "dyce.trace",
            "name": "callback",
            "state": {},
        }

    @pytest.mark.parametrize("name", ["trace.custom", ""])
    def test_explicit_name_preserved(self, name: str) -> None:
        def callback() -> int:
            return 4

        result = trace(callback, name=name)

        assert result.roller.metadata() == {
            "kind": "dyce.trace",
            "name": name,
            "state": {},
        }

    def test_state_metadata(self) -> None:
        token = object()

        def callback(*, token: object) -> object:
            return token

        result = trace(callback, token=token)

        assert result.roller.metadata()["state"] == {"token": token}
        rollers = result.trace()["rollers"]
        assert isinstance(rollers, dict)
        assert rollers["roller0"]["metadata"]["state"] == {"token": token}

    def test_recursive_callback_with_state(self) -> None:
        def explode(
            roll: SingleOutcomeRoll[int], remaining: int = 2
        ) -> SingleOutcomeRoll[int]:
            if remaining:
                return roll + trace(explode, roll.roller, remaining=remaining - 1)
            return roll

        result = trace(explode, LiteralRoller(6))

        assert_type(result, Roll[int])
        assert result.outcomes == (18,)
        rollers = result.trace()["rollers"]
        assert isinstance(rollers, dict)
        assert (
            sum(data["metadata"]["kind"] == "dyce.trace" for data in rollers.values())
            == 3
        )

    def test_parameter_roller_failure_path(self) -> None:
        source = PRoller(P())
        with pytest.raises(RollError) as caught:
            trace(lambda roll: roll, source, name="custom")

        assert caught.value.path[0].metadata() == {
            "kind": "dyce.trace",
            "name": "custom",
            "state": {},
        }
        assert caught.value.path[1:] == (source,)

    def test_callback_failure_path(self) -> None:
        with pytest.raises(RollError) as caught:
            trace(Mock(side_effect=ValueError("callback")), name="custom")

        assert [entry.metadata() for entry in caught.value.path] == [
            {"kind": "dyce.trace", "name": "custom", "state": {}}
        ]

    def test_returned_roller_failure_path(self) -> None:
        returned = PRoller(P())
        with pytest.raises(RollError) as caught:
            trace(lambda: returned, name="custom")

        assert caught.value.path[0].metadata() == {
            "kind": "dyce.trace",
            "name": "custom",
            "state": {},
        }
        assert caught.value.path[1:] == (returned,)

    @pytest.mark.parametrize("exception_type", [ValueError, RecursionError])
    def test_original_exception_preserved_as_cause(
        self, exception_type: type[Exception]
    ) -> None:
        failure = exception_type("callback failure")
        with pytest.raises(RollError) as caught:
            trace(Mock(side_effect=failure))

        assert caught.value.__cause__ is failure

    def test_mixed_parameter_type_inference(self) -> None:
        def callback(single: SingleOutcomeRoll[int], multi: Roll[str]) -> str:
            return str(single.outcome) + multi.outcomes[0]

        result = trace(callback, LiteralRoller(3), PRoller(P(H({"a": 1}))))

        assert_type(result, Roll[str])  # zuban: ignore[misc]
        assert result.outcomes == ("3a",)

    def test_reroll_can_change_number_of_outcomes_and_records_each_callback_result(
        self,
    ) -> None:
        first_roller = RollerPool(LiteralRoller(2))
        second_roller = RollerPool(LiteralRoller(5), LiteralRoller(8))
        callback = Mock(side_effect=[first_roller, second_roller])

        result = trace(cast("Callable[[], Roller[int]]", callback))
        trace_roller = result.roller
        rerolled_result = trace_roller.roll()

        assert_type(result, Roll[int])
        rollers = result.trace()["rollers"]
        rolls = result.trace()["rolls"]
        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"]["relationships"]["sources"] == []
        assert result.outcomes == (2,)
        assert rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }
        assert rolls["roll1"]["roller"] == "roller1"
        assert rerolled_result.roller is trace_roller
        assert rerolled_result.outcomes == (5, 8)
        rerolled_trace = rerolled_result.trace()
        rerolled_rolls = rerolled_trace["rolls"]
        assert isinstance(rerolled_rolls, dict)
        assert rerolled_rolls["roll0"]["relationships"] == {
            "arguments": [],
            "result": "roll1",
        }

    @pytest.mark.parametrize(
        ("selector", "expected"), [(-1, (3,)), (slice(1, None), (2, 3))]
    )
    def test_selecting_trace_roller_calls_callback_again(
        self, selector: int | slice, expected: tuple[int, ...]
    ) -> None:
        callback = Mock(
            side_effect=[
                RollerPool(LiteralRoller(1)),
                RollerPool(LiteralRoller(1), LiteralRoller(2), LiteralRoller(3)),
            ]
        )

        result = trace(cast("Callable[[], Roller[int]]", callback))

        assert result.roller.select(selector).roll().outcomes == expected


class TestHableAndRollerBinaryArithmetic:
    def test_binary_operator_type_inference(self) -> None:
        h = H({8: 1})
        p = P(h)
        roller = LiteralRoller(3)
        roll = roller.roll()
        power_h = H({2: 1})
        power_p = P(power_h)
        power_roller = LiteralRoller(_PowerOutcome(3))
        power_roll = power_roller.roll()

        assert_type(h + roller, SingleOutcomeRoller[int])
        assert_type(roller + h, SingleOutcomeRoller[int])
        assert_type(p + roller, SingleOutcomeRoller[int])
        assert_type(roller + p, SingleOutcomeRoller[int])
        assert_type(h + roll, SingleOutcomeRoll[int])
        assert_type(roll + h, SingleOutcomeRoll[int])
        assert_type(p + roll, SingleOutcomeRoll[int])
        assert_type(roll + p, SingleOutcomeRoll[int])

        assert_type(h - roller, SingleOutcomeRoller[int])
        assert_type(roller - h, SingleOutcomeRoller[int])
        assert_type(p - roller, SingleOutcomeRoller[int])
        assert_type(roller - p, SingleOutcomeRoller[int])
        assert_type(h - roll, SingleOutcomeRoll[int])
        assert_type(roll - h, SingleOutcomeRoll[int])
        assert_type(p - roll, SingleOutcomeRoll[int])
        assert_type(roll - p, SingleOutcomeRoll[int])

        assert_type(h * roller, SingleOutcomeRoller[int])
        assert_type(roller * h, SingleOutcomeRoller[int])
        assert_type(p * roller, SingleOutcomeRoller[int])
        assert_type(roller * p, SingleOutcomeRoller[int])
        assert_type(h * roll, SingleOutcomeRoll[int])
        assert_type(roll * h, SingleOutcomeRoll[int])
        assert_type(p * roll, SingleOutcomeRoll[int])
        assert_type(roll * p, SingleOutcomeRoll[int])

        assert_type(h / roller, SingleOutcomeRoller[float])
        assert_type(roller / h, SingleOutcomeRoller[float])
        assert_type(p / roller, SingleOutcomeRoller[float])
        assert_type(roller / p, SingleOutcomeRoller[float])
        assert_type(h / roll, SingleOutcomeRoll[float])
        assert_type(roll / h, SingleOutcomeRoll[float])
        assert_type(p / roll, SingleOutcomeRoll[float])
        assert_type(roll / p, SingleOutcomeRoll[float])

        assert_type(h // roller, SingleOutcomeRoller[int])
        assert_type(roller // h, SingleOutcomeRoller[int])
        assert_type(p // roller, SingleOutcomeRoller[int])
        assert_type(roller // p, SingleOutcomeRoller[int])
        assert_type(h // roll, SingleOutcomeRoll[int])
        assert_type(roll // h, SingleOutcomeRoll[int])
        assert_type(p // roll, SingleOutcomeRoll[int])
        assert_type(roll // p, SingleOutcomeRoll[int])

        assert_type(h % roller, SingleOutcomeRoller[int])
        assert_type(roller % h, SingleOutcomeRoller[int])
        assert_type(p % roller, SingleOutcomeRoller[int])
        assert_type(roller % p, SingleOutcomeRoller[int])
        assert_type(h % roll, SingleOutcomeRoll[int])
        assert_type(roll % h, SingleOutcomeRoll[int])
        assert_type(p % roll, SingleOutcomeRoll[int])
        assert_type(roll % p, SingleOutcomeRoll[int])

        assert_type(power_h**power_roller, SingleOutcomeRoller[_PowerOutcome])
        assert_type(power_roller**power_h, SingleOutcomeRoller[_PowerOutcome])
        assert_type(power_p**power_roller, SingleOutcomeRoller[_PowerOutcome])
        assert_type(power_roller**power_p, SingleOutcomeRoller[_PowerOutcome])
        assert_type(power_h**power_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(power_roll**power_h, SingleOutcomeRoll[_PowerOutcome])
        assert_type(power_p**power_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(power_roll**power_p, SingleOutcomeRoll[_PowerOutcome])

        assert_type(h << roller, SingleOutcomeRoller[int])
        assert_type(roller << h, SingleOutcomeRoller[int])
        assert_type(p << roller, SingleOutcomeRoller[int])
        assert_type(roller << p, SingleOutcomeRoller[int])
        assert_type(h << roll, SingleOutcomeRoll[int])
        assert_type(roll << h, SingleOutcomeRoll[int])
        assert_type(p << roll, SingleOutcomeRoll[int])
        assert_type(roll << p, SingleOutcomeRoll[int])

        assert_type(h >> roller, SingleOutcomeRoller[int])
        assert_type(roller >> h, SingleOutcomeRoller[int])
        assert_type(p >> roller, SingleOutcomeRoller[int])
        assert_type(roller >> p, SingleOutcomeRoller[int])
        assert_type(h >> roll, SingleOutcomeRoll[int])
        assert_type(roll >> h, SingleOutcomeRoll[int])
        assert_type(p >> roll, SingleOutcomeRoll[int])
        assert_type(roll >> p, SingleOutcomeRoll[int])

        assert_type(h & roller, SingleOutcomeRoller[int])
        assert_type(roller & h, SingleOutcomeRoller[int])
        assert_type(p & roller, SingleOutcomeRoller[int])
        assert_type(roller & p, SingleOutcomeRoller[int])
        assert_type(h & roll, SingleOutcomeRoll[int])
        assert_type(roll & h, SingleOutcomeRoll[int])
        assert_type(p & roll, SingleOutcomeRoll[int])
        assert_type(roll & p, SingleOutcomeRoll[int])

        assert_type(h | roller, SingleOutcomeRoller[int])
        assert_type(roller | h, SingleOutcomeRoller[int])
        assert_type(p | roller, SingleOutcomeRoller[int])
        assert_type(roller | p, SingleOutcomeRoller[int])
        assert_type(h | roll, SingleOutcomeRoll[int])
        assert_type(roll | h, SingleOutcomeRoll[int])
        assert_type(p | roll, SingleOutcomeRoll[int])
        assert_type(roll | p, SingleOutcomeRoll[int])

        assert_type(h ^ roller, SingleOutcomeRoller[int])
        assert_type(roller ^ h, SingleOutcomeRoller[int])
        assert_type(p ^ roller, SingleOutcomeRoller[int])
        assert_type(roller ^ p, SingleOutcomeRoller[int])
        assert_type(h ^ roll, SingleOutcomeRoll[int])
        assert_type(roll ^ h, SingleOutcomeRoll[int])
        assert_type(p ^ roll, SingleOutcomeRoll[int])
        assert_type(roll ^ p, SingleOutcomeRoll[int])

    @pytest.mark.parametrize(("op", "_name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_with_h_and_p_produce_expected_rollers_and_rolls(
        self,
        op: Callable[[Any, Any], Any],
        _name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_h = H({lhs: 1})
        right_h = H({rhs: 1})
        left_p = P(left_h)
        right_p = P(right_h)
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)
        left_roll = left_roller.roll()
        right_roll = right_roller.roll()
        expected_outcome = op(lhs, rhs)

        roller_results = (
            op(left_roller, right_h),
            op(left_h, right_roller),
            op(left_roller, right_p),
            op(left_p, right_roller),
        )
        roll_results = (
            op(left_roll, right_h),
            op(left_h, right_roll),
            op(left_roll, right_p),
            op(left_p, right_roll),
        )

        for result in roller_results:
            assert isinstance(result, SingleOutcomeRoller)
            assert result.roll().outcome == expected_outcome

        for result in roll_results:
            assert isinstance(result, SingleOutcomeRoll)
            assert result.outcome == expected_outcome

    @pytest.mark.parametrize(
        "method_name",
        [
            pytest.param(method_name, id=f"{prefix}{name}")
            for _, name, _, _ in _BINARY_OPERATOR_CASES
            for prefix, method_name in (
                ("forward-", f"__{name}__"),
                ("reflected-", f"__r{name}__"),
            )
        ],
    )
    @pytest.mark.parametrize(
        "make_operand",
        [
            pytest.param(lambda: LiteralRoller(1), id="roller"),
            pytest.param(lambda: LiteralRoller(1).roll(), id="roll"),
        ],
    )
    def test_h_and_p_binary_operator_methods_return_not_implemented_for_rolls_and_rollers(
        self, method_name: str, make_operand: Callable[[], object]
    ) -> None:
        operand = make_operand()

        assert getattr(H(6), method_name)(operand) is NotImplemented
        assert getattr(P(6), method_name)(operand) is NotImplemented

    def test_hable_operand_is_wrapped_in_hable_roller_without_calling_h(self) -> None:
        hable = _Hable(H(6))

        with patch.object(hable, "h", wraps=hable.h) as h_mock:
            combined = LiteralRoller(1) + hable
            operands = _roller_operands(combined)
            wrapped = operands[1]

            assert isinstance(wrapped, HableRoller)
            assert wrapped.hable is hable
            h_mock.assert_not_called()

    def test_h_operand_is_wrapped_in_hroller_with_default_name(self) -> None:
        h = H(8)
        combined = LiteralRoller(1) + h
        operands = _roller_operands(combined)
        wrapped = operands[1]

        assert isinstance(wrapped, HRoller)
        assert wrapped.metadata() == {"kind": "dyce.source", "name": str(h)}

    def test_p_operand_is_wrapped_in_p_roller_wrapped_in_pool_sum_roller(self) -> None:
        p = P(H({2: 1}), H({3: 1}))
        combined = LiteralRoller(1) + p
        operands = _roller_operands(combined)
        pool_sum_roller = operands[1]
        pool_sum_operands = _roller_operands(pool_sum_roller)
        (p_roller,) = pool_sum_operands

        assert pool_sum_roller.metadata() == {"kind": "dyce.pool-sum"}
        assert isinstance(p_roller, PRoller)
        assert p_roller.p is p


class TestSingleOutcomeRoller:
    def test_sum_returns_self(self) -> None:
        roller = LiteralRoller(3)

        assert roller.sum() is roller

    def test_binary_operator_type_inference(self) -> None:
        d6 = HRoller(H(6), name="d6")
        power_roller = HRoller(H({_PowerOutcome(2): 1}))

        # TODO(@posita): <https://github.com/zubanls/zuban/issues/560>
        assert_type(d6 + H(6), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 + P(6), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 - H(6), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 - P(6), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 * H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 / H(2), SingleOutcomeRoller[float])  # zuban: ignore[misc]
        assert_type(d6 // H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 % H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(
            power_roller**2, SingleOutcomeRoller[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(d6 << H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 >> H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 & H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 | H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(d6 ^ H(2), SingleOutcomeRoller[int])  # zuban: ignore[misc]

        assert_type(2 * d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 / d6, SingleOutcomeRoller[float])  # zuban: ignore[misc]
        assert_type(12 // d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 % d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(
            2**power_roller, SingleOutcomeRoller[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(2 << d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 >> d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 & d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 | d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 ^ d6, SingleOutcomeRoller[int])  # zuban: ignore[misc]

    def test_unary_operator_type_inference(self) -> None:
        roller = LiteralRoller(-2)

        assert_type(-roller, SingleOutcomeRoller[int])
        assert_type(+roller, SingleOutcomeRoller[int])
        assert_type(abs(roller), SingleOutcomeRoller[int])
        assert_type(~roller, SingleOutcomeRoller[int])

    def test_comparison_type_inference(self) -> None:
        roller = LiteralRoller(2)

        assert_type(roller.lt(3), SingleOutcomeRoller[bool])
        assert_type(roller.le(H(3)), SingleOutcomeRoller[bool])
        assert_type(roller.eq(P(3, 2)), SingleOutcomeRoller[bool])
        assert_type(roller.ne(LiteralRoller(3)), SingleOutcomeRoller[bool])
        assert_type(
            roller.ge(RollerPool(LiteralRoller(2), LiteralRoller(3))),
            SingleOutcomeRoller[bool],
        )
        assert_type(roller.gt(1), SingleOutcomeRoller[bool])

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_rolls_and_metadata(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)
        combined = op(left_roller, right_roller)
        expected_outcome = op(lhs, rhs)

        assert combined.roll().outcome == expected_outcome
        assert combined.metadata() == {"kind": "dyce.binary", "operator": name}
        assert combined.operands == (left_roller, right_roller)

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_rolls_and_metadata(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        roller = LiteralRoller(value)
        combined = op(roller)
        expected_outcome = op(value)

        assert combined.roll().outcome == expected_outcome
        assert combined.metadata() == {"kind": "dyce.unary", "operator": name}
        assert combined.operands == (roller,)

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _COMPARISON_CASES)
    def test_comparisons_preserve_rolls_and_metadata(
        self,
        op: Callable[[Any, Any], bool],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)
        combined = getattr(left_roller, name)(right_roller)

        assert combined.roll().outcome is op(lhs, rhs)
        assert combined.metadata() == {"kind": "dyce.binary", "operator": name}
        assert combined.operands == (left_roller, right_roller)


class TestHRoller:
    def test_exposes_h_source(self) -> None:
        h = H(6)
        roller = HRoller(h, name="d6")

        assert_type(roller, HRoller[int])
        assert roller.h is h
        assert roller.metadata() == {"kind": "dyce.source", "name": "d6"}

    def test_uses_h_representation_as_default_name(self) -> None:
        h = H(6)
        roller = HRoller(h)

        assert roller.metadata() == {"kind": "dyce.source", "name": str(h)}


class TestHableRoller:
    def test_exposes_hable_source(self) -> None:
        hable = _Hable(H(6))
        roller = HableRoller(hable, name="d6")

        assert_type(roller, HableRoller[int])
        assert roller.hable is hable
        assert roller.metadata() == {"kind": "dyce.source", "name": "d6"}

    def test_uses_hable_representation_as_default_name(self) -> None:
        hable = _Hable(H(6))
        roller = HableRoller(hable)

        assert roller.metadata() == {"kind": "dyce.source", "name": str(hable)}

    def test_roll_calls_h_and_includes_source_metadata_in_trace(self) -> None:
        hable = _Hable(H({4: 1}))
        roller = HableRoller(hable, name="source")

        with patch.object(hable, "h", wraps=hable.h) as h_mock:
            roll = roller.roll()

        trace = roll.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        h_mock.assert_called_once_with()
        assert roll.outcome == 4
        assert roll.roller is roller
        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"] == {
            "metadata": {"kind": "dyce.source", "name": "source"}
        }
        assert "relationships" not in rolls["roll0"]


class TestLiteralRoller:
    def test_type_inference(self) -> None:
        roller = LiteralRoller(3)
        roll = roller.roll()

        assert_type(roller, LiteralRoller[int])  # ty: ignore[type-assertion-failure]
        assert_type(roll, SingleOutcomeRoll[int])  # ty: ignore[type-assertion-failure]
        assert_type(roll.roller, SingleOutcomeRoller[int])  # ty: ignore[type-assertion-failure]
        # ty is special, apparently
        assert_type(roller, LiteralRoller[Literal[3]])  # type: ignore[assert-type] # zuban: ignore[misc]
        assert_type(roll, SingleOutcomeRoll[Literal[3]])  # type: ignore[assert-type] # zuban: ignore[misc]
        assert_type(roll.roller, SingleOutcomeRoller[Literal[3]])  # type: ignore[assert-type] # zuban: ignore[misc]

        # An explicit generic specialization works for all checkers
        roller_int = LiteralRoller[int](3)
        roll_int = roller_int.roll()

        assert_type(roller_int, LiteralRoller[int])
        assert_type(roll_int, SingleOutcomeRoll[int])
        assert_type(roll_int.roller, SingleOutcomeRoller[int])

    def test_exposes_and_rolls_value(self) -> None:
        roller = LiteralRoller(3)
        roll = roller.roll()

        assert roller.value == 3
        assert roller.metadata() == {"kind": "dyce.literal", "value": 3}
        assert roll.outcomes == (3,)
        assert roll.outcome == 3
        assert roll.roller is roller


class TestRoller:
    def test_binary_operator_type_inference(self) -> None:
        left = PRoller(P(H({2: 1})), name="left")
        right = PRoller(P(H({3: 1})), name="right")
        single = HRoller(H({5: 1}), name="single")
        power_pool = PRoller(P(H({_PowerOutcome(2): 1})), name="power_pool")

        # TODO(@posita): <https://github.com/zubanls/zuban/issues/560>
        assert_type(left + right, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left + single, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(single + left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(
            left + P(H({5: 1})), SingleOutcomeRoller[int]
        )  # zuban: ignore[misc]
        assert_type(left - right, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(right - left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(10 - left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left * 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left / 2, SingleOutcomeRoller[float])  # zuban: ignore[misc]
        assert_type(left // 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left % 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(
            power_pool**2, SingleOutcomeRoller[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(left << 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left >> 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left & 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left | 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(left ^ 2, SingleOutcomeRoller[int])  # zuban: ignore[misc]

        assert_type(2 * left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 / left, SingleOutcomeRoller[float])  # zuban: ignore[misc]
        assert_type(12 // left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 % left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(
            2**power_pool, SingleOutcomeRoller[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(2 << left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(12 >> left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 & left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 | left, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(2 ^ left, SingleOutcomeRoller[int])  # zuban: ignore[misc]

    def test_unary_operator_type_inference(self) -> None:
        pool = PRoller(P(H({-2: 1})), name="pool")

        assert_type(-pool, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(+pool, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(abs(pool), SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert_type(~pool, SingleOutcomeRoller[int])  # zuban: ignore[misc]

    def test_comparison_type_inference(self) -> None:
        pool = PRoller(P(H({2: 1})), name="pool")

        assert_type(pool.lt(3), SingleOutcomeRoller[bool])
        assert_type(pool.le(H(3)), SingleOutcomeRoller[bool])
        assert_type(pool.eq(P(3, 2)), SingleOutcomeRoller[bool])
        assert_type(pool.ne(LiteralRoller(3)), SingleOutcomeRoller[bool])
        assert_type(
            pool.ge(RollerPool(LiteralRoller(2), LiteralRoller(3))),
            SingleOutcomeRoller[bool],
        )
        assert_type(pool.gt(1), SingleOutcomeRoller[bool])

    def test_sum_produces_single_outcome_roller(self) -> None:
        pool = PRoller(P(H({"a": 1}), H({"b": 1})), name="pool")
        summed = pool.sum()
        roll = summed.roll()

        assert_type(summed, SingleOutcomeRoller[str])  # zuban: ignore[misc]
        assert_type(roll, SingleOutcomeRoll[str])  # zuban: ignore[misc]
        assert roll.outcome == "ab"

    def test_select_on_selection_applies_selector_to_parent_selection(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        parent_selection = pool.select(-1, 0)
        selection = parent_selection.select(1)
        roll = selection.roll()
        (parent_roll,) = _roll_operands(roll)

        assert_type(selection, Roller[int])  # zuban: ignore[misc]
        assert _roller_operands(selection) == (parent_selection,)
        assert roll.outcomes == (1,)
        assert isinstance(parent_roll, Roll)
        assert parent_roll.outcomes == (3, 1)

    def test_at_returns_sum_of_selected_outcomes(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        result = pool.at(-1, 0)

        assert_type(result, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert result.roll().outcome == 4

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_rolls_and_metadata(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left = PRoller(P(H({lhs - 1: 1}), H({1: 1})), name="left")
        right = PRoller(P(H({rhs - 1: 1}), H({1: 1})), name="right")
        combined = op(left, right)
        expected_outcome = op(lhs, rhs)
        left_operand, right_operand = _roller_operands(combined)

        assert combined.roll().outcome == expected_outcome
        assert combined.metadata() == {"kind": "dyce.binary", "operator": name}
        assert left_operand.metadata() == {"kind": "dyce.pool-sum"}
        assert _roller_operands(left_operand) == (left,)
        assert right_operand.metadata() == {"kind": "dyce.pool-sum"}
        assert _roller_operands(right_operand) == (right,)
        assert op(left, LiteralRoller(rhs)).roll().outcome == expected_outcome
        assert op(LiteralRoller(lhs), right).roll().outcome == expected_outcome
        assert op(lhs, right).roll().outcome == expected_outcome
        assert op(P(H({lhs: 1})), right).roll().outcome == expected_outcome
        assert op(left, P(H({rhs: 1}))).roll().outcome == expected_outcome

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_rolls_and_metadata(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        pool = PRoller(P(H({value - 1: 1}), H({1: 1})), name="pool")
        combined = op(pool)
        expected_outcome = op(value)
        (operand,) = _roller_operands(combined)

        assert combined.roll().outcome == expected_outcome
        assert combined.metadata() == {"kind": "dyce.unary", "operator": name}
        assert operand.metadata() == {"kind": "dyce.pool-sum"}
        assert _roller_operands(operand) == (pool,)


class TestPRoller:
    @pytest.mark.parametrize("size", [0, 1, 3])
    def test_length(self, size: int) -> None:
        assert len(PRoller(size @ P(6))) == size

    def test_roll_delegates_to_p(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = P(H({2: 1}), H({1: 1}))

        def p_roll(source: P[int]) -> tuple[int, ...]:
            assert source is p
            return (1, 2)

        monkeypatch.setattr(P, "roll", p_roll)
        pool = PRoller(p, name="pool")
        roll = pool.roll()

        assert_type(pool, PRoller[int])  # zuban: ignore[misc]
        assert_type(roll, Roll[int])  # zuban: ignore[misc]
        assert pool.p is p
        assert pool.metadata()["name"] == "pool"
        assert roll.outcomes == (1, 2)
        assert roll.roller is pool

    def test_select_produces_multi_outcome_roller(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        selected = pool.select(-1, 0)
        roll = selected.roll()
        trace = roll.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert_type(selected, Roller[int])  # zuban: ignore[misc]
        assert roll.outcomes == (3, 1)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "metadata": {
                "kind": "dyce.pool-selection",
                "selectors": [-1, 0],
            },
            "relationships": {"operands": ["roller1"]},
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["outcomes"] == [3, 1]
        assert rolls["roll0"]["relationships"]["operands"] == ["roll1"]
        assert rolls["roll1"]["outcomes"] == [1, 2, 3]

    def test_invalid_selection_fails_when_rolled(self) -> None:
        selected = PRoller(P(2)).select(1)

        with pytest.raises(RollError) as caught:
            selected.roll()

        assert isinstance(caught.value.__cause__, IndexError)

    def test_empty_p_sum_type_and_metadata(self) -> None:
        pool = PRoller(P())
        summed = pool.sum()

        assert_type(pool, PRoller[Never])  # zuban: ignore[misc]
        assert_type(summed, SingleOutcomeRoller[Never])  # zuban: ignore[misc]
        assert summed.metadata() == {"kind": "dyce.pool-sum"}


class TestRollerPool:
    def test_composes_single_rollers(self) -> None:
        two = LiteralRoller(2)
        one = LiteralRoller(1)
        pool = RollerPool(two, one, name="pool")
        roll = pool.roll()

        pool_int: RollerPool[int] = pool
        assert pool_int is pool
        assert isinstance(pool, Roller)
        assert len(pool) == 2
        assert pool.rollers == (two, one)
        assert pool.operands == (two, one)
        assert roll.outcomes == (1, 2)
        assert tuple(operand.roller for operand in _roll_operands(roll)) == (one, two)
        assert pool.metadata() == {"kind": "dyce.pool", "name": "pool"}

    def test_reused_single_roller_produces_independent_rolls(self) -> None:
        d6 = HRoller(H(6), name="d6")
        trace = RollerPool(d6, d6).roll().trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"] == {
            "metadata": {"kind": "dyce.pool"},
            "relationships": {"operands": ["roller1", "roller1"]},
        }
        assert rolls["roll0"]["relationships"]["operands"] == ["roll1", "roll2"]

    def test_roll_uses_natural_order_for_incomparable_outcomes(self) -> None:
        pool = RollerPool(
            HRoller(H({2j: 1})),
            HRoller(H({1j: 1})),
        )

        assert pool.roll().outcomes == (1j, 2j)


class TestSingleOutcomeFactoryRoller:
    def test_callables(self) -> None:
        class RollerFactories:
            @roller_factory()
            def factory(self, value: int) -> SingleOutcomeRoller[int]:
                return LiteralRoller(value)

            def __call__(self, value: int) -> SingleOutcomeRoller[int]:
                return LiteralRoller(value)

        some_rollers = RollerFactories()
        returned_roller = some_rollers.factory(3)
        assert_type(returned_roller, SingleOutcomeRoller[int])
        assert isinstance(returned_roller, _SingleOutcomeFactoryRoller)
        assert returned_roller.roll().outcome == 3

        callable_factory = roller_factory(some_rollers)
        callable_roller = callable_factory(4)
        assert_type(callable_roller, SingleOutcomeRoller[int])
        assert isinstance(callable_roller, _SingleOutcomeFactoryRoller)
        assert callable_roller.metadata()["name"] == "RollerFactories"
        assert callable_roller.roll().outcome == 4

        bound_factory = roller_factory(partial(some_rollers, 5), name="bound")
        bound_roller = bound_factory()
        assert isinstance(bound_roller, _SingleOutcomeFactoryRoller)
        assert bound_roller.metadata()["name"] == "bound"
        assert bound_roller.roll().outcome == 5

    def test_implicit_name_uses_factory_name(self) -> None:
        @roller_factory
        def factory() -> SingleOutcomeRoller[int]:
            return LiteralRoller(3)

        assert factory().metadata()["name"] == factory.__name__

    @pytest.mark.parametrize("name", ["explicit_name", ""])
    def test_explicit_name_preserved(self, name: str) -> None:
        @roller_factory(name=name)
        def factory() -> SingleOutcomeRoller[int]:
            return LiteralRoller(3)

        assert factory().metadata()["name"] == name

    def test_expression(self) -> None:
        literal_roller = LiteralRoller(3)

        @roller_factory
        def factory() -> SingleOutcomeRoller[int]:
            return literal_roller

        roller = factory()
        assert isinstance(roller, _SingleOutcomeFactoryRoller)
        assert roller.expression is literal_roller
        roller_trace = roller.roll().trace()
        rollers = roller_trace["rollers"]
        rolls = roller_trace["rolls"]
        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"]["relationships"] == {"expression": "roller1"}
        assert rolls["roll0"]["relationships"] == {"result": "roll1"}

    def test_returning_non_roller_raises(self) -> None:
        @roller_factory
        def invalid_factory() -> SingleOutcomeRoller[int]:
            return cast("Any", "not_a_roller")  # type: ignore[no-any-return]

        with pytest.raises(
            TypeError, match="must return a SingleOutcomeRoller or Roller"
        ):
            invalid_factory()


class TestFactoryRoller:
    def test_callables(self) -> None:
        class RollerFactories:
            @roller_factory()
            def factory(self, n: int) -> Roller[int]:
                return PRoller(n @ P(2))

            def __call__(self, first: int, second: int) -> Roller[int]:
                return RollerPool(LiteralRoller(first), LiteralRoller(second))

        some_rollers = RollerFactories()
        returned_roller = some_rollers.factory(2)
        assert_type(returned_roller, Roller[int])
        assert isinstance(returned_roller, _FactoryRoller)
        assert len(returned_roller.roll().outcomes) == 2

        callable_factory = roller_factory(some_rollers)
        callable_roller = callable_factory(3, 4)
        assert_type(callable_roller, Roller[int])
        assert isinstance(callable_roller, _FactoryRoller)
        assert callable_roller.metadata()["name"] == "RollerFactories"
        assert callable_roller.roll().outcomes == (3, 4)

        bound_factory = roller_factory(partial(some_rollers, 5, 6), name="bound")
        bound_roller = bound_factory()
        assert isinstance(bound_roller, _FactoryRoller)
        assert bound_roller.metadata()["name"] == "bound"
        assert bound_roller.roll().outcomes == (5, 6)

    def test_implicit_name_uses_factory_name(self) -> None:
        @roller_factory
        def factory() -> Roller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == factory.__name__

    @pytest.mark.parametrize("name", ["explicit_name", ""])
    def test_explicit_name_preserved(self, name: str) -> None:
        @roller_factory(name=name)
        def factory() -> Roller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == name

    def test_expression(self) -> None:
        p_roller = PRoller(P(2))

        @roller_factory
        def factory() -> Roller[int]:
            return p_roller

        roller = factory()
        assert isinstance(roller, _FactoryRoller)
        assert roller.expression is p_roller
        roller_trace = roller.roll().trace()
        rollers = roller_trace["rollers"]
        rolls = roller_trace["rolls"]
        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"]["relationships"] == {"expression": "roller1"}
        assert rolls["roll0"]["relationships"] == {"result": "roll1"}


class TestSingleOutcomeRoll:
    def test_sum_returns_self(self) -> None:
        roll = LiteralRoller(3).roll()

        assert roll.sum() is roll

    def test_binary_operator_type_inference(self) -> None:
        roll = LiteralRoller(2).roll()
        power_roll = HRoller(H({_PowerOutcome(2): 1})).roll()

        assert_type(roll * 2, SingleOutcomeRoll[int])
        assert_type(roll / 2, SingleOutcomeRoll[float])
        assert_type(roll // 2, SingleOutcomeRoll[int])
        assert_type(roll % 2, SingleOutcomeRoll[int])
        assert_type(
            power_roll**2, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(roll << 2, SingleOutcomeRoll[int])
        assert_type(roll >> 2, SingleOutcomeRoll[int])
        assert_type(roll & 2, SingleOutcomeRoll[int])
        assert_type(roll | 2, SingleOutcomeRoll[int])
        assert_type(roll ^ 2, SingleOutcomeRoll[int])

        assert_type(2 * roll, SingleOutcomeRoll[int])
        assert_type(12 / roll, SingleOutcomeRoll[float])
        assert_type(12 // roll, SingleOutcomeRoll[int])
        assert_type(12 % roll, SingleOutcomeRoll[int])
        assert_type(
            2**power_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(2 << roll, SingleOutcomeRoll[int])
        assert_type(12 >> roll, SingleOutcomeRoll[int])
        assert_type(2 & roll, SingleOutcomeRoll[int])
        assert_type(2 | roll, SingleOutcomeRoll[int])
        assert_type(2 ^ roll, SingleOutcomeRoll[int])

    def test_unary_operator_type_inference(self) -> None:
        roll = LiteralRoller(-2).roll()

        assert_type(-roll, SingleOutcomeRoll[int])
        assert_type(+roll, SingleOutcomeRoll[int])
        assert_type(abs(roll), SingleOutcomeRoll[int])
        assert_type(~roll, SingleOutcomeRoll[int])

    def test_comparison_type_inference(self) -> None:
        roll = LiteralRoller(2).roll()

        assert_type(roll.lt(3), SingleOutcomeRoll[bool])
        assert_type(roll.le(H(3)), SingleOutcomeRoll[bool])
        assert_type(roll.eq(P(3)), SingleOutcomeRoll[bool])
        assert_type(roll.ne(LiteralRoller(3)), SingleOutcomeRoll[bool])
        assert_type(roll.ge(LiteralRoller(3).roll()), SingleOutcomeRoll[bool])
        assert_type(roll.gt(1), SingleOutcomeRoll[bool])

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_outcomes_and_trace(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roll = LiteralRoller(lhs).roll()
        right_roll = LiteralRoller(rhs).roll()
        combined = op(left_roll, right_roll)
        trace = combined.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert combined.outcome == op(lhs, rhs)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "metadata": {"kind": "dyce.binary", "operator": name},
            "relationships": {"operands": ["roller1", "roller2"]},
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"]["operands"] == ["roll1", "roll2"]

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_outcomes_and_trace(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        combined = op(LiteralRoller(value).roll())
        trace = combined.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert combined.outcome == op(value)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "metadata": {"kind": "dyce.unary", "operator": name},
            "relationships": {"operands": ["roller1"]},
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"]["operands"] == ["roll1"]

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _COMPARISON_CASES)
    def test_comparisons_preserve_outcomes_and_trace(
        self,
        op: Callable[[Any, Any], bool],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roll = LiteralRoller(lhs).roll()
        right_roll = LiteralRoller(rhs).roll()
        combined = getattr(left_roll, name)(right_roll)
        trace = combined.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert combined.outcome is op(lhs, rhs)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "metadata": {"kind": "dyce.binary", "operator": name},
            "relationships": {"operands": ["roller1", "roller2"]},
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["relationships"]["operands"] == ["roll1", "roll2"]

    def test_trace_is_json_serializable(self) -> None:
        roll = 2 + LiteralRoller(3).roll()
        trace = roll.trace()

        assert json.loads(json.dumps(trace)) == trace

    def test_trace_uses_distinct_ids_for_separate_rolls_and_same_id_for_reused_roll(
        self,
    ) -> None:
        d6 = HRoller(H(6), name="d6")
        separate = d6.roll() + d6.roll()
        reused_operand = d6.roll()
        reused = reused_operand + reused_operand
        separate_rolls = separate.trace()["rolls"]
        reused_rolls = reused.trace()["rolls"]

        assert isinstance(separate_rolls, dict)
        assert isinstance(reused_rolls, dict)
        assert separate_rolls["roll0"]["relationships"]["operands"] == [
            "roll1",
            "roll2",
        ]
        assert reused_rolls["roll0"]["relationships"]["operands"] == ["roll1", "roll1"]


class TestRoll:
    def test_sum_produces_single_outcome_roll(self) -> None:
        pool_roll = PRoller(P(H({"a": 1}), H({"b": 1})), name="pool").roll()
        roll = pool_roll.sum()

        assert_type(roll, SingleOutcomeRoll[str])  # zuban: ignore[misc]
        assert roll.outcome == "ab"
        assert _roll_operands(roll) == (pool_roll,)

    def test_empty_outcomes_raise(self) -> None:
        with pytest.raises(ValueError, match="at least one outcome"):
            Roll((), PRoller(P()))

    def test_comparison_type_inference(self) -> None:
        roll = PRoller(P(H({2: 1}))).roll()

        assert_type(roll.lt(3), SingleOutcomeRoll[bool])
        assert_type(roll.le(H(3)), SingleOutcomeRoll[bool])
        assert_type(roll.eq(P(3)), SingleOutcomeRoll[bool])
        assert_type(roll.ne(LiteralRoller(3)), SingleOutcomeRoll[bool])
        assert_type(roll.ge(LiteralRoller(3).roll()), SingleOutcomeRoll[bool])
        assert_type(roll.gt(1), SingleOutcomeRoll[bool])


class TestMixedRollBinaryArithmetic:
    def test_type_inference(self) -> None:
        single = LiteralRoller(4)
        multi = PRoller(P(H({1: 1}), H({3: 1})))
        single_roll = LiteralRoller(9).roll()
        multi_roll = PRoller(P(H({2: 1}), H({7: 1}))).roll()

        assert_type(single + single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll + single, SingleOutcomeRoll[int])
        # TODO(@posita): <https://github.com/zubanls/zuban/issues/560>
        assert_type(single + multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll + single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi + single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll + multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi + multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll + multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll + multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll + single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll + multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single - single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll - single, SingleOutcomeRoll[int])
        assert_type(single - multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll - single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi - single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll - multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi - multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll - multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll - multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll - single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll - multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single * single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll * single, SingleOutcomeRoll[int])
        assert_type(single * multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll * single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi * single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll * multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi * multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll * multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll * multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll * single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll * multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single / single_roll, SingleOutcomeRoll[float])
        assert_type(single_roll / single, SingleOutcomeRoll[float])
        assert_type(single / multi_roll, SingleOutcomeRoll[float])
        assert_type(
            multi_roll / single, SingleOutcomeRoll[float]
        )  # zuban: ignore[misc]
        assert_type(
            multi / single_roll, SingleOutcomeRoll[float]
        )  # zuban: ignore[misc]
        assert_type(
            single_roll / multi, SingleOutcomeRoll[float]
        )  # zuban: ignore[misc]
        assert_type(multi / multi_roll, SingleOutcomeRoll[float])  # zuban: ignore[misc]
        assert_type(multi_roll / multi, SingleOutcomeRoll[float])  # zuban: ignore[misc]
        assert_type(single_roll / multi_roll, SingleOutcomeRoll[float])
        assert_type(
            multi_roll / single_roll, SingleOutcomeRoll[float]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll / multi_roll, SingleOutcomeRoll[float]
        )  # zuban: ignore[misc]

        assert_type(single // single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll // single, SingleOutcomeRoll[int])
        assert_type(single // multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll // single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi // single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll // multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi // multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll // multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll // multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll // single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll // multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single % single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll % single, SingleOutcomeRoll[int])
        assert_type(single % multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll % single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi % single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll % multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi % multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll % multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll % multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll % single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll % multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single << single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll << single, SingleOutcomeRoll[int])
        assert_type(single << multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll << single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi << single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll << multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi << multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll << multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll << multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll << single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll << multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single >> single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll >> single, SingleOutcomeRoll[int])
        assert_type(single >> multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll >> single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi >> single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll >> multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi >> multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll >> multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll >> multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll >> single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll >> multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single & single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll & single, SingleOutcomeRoll[int])
        assert_type(single & multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll & single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi & single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll & multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi & multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll & multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll & multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll & single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll & multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single | single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll | single, SingleOutcomeRoll[int])
        assert_type(single | multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll | single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi | single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll | multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi | multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll | multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll | multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll | single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll | multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

        assert_type(single ^ single_roll, SingleOutcomeRoll[int])
        assert_type(single_roll ^ single, SingleOutcomeRoll[int])
        assert_type(single ^ multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll ^ single, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi ^ single_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll ^ multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi ^ multi_roll, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(multi_roll ^ multi, SingleOutcomeRoll[int])  # zuban: ignore[misc]
        assert_type(single_roll ^ multi_roll, SingleOutcomeRoll[int])
        assert_type(
            multi_roll ^ single_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll ^ multi_roll, SingleOutcomeRoll[int]
        )  # zuban: ignore[misc]

    def test_addition_with_forward_only_outcome_type_inference(self) -> None:
        addable_roller = LiteralRoller(_AddableOutcome(1))
        addable_roll = LiteralRoller(_AddableOutcome(2)).roll()

        assert_type(
            addable_roller + addable_roll,  # zuban: ignore[misc]
            SingleOutcomeRoll[_AddableOutcome],
        )

    def test_power_type_inference(self) -> None:
        single = LiteralRoller(2)
        multi = PRoller(P(H({1: 1}), H({2: 1})))
        single_roll = single.roll()
        multi_roll = multi.roll()
        power_single = LiteralRoller(_PowerOutcome(2))
        power_multi = PRoller(P(H({_PowerOutcome(2): 1})))
        power_single_roll = power_single.roll()
        power_multi_roll = power_multi.roll()

        assert_type(power_single**single_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(single_roll**power_single, SingleOutcomeRoll[_PowerOutcome])
        # TODO(@posita): <https://github.com/zubanls/zuban/issues/560>
        assert_type(
            power_single**multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll**power_single, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi**single_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            single_roll**power_multi, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi**multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll**power_multi, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(power_single_roll**single, SingleOutcomeRoll[_PowerOutcome])
        assert_type(single**power_single_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(power_single_roll**multi, SingleOutcomeRoll[_PowerOutcome])
        assert_type(
            multi**power_single_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi_roll**single, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            single**power_multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi_roll**multi, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            multi**power_multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(power_single_roll**multi_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(
            multi_roll**power_single_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi_roll**single_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            single_roll**power_multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            power_multi_roll**multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]
        assert_type(
            multi_roll**power_multi_roll, SingleOutcomeRoll[_PowerOutcome]
        )  # zuban: ignore[misc]

    @pytest.mark.parametrize(
        "op",
        [pytest.param(op, id=name) for op, name, _, _ in _BINARY_OPERATOR_CASES],
    )
    @pytest.mark.parametrize(
        "reverse", [False, True], ids=["roller-first", "roll-first"]
    )
    @pytest.mark.parametrize(
        "make_roller",
        [lambda: LiteralRoller(4), lambda: PRoller(P(H({1: 1}), H({3: 1})))],
        ids=["single-roller", "multi-roller"],
    )
    @pytest.mark.parametrize(
        "make_roll",
        [
            lambda: LiteralRoller(9).roll(),
            lambda: PRoller(P(H({2: 1}), H({7: 1}))).roll(),
        ],
        ids=["single-roll", "multi-roll"],
    )
    def test_roll_with_roller_produces_roll(
        self,
        *,
        op: Callable[[Any, Any], Any],
        reverse: bool,
        make_roller: Callable[[], Roller[int]],
        make_roll: Callable[[], Roll[int]],
    ) -> None:
        roller = make_roller()
        roll = make_roll()

        combined = op(roll, roller) if reverse else op(roller, roll)

        assert isinstance(combined, SingleOutcomeRoll)
        assert combined.outcome == (op(9, 4) if reverse else op(4, 9))

    @pytest.mark.parametrize(
        "op",
        [pytest.param(op, id=name) for op, name, _, _ in _BINARY_OPERATOR_CASES],
    )
    @pytest.mark.parametrize(
        ("left_multi", "right_multi"),
        [(False, True), (True, False), (True, True)],
        ids=["single-multi", "multi-single", "multi-multi"],
    )
    def test_multi_outcome_roll_with_single_or_multi_outcome_roll_produces_single_outcome_roll(
        self,
        *,
        op: Callable[[Any, Any], Any],
        left_multi: bool,
        right_multi: bool,
    ) -> None:
        left = (
            PRoller(P(H({1: 1}), H({3: 1}))).roll()
            if left_multi
            else LiteralRoller(4).roll()
        )
        right = (
            PRoller(P(H({2: 1}), H({7: 1}))).roll()
            if right_multi
            else LiteralRoller(9).roll()
        )

        combined = op(left, right)

        assert isinstance(combined, SingleOutcomeRoll)
        assert combined.outcome == op(4, 9)

    @pytest.mark.parametrize(
        "op",
        [pytest.param(op, id=name) for op, name, _, _ in _BINARY_OPERATOR_CASES],
    )
    @pytest.mark.parametrize(
        "reverse", [False, True], ids=["roll-first", "outcome-first"]
    )
    def test_multi_outcome_roll_with_literal_produces_single_outcome_roll(
        self, *, op: Callable[[Any, Any], Any], reverse: bool
    ) -> None:
        roll = PRoller(P(H({2: 1}), H({7: 1}))).roll()

        combined = op(4, roll) if reverse else op(roll, 4)

        assert isinstance(combined, SingleOutcomeRoll)
        assert combined.outcome == (op(4, 9) if reverse else op(9, 4))

    @pytest.mark.parametrize(("_op", "name", "_lhs", "_rhs"), _BINARY_OPERATOR_CASES)
    def test_roller_methods_return_not_implemented_for_roll(
        self,
        _op: Callable[[Any, Any], Any],
        name: str,
        _lhs: int,
        _rhs: int,
    ) -> None:
        single_roller = LiteralRoller(2)
        multi_roller = PRoller(P(H({1: 1}), H({2: 1})))
        roll = LiteralRoller(3).roll()
        method_name = f"__{name}__"
        reflected_method_name = f"__r{name}__"

        assert getattr(single_roller, method_name)(roll) is NotImplemented
        assert getattr(single_roller, reflected_method_name)(roll) is NotImplemented
        assert getattr(multi_roller, method_name)(roll) is NotImplemented
        assert getattr(multi_roller, reflected_method_name)(roll) is NotImplemented

    def test_result_roller_rerolls_sources_after_roll(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        first, second = 3, 6
        choices = Mock(side_effect=[[first], [second]])
        monkeypatch.setattr(rng.RNG, "choices", choices)
        left_roller = HRoller(H({first: 1, second: 1}))
        left_roll = left_roller.roll()
        right_roller = LiteralRoller(2)

        result = left_roll + right_roller
        rerolled_result = result.roller.roll()

        assert result.outcome == first + 2
        roll_operands = _roll_operands(result)
        assert roll_operands[0] is left_roll
        assert roll_operands[1].roller is right_roller
        roller_operands = _roller_operands(result.roller)
        assert roller_operands[0] is left_roller
        assert roller_operands[1] is right_roller
        assert rerolled_result.outcome == second + 2
        assert choices.call_count == 2

    def test_format_binary_expression(self) -> None:
        left = HRoller(H({2: 1}), name="d6")
        right = HRoller(H({1: 1}), name="d6")

        result = ((left + right) * 5).roll()

        assert result.format() == "(2 [d6] + 1 [d6]) * 5 => 15"

    def test_format_preserves_operator_precedence(self) -> None:
        left = cast("Any", LiteralRoller(2))
        right = cast("Any", LiteralRoller(3))
        left_associative = ((left**3) ** 2).roll()
        right_associative = (left ** (right**2)).roll()
        unary = (-(LiteralRoller(2) + 3)).roll()

        assert left_associative.format() == "(2 ** 3) ** 2 => 64"
        assert right_associative.format() == "2 ** 3 ** 2 => 512"
        assert unary.format() == "-(2 + 3) => -5"
        assert abs(LiteralRoller(-2)).roll().format() == "abs(-2) => 2"

    def test_format_comparison(self) -> None:
        roller = HRoller(H({2: 1}), name="d6")
        result = roller.lt(4).roll()
        nested = roller.lt(3).lt(4).roll()
        existing_roll = LiteralRoller(4).roll()

        assert result.format() == "2 [d6] < 4 => True"
        assert nested.format() == "(2 [d6] < 3) < 4 => True"
        assert roller.lt(existing_roll).format() == "2 [d6] < 4 => True"

    def test_format_named_boundary(self) -> None:
        d6 = HRoller(H({2: 1}), name="d6")

        @roller_factory(name="attack")
        def attack() -> SingleOutcomeRoller[int]:
            return d6 + 1

        assert attack().roll().format() == "attack(2 [d6] + 1) => 3"

    def test_format_pool_operations(self) -> None:
        pool = RollerPool(
            HRoller(H({2: 1}), name="d6"),
            HRoller(H({1: 1}), name="d6"),
            name="pool",
        )

        assert pool.roll().format() == "(1 [d6], 2 [d6]) [pool] => (1, 2)"
        assert pool.sum().roll().format() == "sum((1 [d6], 2 [d6]) [pool]) => 3"
        assert pool.select(-1).roll().format() == (
            "select((1 [d6], 2 [d6]) [pool], -1) => (2,)"
        )
        assert pool.select(slice(None, None, 2)).roll().format() == (
            "select((1 [d6], 2 [d6]) [pool], slice(None, None, 2)) => (1,)"
        )
        assert RollerPool(LiteralRoller(1), name="pool").roll().format() == (
            "(1,) [pool] => (1,)"
        )
        assert PRoller(P(H({1: 1}), H({2: 1})), name="pool").roll().format() == (
            "(1, 2) [pool] => (1, 2)"
        )

    def test_format_customer_roller_fallback(self) -> None:
        class CustomRoll(SingleOutcomeRoll[int]):
            __slots__ = ("operands",)
            operands: tuple[Roll[object], ...]

            def __init__(
                self,
                outcome: int,
                roller: SingleOutcomeRoller[int],
                operands: tuple[Roll[object], ...],
            ) -> None:
                super().__init__(outcome, roller)
                object.__setattr__(self, "operands", operands)

            def _trace_relationships(
                self,
            ) -> dict[str, Roll[object] | tuple[Roll[object], ...]]:
                return {"operands": self.operands}

        class CustomRoller(SingleOutcomeRoller[int]):
            def __init__(self, operand: SingleOutcomeRoller[int] | None = None) -> None:
                self._operand = operand

            @property
            def operands(self) -> tuple[Roller[object], ...]:
                return () if self._operand is None else (self._operand,)

            def metadata(self) -> dict[str, object]:
                return {"kind": "tests.custom", "name": "custom"}

            def _trace_relationships(
                self,
            ) -> dict[str, Roller[object] | tuple[Roller[object], ...]]:
                return {"operands": self.operands}

            def _roll(self) -> SingleOutcomeRoll[int]:
                if self._operand is None:
                    outcome: int = 2
                    return SingleOutcomeRoll[int](outcome, self)
                else:
                    operand_roll = self._operand.roll()
                    return CustomRoll(operand_roll.outcome, self, (operand_roll,))

        source = CustomRoller()

        assert source.roll().format() == "2 [custom] => 2"
        assert CustomRoller(source).roll().format() == "custom(2 [custom]) => 2"


class TestRollerAndRollOperationEquivalence:
    @pytest.mark.parametrize(("op", "_name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators(
        self,
        op: Callable[[Any, Any], Any],
        _name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)

        roll_from_roller_arithmetic = op(left_roller, right_roller).roll()
        roll_from_roll_arithmetic = op(left_roller.roll(), right_roller.roll())
        reflected_roll_from_roller_arithmetic = op(lhs, right_roller).roll()
        reflected_roll_from_roll_arithmetic = op(lhs, right_roller.roll())

        assert roll_from_roller_arithmetic.trace() == roll_from_roll_arithmetic.trace()
        assert (
            reflected_roll_from_roller_arithmetic.trace()
            == reflected_roll_from_roll_arithmetic.trace()
        )

    @pytest.mark.parametrize(("op", "_name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators(
        self,
        op: Callable[[Any], Any],
        _name: str,
        value: int,
    ) -> None:
        roller = LiteralRoller(value)

        assert op(roller).roll().trace() == op(roller.roll()).trace()

    @pytest.mark.parametrize(("_op", "name", "lhs", "rhs"), _COMPARISON_CASES)
    def test_comparisons(
        self,
        _op: Callable[[Any, Any], bool],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)

        roll_from_rollers = getattr(left_roller, name)(right_roller).roll()
        roll_from_rolls = getattr(left_roller.roll(), name)(right_roller.roll())

        assert roll_from_rollers.trace() == roll_from_rolls.trace()

    def test_pool_selection_and_sum(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")

        roll_from_roller_sum = pool.select(-1, 0).sum().roll()
        roll_from_roll_sum = pool.select(-1, 0).roll().sum()

        assert roll_from_roller_sum.trace() == roll_from_roll_sum.trace()

    @pytest.mark.parametrize(
        "make_pool",
        [
            lambda: PRoller(P()),
            RollerPool,
            lambda: PRoller(P(6)).select(slice(0)),
            lambda: RollerPool(LiteralRoller(1)).select(slice(0)),
            lambda: PRoller(P(6)).select(0).select(slice(0)),
        ],
    )
    def test_empty_pool_roll_raises(self, make_pool: Callable[[], Roller[int]]) -> None:
        pool = make_pool()
        with pytest.raises(RollError, match="no outcomes from an empty"):
            pool.roll()
        with pytest.raises(RollError, match="no outcomes from an empty"):
            pool.sum().roll()
        with pytest.raises(RollError, match="no outcomes from an empty"):
            pool.roll().sum()

    def test_roller_subtraction_and_roll_subtraction_produce_equivalent_rolls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")
        d4 = HRoller(H(4), name="d4")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        roll_from_roller_arithmetic = (d6 - d4).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        roll_from_roll_arithmetic = d6.roll() - d4.roll()

        assert roll_from_roller_arithmetic.outcome == roll_from_roll_arithmetic.outcome
        assert roll_from_roller_arithmetic.trace() == roll_from_roll_arithmetic.trace()
        rollers = roll_from_roller_arithmetic.trace()["rollers"]
        assert isinstance(rollers, dict)
        assert rollers["roller0"]["metadata"]["operator"] == "sub"

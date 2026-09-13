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
from typing import Any, Never, assert_type, cast
from unittest.mock import Mock, patch

import pytest

from dyce import H, HableT, P, rng
from dyce.roller import (
    HableRoller,
    HRoller,
    LiteralRoller,
    MultiOutcomeRoll,
    MultiOutcomeRoller,
    PRoller,
    RollerPool,
    RollError,
    SingleOutcomeRoll,
    SingleOutcomeRoller,
    _MultiOutcomeFactoryRoller,
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
_UNARY_OPERATOR_CASES: tuple[tuple[Callable[[Any], Any], str, int], ...] = (
    (operator.neg, "neg", 3),
    (operator.pos, "pos", -3),
    (operator.abs, "abs", -3),
    (operator.invert, "invert", 3),
)


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
    # sum() methods from either MultiOutcomeRoller or MultiOutcomeRoll
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

        with pytest.raises(RollError) as caught:
            roller.roll()
        assert caught.value.path == (
            roller,
            roller.operands[0],
            roller.operands[0].operands[1],
            damage,
        )

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
            "  {'kind': 'pool'}\n"
            "  → {'kind': 'pool-sum'}\n"
            "  → {'kind': 'pool-source', 'name': 'damage'}"
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
        assert isinstance(args[1], MultiOutcomeRoll)
        assert args[1].outcomes == (2, 4)  # zuban: ignore[comparison-overlap]
        assert args[1].roller is multi
        assert kwargs == {"token": token}

    def test_callback_returns_single_roll(self) -> None:
        roll = LiteralRoller(4).roll()

        def callback() -> SingleOutcomeRoll[int]:
            return roll

        result = trace(callback)

        assert_type(result, SingleOutcomeRoll[int])
        assert result.outcome == 4
        assert result.operands == (roll,)

    def test_callback_returns_multi_roll(self) -> None:
        returned = PRoller(P(H({2: 1}), H({3: 1}))).roll()

        def callback() -> MultiOutcomeRoll[int]:
            return returned

        result = trace(callback)

        assert_type(result, MultiOutcomeRoll[int])
        assert result.outcomes == (2, 3)
        assert result.operands == (returned,)

    def test_callback_returns_single_roller(self) -> None:
        def callback() -> SingleOutcomeRoller[int]:
            return LiteralRoller(8)

        result = trace(callback)

        assert_type(result, SingleOutcomeRoll[int])
        assert result.outcome == 8
        assert isinstance(result.operands[0], SingleOutcomeRoll)
        assert result.operands[0].outcome == 8

    def test_callback_returns_multi_roller(self) -> None:
        def callback() -> MultiOutcomeRoller[int]:
            return PRoller(P(H({2: 1}), H({3: 1})))

        result = trace(callback)

        assert_type(result, MultiOutcomeRoll[int])
        assert result.outcomes == (2, 3)
        assert isinstance(result.operands[0], MultiOutcomeRoll)
        assert result.operands[0].outcomes == (2, 3)

    def test_callback_returns_literal_string(self) -> None:
        source = LiteralRoller(3)

        def callback(roll: SingleOutcomeRoll[int]) -> str:
            return "hit" if roll.outcome == 3 else "miss"

        result = trace(callback, source)

        assert_type(result, SingleOutcomeRoll[str])
        assert result.outcome == "hit"
        assert len(result.operands) == 1
        assert isinstance(result.operands[0], SingleOutcomeRoll)
        assert result.operands[0].outcome == "hit"
        assert isinstance(result.operands[0].roller, LiteralRoller)

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

    def test_binary_return_trace(self) -> None:
        def callback(roll: SingleOutcomeRoll[int]) -> SingleOutcomeRoll[int]:
            return 1 + roll

        result = trace(callback, HRoller(H(6), name="d6"))
        rolls = result.trace()["rolls"]

        assert isinstance(rolls, dict)
        assert rolls["roll0"]["operands"] == ["roll1"]
        assert rolls["roll1"]["operands"] == ["roll2", "roll3"]
        assert rolls["roll2"]["outcome"] == 1
        assert rolls["roll0"]["outcome"] == 1 + rolls["roll3"]["outcome"]

    def test_implicit_name_uses_callback_name(self) -> None:
        def callback() -> int:
            return 4

        result = trace(callback)

        assert result.roller.metadata() == {
            "kind": "trace",
            "name": "callback",
            "state": {},
        }

    @pytest.mark.parametrize("name", ["trace.custom", ""])
    def test_explicit_name_preserved(self, name: str) -> None:
        def callback() -> int:
            return 4

        result = trace(callback, name=name)

        assert result.roller.metadata() == {
            "kind": "trace",
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
        assert rollers["roller0"]["state"] == {"token": token}

    def test_recursive_callback_with_state(self) -> None:
        def explode(
            roll: SingleOutcomeRoll[int], remaining: int = 2
        ) -> SingleOutcomeRoll[int]:
            if remaining:
                return roll + trace(explode, roll.roller, remaining=remaining - 1)
            return roll

        result = trace(explode, LiteralRoller(6))

        assert_type(result, SingleOutcomeRoll[int])
        assert result.outcome == 18
        rollers = result.trace()["rollers"]
        assert isinstance(rollers, dict)
        assert sum(data["kind"] == "trace" for data in rollers.values()) == 3

    def test_parameter_roller_failure_path(self) -> None:
        source = PRoller(P())
        with pytest.raises(RollError) as caught:
            trace(lambda roll: roll, source, name="custom")

        assert caught.value.path[0].metadata() == {
            "kind": "trace",
            "name": "custom",
            "state": {},
        }
        assert caught.value.path[1:] == (source,)

    def test_callback_failure_path(self) -> None:
        with pytest.raises(RollError) as caught:
            trace(Mock(side_effect=ValueError("callback")), name="custom")

        assert [entry.metadata() for entry in caught.value.path] == [
            {"kind": "trace", "name": "custom", "state": {}}
        ]

    def test_returned_roller_failure_path(self) -> None:
        returned = PRoller(P())
        with pytest.raises(RollError) as caught:
            trace(lambda: returned, name="custom")

        assert caught.value.path[0].metadata() == {
            "kind": "trace",
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
        def callback(
            single: SingleOutcomeRoll[int], multi: MultiOutcomeRoll[str]
        ) -> str:
            return str(single.outcome) + multi.outcomes[0]

        result = trace(callback, LiteralRoller(3), PRoller(P(H({"a": 1}))))

        assert_type(result, SingleOutcomeRoll[str])  # zuban: ignore[misc]
        assert result.outcome == "3a"

    def test_single_outcome_roller_calls_callback_again(self) -> None:
        callback = Mock(side_effect=[2, 5])
        result = trace(cast("Callable[[], int]", callback))

        assert result.roller.roll().outcome == 5

    @pytest.mark.parametrize(
        ("selector", "expected"), [(-1, (3,)), (slice(1, None), (2, 3))]
    )
    def test_multi_outcome_roller_selection_calls_callback_again(
        self, selector: int | slice, expected: tuple[int, ...]
    ) -> None:
        callback = Mock(
            side_effect=[
                RollerPool(LiteralRoller(1)),
                RollerPool(LiteralRoller(1), LiteralRoller(2), LiteralRoller(3)),
            ]
        )

        result = trace(cast("Callable[[], MultiOutcomeRoller[int]]", callback))

        assert result.roller.select(selector).roll().outcomes == expected


class TestHableAndRollerBinaryArithmetic:
    @pytest.mark.parametrize(
        "method_name",
        [
            pytest.param(f"__{name}__", id=name)
            for _, name, _, _ in _BINARY_OPERATOR_CASES
        ],
    )
    def test_h_and_p_binary_operator_methods_return_not_implemented_for_roller(
        self, method_name: str
    ) -> None:
        roller = LiteralRoller(1)

        assert getattr(H(6), method_name)(roller) is NotImplemented
        assert getattr(P(6), method_name)(roller) is NotImplemented

    @pytest.mark.parametrize(("op", "_name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_with_h_and_p_produce_expected_distributions(
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
        expected_h = H({op(lhs, rhs): 1})

        results = (
            op(left_roller, right_h),
            op(left_h, right_roller),
            op(left_roller, right_p),
            op(left_p, right_roller),
        )

        for result in results:
            assert isinstance(result, SingleOutcomeRoller)
            assert result.h() == expected_h

    def test_hable_operand_is_wrapped_in_hable_roller_without_calling_h(self) -> None:
        hable = _Hable(H(6))

        with patch.object(hable, "h", wraps=hable.h) as h_mock:
            combined = LiteralRoller(1) + hable
            wrapped = combined.operands[1]

            assert isinstance(wrapped, HableRoller)
            assert wrapped.hable is hable
            h_mock.assert_not_called()
            assert combined.h() == H(6) + 1
            h_mock.assert_called_once_with()

    def test_h_operand_is_wrapped_in_hroller_with_default_name(self) -> None:
        h = H(8)
        combined = LiteralRoller(1) + h
        wrapped = combined.operands[1]

        assert isinstance(wrapped, HRoller)
        assert wrapped.h() is h
        assert wrapped.metadata() == {"kind": "source", "name": str(h)}

    def test_p_operand_is_wrapped_in_p_roller_wrapped_in_pool_sum_roller(self) -> None:
        p = P(H({2: 1}), H({3: 1}))
        combined = LiteralRoller(1) + p
        pool_sum_roller = combined.operands[1]
        (p_roller,) = pool_sum_roller.operands

        assert pool_sum_roller.metadata() == {"kind": "pool-sum"}
        assert isinstance(p_roller, PRoller)
        assert p_roller.p is p


class TestSingleOutcomeRoller:
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

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_distributions_and_metadata(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)
        combined = op(left_roller, right_roller)
        expected_h = H({op(lhs, rhs): 1})

        assert combined.h() == expected_h
        assert combined.metadata() == {"kind": "binary", "operator": name}
        assert combined.operands == (left_roller, right_roller)

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_distributions_and_metadata(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        roller = LiteralRoller(value)
        combined = op(roller)
        expected_h = H({op(value): 1})

        assert combined.h() == expected_h
        assert combined.metadata() == {"kind": "unary", "operator": name}
        assert combined.operands == (roller,)


class TestHRoller:
    def test_addition_preserves_distribution(self) -> None:
        d6 = HRoller(H(6), name="d6")

        assert d6.metadata()["name"] == "d6"
        assert (d6 + d6).h() == 2 @ H(6)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (d6 + 2).h() == H(6) + 2
        assert (2 + d6).h() == 2 + H(6)

    def test_distribution_is_computed_lazily(self) -> None:
        outcome = _AddableOutcome(1)
        source = HRoller(H({outcome: 1}), name="source")

        with patch.object(
            _AddableOutcome,
            "__add__",
            autospec=True,
            side_effect=_AddableOutcome.__add__,
        ) as add:
            combined = source + source
            add.assert_not_called()
            assert combined.h() == H({_AddableOutcome(2): 1})
            add.assert_called_once_with(outcome, outcome)


class TestHableRoller:
    def test_exposes_hable_source(self) -> None:
        hable = _Hable(H(6))
        roller = HableRoller(hable, name="d6")

        assert_type(roller, HableRoller[int])
        assert roller.hable is hable
        assert roller.h() == H(6)
        assert roller.metadata() == {"kind": "source", "name": "d6"}

    def test_uses_hable_representation_as_default_name(self) -> None:
        hable = _Hable(H(6))
        roller = HableRoller(hable)

        assert roller.metadata() == {"kind": "source", "name": str(hable)}

    def test_roll_calls_h_and_includes_source_metadata_in_trace(self) -> None:
        hable = _Hable(H({4: 1}))
        roller = HableRoller(hable, name="source")

        with patch.object(hable, "h", wraps=hable.h) as h_mock:
            roll = roller.roll()

        trace = roll.trace()
        rollers = trace["rollers"]

        h_mock.assert_called_once_with()
        assert roll.outcome == 4
        assert roll.roller is roller
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {"kind": "source", "name": "source"}


class TestLiteralRoller:
    def test_exposes_and_rolls_value(self) -> None:
        roller = LiteralRoller(3)
        roll = roller.roll()

        assert_type(roller, LiteralRoller[int])
        assert roller.value == 3
        assert roller.h() == H({3: 1})
        assert roller.metadata() == {"kind": "literal", "value": 3}
        assert roll.outcome == 3
        assert roll.roller is roller


class TestMultiOutcomeRoller:
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

    def test_sum_produces_single_outcome_roller(self) -> None:
        pool = PRoller(P(H({"a": 1}), H({"b": 1})), name="pool")
        summed = pool.sum()
        roll = summed.roll()

        assert_type(summed, SingleOutcomeRoller[str])  # zuban: ignore[misc]
        assert summed.h() == H({"ab": 1})
        assert_type(roll, SingleOutcomeRoll[str])  # zuban: ignore[misc]
        assert roll.outcome == "ab"

    def test_select_on_selection_applies_selector_to_parent_selection(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        parent_selection = pool.select(-1, 0)
        selection = parent_selection.select(1)
        roll = selection.roll()
        (parent_roll,) = roll.operands

        assert_type(selection, MultiOutcomeRoller[int])  # zuban: ignore[misc]
        assert selection.operands == (parent_selection,)
        assert list(selection.rolls_with_counts()) == [((1,), 1)]
        assert roll.outcomes == (1,)
        assert isinstance(parent_roll, MultiOutcomeRoll)
        assert parent_roll.outcomes == (3, 1)

    def test_select_applies_selector_to_each_outcome_tuple_and_preserves_counts(
        self,
    ) -> None:
        pool = PRoller(P(2))
        with patch.object(
            PRoller,
            "rolls_with_counts",
            return_value=iter(
                [
                    ((1, 2), 3),
                    ((1, 2, 3), 4),
                ]
            ),
        ):
            assert list(pool.select(-1).rolls_with_counts()) == [((2,), 3), ((3,), 4)]

    def test_h_excludes_empty_selection_results_from_distribution(self) -> None:
        pool = PRoller(P(2))
        with patch.object(
            PRoller,
            "rolls_with_counts",
            return_value=iter(
                [
                    ((1,), 3),
                    ((1, 2, 3), 4),
                ]
            ),
        ):
            assert pool.select(slice(1, None)).h() == H({5: 4})

    def test_at_returns_sum_of_selected_outcomes(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        result = pool.at(-1, 0)

        assert_type(result, SingleOutcomeRoller[int])  # zuban: ignore[misc]
        assert result.h() == H({4: 1})
        assert result.roll().outcome == 4

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_distributions_and_metadata(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left = PRoller(P(H({lhs - 1: 1}), H({1: 1})), name="left")
        right = PRoller(P(H({rhs - 1: 1}), H({1: 1})), name="right")
        combined = op(left, right)
        expected_h = H({op(lhs, rhs): 1})
        left_operand, right_operand = combined.operands

        assert combined.h() == expected_h
        assert combined.metadata() == {"kind": "binary", "operator": name}
        assert left_operand.metadata() == {"kind": "pool-sum"}
        assert left_operand.operands == (left,)
        assert right_operand.metadata() == {"kind": "pool-sum"}
        assert right_operand.operands == (right,)
        assert op(left, LiteralRoller(rhs)).h() == expected_h
        assert op(LiteralRoller(lhs), right).h() == expected_h
        assert op(lhs, right).h() == expected_h
        assert op(P(H({lhs: 1})), right).h() == expected_h
        assert op(left, P(H({rhs: 1}))).h() == expected_h

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_distributions_and_metadata(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        pool = PRoller(P(H({value - 1: 1}), H({1: 1})), name="pool")
        combined = op(pool)
        expected_h = H({op(value): 1})
        (operand,) = combined.operands

        assert combined.h() == expected_h
        assert combined.metadata() == {"kind": "unary", "operator": name}
        assert operand.metadata() == {"kind": "pool-sum"}
        assert operand.operands == (pool,)


class TestPRoller:
    @pytest.mark.parametrize("size", [0, 1, 3])
    def test_length(self, size: int) -> None:
        assert len(PRoller(size @ P(6))) == size

    def test_is_hable_as_aggregate_distribution(self) -> None:
        p = P(H({1: 1}), H({2: 1}))
        pool = PRoller(p, name="pool")

        assert isinstance(pool, HableT)
        assert pool.h() == p.h()

    def test_roll_delegates_to_p(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = P(H({2: 1}), H({1: 1}))

        def p_roll(source: P[int]) -> tuple[int, ...]:
            assert source is p
            return (1, 2)

        monkeypatch.setattr(P, "roll", p_roll)
        pool = PRoller(p, name="pool")
        roll = pool.roll()

        assert_type(pool, PRoller[int])  # zuban: ignore[misc]
        assert_type(roll, MultiOutcomeRoll[int])  # zuban: ignore[misc]
        assert pool.p is p
        assert pool.metadata()["name"] == "pool"
        assert pool.operands == ()
        assert roll.outcomes == (1, 2)
        assert roll.roller is pool
        assert roll.operands == ()

    def test_rolls_with_counts_matches_source_p(self) -> None:
        p = P(H(2), H(3))

        assert list(PRoller(p).rolls_with_counts()) == list(p.rolls_with_counts())

    def test_select_produces_multi_outcome_roller(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        selected = pool.select(-1, 0)
        roll = selected.roll()
        trace = roll.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert_type(selected, MultiOutcomeRoller[int])  # zuban: ignore[misc]
        assert roll.outcomes == (3, 1)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "kind": "pool-selection",
            "selectors": [-1, 0],
            "operands": ["roller1"],
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["outcomes"] == [3, 1]
        assert rolls["roll0"]["operands"] == ["roll1"]
        assert rolls["roll1"]["outcomes"] == [1, 2, 3]

    def test_invalid_selection_fails_when_rolled(self) -> None:
        selected = PRoller(P(2)).select(1)

        with pytest.raises(RollError) as caught:
            selected.roll()

        assert isinstance(caught.value.__cause__, IndexError)

    def test_empty_selection_has_empty_sum_distribution(self) -> None:
        pool = PRoller(P(H({1: 1})), name="pool")

        assert pool.select(slice(0)).sum().h() == H({})

    def test_empty_p_produces_no_rolls(self) -> None:
        pool = PRoller(P())
        summed = pool.sum()

        assert_type(pool, PRoller[Never])  # zuban: ignore[misc]
        assert_type(summed, SingleOutcomeRoller[Never])  # zuban: ignore[misc]
        assert list(pool.rolls_with_counts()) == []
        assert pool.h() == H({})
        assert summed.h() == H({})
        assert summed.metadata() == {"kind": "pool-sum"}


class TestRollerPool:
    def test_composes_single_rollers(self) -> None:
        two = LiteralRoller(2)
        one = LiteralRoller(1)
        pool = RollerPool(two, one, name="pool")
        roll = pool.roll()

        assert_type(pool, RollerPool[int])
        assert isinstance(pool, MultiOutcomeRoller)
        assert len(pool) == 2
        assert pool.rollers == (two, one)
        assert pool.operands == (two, one)
        assert pool.h() == H({3: 1})
        assert list(pool.rolls_with_counts()) == [((1, 2), 1)]
        assert roll.outcomes == (1, 2)
        assert tuple(operand.roller for operand in roll.operands) == (one, two)
        assert pool.metadata() == {"kind": "pool", "name": "pool"}

    def test_reused_single_roller_produces_independent_rolls(self) -> None:
        d6 = HRoller(H(6), name="d6")
        trace = RollerPool(d6, d6).roll().trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert isinstance(rollers, dict)
        assert isinstance(rolls, dict)
        assert rollers["roller0"] == {
            "kind": "pool",
            "operands": ["roller1", "roller1"],
        }
        assert rolls["roll0"]["operands"] == ["roll1", "roll2"]

    def test_selection_distribution_uses_each_source_roller_distribution(
        self,
    ) -> None:
        d2 = HRoller(H(2), name="d2")
        d3 = HRoller(H(3), name="d3")
        pool = RollerPool(d2, d3)

        assert pool.select(-1).sum().h() == H({1: 1, 2: 3, 3: 2})

    def test_roll_uses_natural_order_for_incomparable_outcomes(self) -> None:
        pool = RollerPool(
            HRoller(H({2j: 1})),
            HRoller(H({1j: 1})),
        )

        assert pool.roll().outcomes == (1j, 2j)

    def test_empty_pool_produces_no_rolls(self) -> None:
        pool: RollerPool[Never] = RollerPool()

        assert_type(pool, RollerPool[Never])
        assert list(pool.rolls_with_counts()) == []
        assert pool.h() == H({})
        assert pool.sum().h() == H({})

    def test_impossible_pool_produces_no_rolls_but_remains_an_empty_distribution(
        self,
    ) -> None:
        impossible_pool = RollerPool(HRoller(H({}))).select(slice(0))

        assert list(impossible_pool.rolls_with_counts()) == []
        assert impossible_pool.h() == H({})
        assert impossible_pool.sum().h() == H({})


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

    def test_operands(self) -> None:
        literal_roller = LiteralRoller(3)

        @roller_factory
        def factory() -> SingleOutcomeRoller[int]:
            return literal_roller

        assert factory().operands == (literal_roller,)

    def test_h(self) -> None:
        d6 = H(6)

        @roller_factory
        def factory() -> SingleOutcomeRoller[int]:
            return HRoller(d6)

        assert factory().h() == d6

    def test_returning_non_roller_raises(self) -> None:
        @roller_factory
        def invalid_factory() -> SingleOutcomeRoller[int]:
            return cast("Any", "not_a_roller")  # type: ignore[no-any-return]

        with pytest.raises(
            TypeError, match="must return a SingleOutcomeRoller or MultiOutcomeRoller"
        ):
            invalid_factory()


class TestMultiOutcomeFactoryRoller:
    def test_callables(self) -> None:
        class RollerFactories:
            @roller_factory()
            def factory(self, n: int) -> MultiOutcomeRoller[int]:
                return PRoller(n @ P(2))

            def __call__(self, first: int, second: int) -> MultiOutcomeRoller[int]:
                return RollerPool(LiteralRoller(first), LiteralRoller(second))

        some_rollers = RollerFactories()
        returned_roller = some_rollers.factory(2)
        assert_type(returned_roller, MultiOutcomeRoller[int])
        assert isinstance(returned_roller, _MultiOutcomeFactoryRoller)
        assert len(returned_roller.roll().outcomes) == 2

        callable_factory = roller_factory(some_rollers)
        callable_roller = callable_factory(3, 4)
        assert_type(callable_roller, MultiOutcomeRoller[int])
        assert isinstance(callable_roller, _MultiOutcomeFactoryRoller)
        assert callable_roller.metadata()["name"] == "RollerFactories"
        assert callable_roller.roll().outcomes == (3, 4)

        bound_factory = roller_factory(partial(some_rollers, 5, 6), name="bound")
        bound_roller = bound_factory()
        assert isinstance(bound_roller, _MultiOutcomeFactoryRoller)
        assert bound_roller.metadata()["name"] == "bound"
        assert bound_roller.roll().outcomes == (5, 6)

    def test_implicit_name_uses_factory_name(self) -> None:
        @roller_factory
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == factory.__name__

    @pytest.mark.parametrize("name", ["explicit_name", ""])
    def test_explicit_name_preserved(self, name: str) -> None:
        @roller_factory(name=name)
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == name

    def test_operands(self) -> None:
        p_roller = PRoller(P(2))

        @roller_factory
        def factory() -> MultiOutcomeRoller[int]:
            return p_roller

        assert factory().operands == (p_roller,)

    def test_h(self) -> None:
        p3d6 = 3 @ P(6)

        @roller_factory
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(p3d6)

        assert factory().h() == p3d6.h()

    def test_rolls_with_counts(self) -> None:
        p2d2 = 2 @ P(2)

        @roller_factory
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(p2d2)

        assert sorted(factory().rolls_with_counts()) == sorted(p2d2.rolls_with_counts())


class TestSingleOutcomeRoll:
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
            "kind": "binary",
            "operator": name,
            "operands": ["roller1", "roller2"],
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["operands"] == ["roll1", "roll2"]

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
            "kind": "unary",
            "operator": name,
            "operands": ["roller1"],
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["operands"] == ["roll1"]

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
        assert separate_rolls["roll0"]["operands"] == ["roll1", "roll2"]
        assert reused_rolls["roll0"]["operands"] == ["roll1", "roll1"]


class TestMultiOutcomeRoll:
    def test_sum_produces_single_outcome_roll(self) -> None:
        pool_roll = PRoller(P(H({"a": 1}), H({"b": 1})), name="pool").roll()
        roll = pool_roll.sum()

        assert_type(roll, SingleOutcomeRoll[str])  # zuban: ignore[misc]
        assert roll.outcome == "ab"
        assert roll.operands == (pool_roll,)

    def test_empty_sum_raises(self) -> None:
        pool_roll: MultiOutcomeRoll[Never] = MultiOutcomeRoll((), PRoller(P()))

        assert_type(pool_roll, MultiOutcomeRoll[Never])
        with pytest.raises(ValueError, match="no outcomes to sum"):
            pool_roll.sum()


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
        make_roller: Callable[[], SingleOutcomeRoller[int] | MultiOutcomeRoller[int]],
        make_roll: Callable[[], SingleOutcomeRoll[int] | MultiOutcomeRoll[int]],
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
        assert result.operands[0] is left_roll
        assert result.operands[1].roller is right_roller
        assert result.roller.operands[0] is left_roller
        assert result.roller.operands[1] is right_roller
        assert rerolled_result.outcome == second + 2
        assert choices.call_count == 2


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
    def test_empty_pool_roll_raises(
        self, make_pool: Callable[[], MultiOutcomeRoller[int]]
    ) -> None:
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
        assert rollers["roller0"]["operator"] == "sub"

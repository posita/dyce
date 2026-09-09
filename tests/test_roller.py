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
from unittest.mock import patch

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
)

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


class TestSingleOutcomeRoller:
    def test_binary_operator_types(self) -> None:
        d6 = HRoller(H(6), name="d6")
        power_roller = HRoller(H({_PowerOutcome(2): 1}))

        assert_type(d6 + H(6), SingleOutcomeRoller[int])
        assert_type(d6 + P(6), SingleOutcomeRoller[int])
        assert_type(d6 - H(6), SingleOutcomeRoller[int])
        assert_type(d6 - P(6), SingleOutcomeRoller[int])
        assert_type(d6 * H(2), SingleOutcomeRoller[int])
        assert_type(d6 / H(2), SingleOutcomeRoller[float])
        assert_type(d6 // H(2), SingleOutcomeRoller[int])
        assert_type(d6 % H(2), SingleOutcomeRoller[int])
        assert_type(power_roller**2, SingleOutcomeRoller[_PowerOutcome])
        assert_type(d6 << H(2), SingleOutcomeRoller[int])
        assert_type(d6 >> H(2), SingleOutcomeRoller[int])
        assert_type(d6 & H(2), SingleOutcomeRoller[int])
        assert_type(d6 | H(2), SingleOutcomeRoller[int])
        assert_type(d6 ^ H(2), SingleOutcomeRoller[int])

        assert_type(2 * d6, SingleOutcomeRoller[int])
        assert_type(12 / d6, SingleOutcomeRoller[float])
        assert_type(12 // d6, SingleOutcomeRoller[int])
        assert_type(12 % d6, SingleOutcomeRoller[int])
        assert_type(2**power_roller, SingleOutcomeRoller[_PowerOutcome])
        assert_type(2 << d6, SingleOutcomeRoller[int])
        assert_type(12 >> d6, SingleOutcomeRoller[int])
        assert_type(2 & d6, SingleOutcomeRoller[int])
        assert_type(2 | d6, SingleOutcomeRoller[int])
        assert_type(2 ^ d6, SingleOutcomeRoller[int])

    def test_unary_operator_types(self) -> None:
        roller = LiteralRoller(-2)

        assert_type(-roller, SingleOutcomeRoller[int])
        assert_type(+roller, SingleOutcomeRoller[int])
        assert_type(abs(roller), SingleOutcomeRoller[int])
        assert_type(~roller, SingleOutcomeRoller[int])

    def test_hable_forward_addition_defers_to_roller(self) -> None:
        d6 = HRoller(H(6), name="d6")

        assert H(6).__add__(d6) is NotImplemented
        assert P(6).__add__(d6) is NotImplemented

    def test_hable_forward_subtraction_defers_to_roller(self) -> None:
        d6 = HRoller(H(6), name="d6")

        assert H(6).__sub__(d6) is NotImplemented
        assert P(6).__sub__(d6) is NotImplemented

    def test_hable_addition_is_symmetric(self) -> None:
        d6 = HRoller(H(6), name="d6")

        assert isinstance(d6 + H(6), SingleOutcomeRoller)
        assert isinstance(H(6) + d6, SingleOutcomeRoller)
        assert isinstance(d6 + P(6), SingleOutcomeRoller)
        assert isinstance(P(6) + d6, SingleOutcomeRoller)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (H(6) + d6).h() == 2 @ H(6)
        assert (d6 + P(6)).h() == 2 @ H(6)
        assert (P(6) + d6).h() == 2 @ H(6)

    def test_hable_subtraction_preserves_operand_order(self) -> None:
        d6 = HRoller(H(6), name="d6")
        two = H({2: 1})

        assert isinstance(d6 - two, SingleOutcomeRoller)
        assert isinstance(d6 - P(4), SingleOutcomeRoller)
        assert (d6 - two).h() == H(6) - 2
        assert (two - d6).h() == 2 - H(6)
        assert (d6 - P(4)).h() == H(6) - H(4)
        assert (P(4) - d6).h() == H(4) - H(6)

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_hable_ordering(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_h = H({lhs: 1})
        right_h = H({rhs: 1})
        left_p = P(left_h)
        right_p = P(right_h)
        left_roller = LiteralRoller(lhs)
        right_roller = LiteralRoller(rhs)
        combined = op(left_roller, right_roller)
        expected_h = H({op(lhs, rhs): 1})

        assert op(left_roller, right_h).h() == expected_h
        assert op(left_h, right_roller).h() == expected_h
        assert op(left_roller, right_p).h() == expected_h
        assert op(left_p, right_roller).h() == expected_h
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

    def test_hable_promotion_is_lazy(self) -> None:
        d6 = HRoller(H(6), name="d6")
        hable = _Hable(H(6))

        with patch.object(hable, "h", wraps=hable.h) as h:
            combined = d6 + hable
            h.assert_not_called()
            assert isinstance(combined.operands[1], HableRoller)
            assert combined.h() == 2 @ H(6)
            h.assert_called_once_with()

    def test_hable_promotion_supports_rolls_and_trace(self) -> None:
        hable = _Hable(H(6))

        with patch.object(hable, "h", wraps=hable.h) as h:
            roll = (HRoller(H(6), name="d6") + hable).roll()
            h.assert_called_once_with()

        trace = roll.trace()
        rollers = trace["rollers"]

        assert roll.outcome in 2 @ H(6)
        assert isinstance(rollers, dict)
        assert rollers["roller2"] == {"kind": "source", "name": str(hable)}

    def test_mixed_roller_addition(self) -> None:
        roll = (HRoller(H({1: 1}), name="one") + LiteralRoller(2)).roll()

        assert roll.outcome == 3
        assert json.loads(json.dumps(roll.trace())) == roll.trace()

    def test_raw_histograms_are_promoted_to_named_sources(self) -> None:
        combined = HRoller(H(6), name="d6") + H(8)
        promoted = combined.operands[1]

        assert promoted.metadata() == {"kind": "source", "name": str(H(8))}


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


class TestPRoller:
    def test_is_hable_as_aggregate_distribution(self) -> None:
        p = P(H({1: 1}), H({2: 1}))
        pool = PRoller(p, name="pool")

        assert isinstance(pool, HableT)
        assert pool.h() == p.h()

    def test_binary_operator_types(self) -> None:
        left = PRoller(P(H({2: 1})), name="left")
        right = PRoller(P(H({3: 1})), name="right")
        single = HRoller(H({5: 1}), name="single")
        power_pool = PRoller(P(H({_PowerOutcome(2): 1})), name="power_pool")

        assert_type(left + right, SingleOutcomeRoller[int])
        assert_type(left + single, SingleOutcomeRoller[int])
        assert_type(single + left, SingleOutcomeRoller[int])
        assert_type(left + P(H({5: 1})), SingleOutcomeRoller[int])
        assert_type(left - right, SingleOutcomeRoller[int])
        assert_type(right - left, SingleOutcomeRoller[int])
        assert_type(10 - left, SingleOutcomeRoller[int])
        assert_type(left * 2, SingleOutcomeRoller[int])
        assert_type(left / 2, SingleOutcomeRoller[float])
        assert_type(left // 2, SingleOutcomeRoller[int])
        assert_type(left % 2, SingleOutcomeRoller[int])
        assert_type(power_pool**2, SingleOutcomeRoller[_PowerOutcome])
        assert_type(left << 2, SingleOutcomeRoller[int])
        assert_type(left >> 2, SingleOutcomeRoller[int])
        assert_type(left & 2, SingleOutcomeRoller[int])
        assert_type(left | 2, SingleOutcomeRoller[int])
        assert_type(left ^ 2, SingleOutcomeRoller[int])

        assert_type(2 * left, SingleOutcomeRoller[int])
        assert_type(12 / left, SingleOutcomeRoller[float])
        assert_type(12 // left, SingleOutcomeRoller[int])
        assert_type(12 % left, SingleOutcomeRoller[int])
        assert_type(2**power_pool, SingleOutcomeRoller[_PowerOutcome])
        assert_type(2 << left, SingleOutcomeRoller[int])
        assert_type(12 >> left, SingleOutcomeRoller[int])
        assert_type(2 & left, SingleOutcomeRoller[int])
        assert_type(2 | left, SingleOutcomeRoller[int])
        assert_type(2 ^ left, SingleOutcomeRoller[int])

    def test_addition_aggregates_pool_operands(self) -> None:
        left = PRoller(P(H({1: 1}), H({2: 1})), name="left")
        right = PRoller(P(H({3: 1}), H({4: 1})), name="right")
        single = HRoller(H({5: 1}), name="single")

        assert (left + right).h() == H({10: 1})
        assert (left + single).h() == H({8: 1})
        assert (single + left).h() == H({8: 1})
        assert (left + P(H({5: 1}))).h() == H({8: 1})
        assert (P(H({5: 1})) + left).h() == H({8: 1})

    def test_subtraction_aggregates_pools_and_preserves_order(self) -> None:
        left = PRoller(P(H({1: 1}), H({2: 1})), name="left")
        right = PRoller(P(H({3: 1}), H({4: 1})), name="right")

        assert (left - right).h() == H({-4: 1})
        assert (right - left).h() == H({4: 1})
        assert (10 - left).h() == H({7: 1})

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_aggregate_pools(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left = PRoller(P(H({lhs: 1})), name="left")
        right = PRoller(P(H({rhs: 1})), name="right")
        expected = H({op(lhs, rhs): 1})
        combined = op(left, right)

        assert combined.h() == expected
        assert combined.metadata() == {"kind": "binary", "operator": name}
        assert op(lhs, right).h() == expected
        assert op(P(H({lhs: 1})), right).h() == expected
        assert op(left, P(H({rhs: 1}))).h() == expected

    def test_unary_operator_types_and_distributions(self) -> None:
        pool = PRoller(P(H({-2: 1})), name="pool")

        assert_type(-pool, SingleOutcomeRoller[int])
        assert_type(+pool, SingleOutcomeRoller[int])
        assert_type(abs(pool), SingleOutcomeRoller[int])
        assert_type(~pool, SingleOutcomeRoller[int])
        assert (-pool).h() == H({2: 1})
        assert (+pool).h() == H({-2: 1})
        assert abs(pool).h() == H({2: 1})
        assert (~pool).h() == H({1: 1})

    def test_raw_pool_promotion_preserves_pool_trace(self) -> None:
        combined = HRoller(H({1: 1}), name="one") + P(H({2: 1}), H({3: 1}))
        trace = combined.roll().trace()
        rollers = trace["rollers"]

        assert isinstance(rollers, dict)
        assert rollers["roller2"] == {
            "kind": "pool-sum",
            "operands": ["roller3"],
        }
        assert rollers["roller3"]["kind"] == "pool-source"

    def test_roll_delegates_to_p(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = P(H({2: 1}), H({1: 1}))

        def p_roll(source: P[int]) -> tuple[int, ...]:
            assert source is p
            return (1, 2)

        monkeypatch.setattr(P, "roll", p_roll)
        pool = PRoller(p, name="pool")
        roll = pool.roll()

        assert_type(pool, PRoller[int])
        assert_type(roll, MultiOutcomeRoll[int])
        assert pool.p is p
        assert pool.metadata()["name"] == "pool"
        assert pool.operands == ()
        assert roll.outcomes == (1, 2)
        assert roll.roller is pool
        assert roll.operands == ()

    def test_roll_uses_natural_order_for_incomparable_outcomes(self) -> None:
        pool = PRoller(P(H({2j: 1}), H({1j: 1})))

        assert pool.roll().outcomes == (1j, 2j)

    def test_rolls_with_counts_delegates_to_p(self) -> None:
        p = P(H(2), H(3))

        assert list(PRoller(p).rolls_with_counts()) == list(p.rolls_with_counts())

    def test_sum_bridges_to_single_roller(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1})), name="pool")
        summed = pool.sum()

        assert_type(summed, SingleOutcomeRoller[int])
        assert summed.h() == H({3: 1})
        assert_type(summed.roll(), SingleOutcomeRoll[int])
        assert summed.roll().outcome == 3

    def test_select_creates_deferred_pool_roller(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        selected = pool.select(-1, 0)
        roll = selected.roll()
        trace = roll.trace()
        rollers = trace["rollers"]
        rolls = trace["rolls"]

        assert_type(selected, MultiOutcomeRoller[int])
        assert roll.outcomes == (3, 1)
        assert isinstance(rollers, dict)
        assert rollers["roller0"] == {
            "kind": "pool-selection",
            "positions": [2, 0],
            "operands": ["roller1"],
        }
        assert isinstance(rolls, dict)
        assert rolls["roll0"]["outcomes"] == [3, 1]
        assert rolls["roll0"]["operands"] == ["roll1"]
        assert rolls["roll1"]["outcomes"] == [1, 2, 3]

    def test_nested_selection_uses_positions_from_selected_pool(self) -> None:
        p = 3 @ P(2)
        selected = PRoller(p, name="pool").select(-1, 0).select(1)

        assert len(selected) == 1
        assert selected.sum().h() == p.at(0)

    def test_empty_selection_has_empty_sum_distribution(self) -> None:
        pool = PRoller(P(H({1: 1})), name="pool")

        assert pool.select(slice(0)).sum().h() == H({})

    def test_empty_pool_is_one_possible_empty_roll(self) -> None:
        pool = PRoller(P())
        summed = pool.sum()

        assert_type(pool, PRoller[Never])
        assert_type(summed, SingleOutcomeRoller[Never])
        assert list(pool.rolls_with_counts()) == [((), 1)]
        assert pool.h() == H({})
        assert summed.h() == H({})
        assert summed.metadata() == {"kind": "pool-sum"}

    def test_at_composes_selection_and_sum(self) -> None:
        pool = PRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")

        assert_type(pool.at(-1, 0), SingleOutcomeRoller[int])
        assert pool.at(-1, 0).h() == H({4: 1})
        assert pool.at(-1, 0).roll().outcome == 4


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

    def test_reused_roller_has_one_roller_and_independent_rolls(self) -> None:
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

    def test_selection_uses_composite_pool_distribution(self) -> None:
        d2 = HRoller(H(2), name="d2")
        d3 = HRoller(H(3), name="d3")
        pool = RollerPool(d2, d3)

        assert pool.select(-1).sum().h() == P(H(2), H(3)).at(-1)

    def test_sum_preserves_string_outcomes(self) -> None:
        pool = RollerPool(LiteralRoller("a"), LiteralRoller("b"))

        assert_type(pool.sum(), SingleOutcomeRoller[str])
        assert_type(pool.roll().sum(), SingleOutcomeRoll[str])
        assert pool.sum().h() == H({"ab": 1})
        assert pool.roll().sum().outcome == "ab"

    def test_roll_uses_natural_order_for_incomparable_outcomes(self) -> None:
        pool = RollerPool(
            HRoller(H({2j: 1})),
            HRoller(H({1j: 1})),
        )

        assert pool.roll().outcomes == (1j, 2j)

    def test_empty_pool_is_one_possible_empty_roll(self) -> None:
        pool: RollerPool[Never] = RollerPool()

        assert_type(pool, RollerPool[Never])
        assert list(pool.rolls_with_counts()) == [((), 1)]
        assert pool.h() == H({})
        assert pool.sum().h() == H({})

    def test_impossible_pool_remains_an_empty_distribution(self) -> None:
        impossible_pool = RollerPool(HRoller(H({}))).select(slice(0))

        assert len(impossible_pool) == 0
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

    def test_implicit_name(self) -> None:
        @roller_factory
        def factory() -> SingleOutcomeRoller[int]:
            return LiteralRoller(3)

        assert factory().metadata()["name"] == factory.__name__

    def test_explicit_name(self) -> None:
        @roller_factory(name="explicit_name")
        def factory() -> SingleOutcomeRoller[int]:
            return LiteralRoller(3)

        assert factory().metadata()["name"] == "explicit_name"

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

    def test_factory_returning_non_roller_raises(self) -> None:
        @roller_factory
        def invalid_factory() -> SingleOutcomeRoller[int]:
            return cast("Any", "not_a_roller")

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
        assert len(returned_roller) == 2

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

    def test_implicit_name(self) -> None:
        @roller_factory
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == factory.__name__

    def test_explicit_name(self) -> None:
        @roller_factory(name="explicit_name")
        def factory() -> MultiOutcomeRoller[int]:
            return PRoller(P(2))

        assert factory().metadata()["name"] == "explicit_name"

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
    def test_roll_binary_operator_types(self) -> None:
        roll = LiteralRoller(2).roll()
        power_roll = HRoller(H({_PowerOutcome(2): 1})).roll()

        assert_type(roll * 2, SingleOutcomeRoll[int])
        assert_type(roll / 2, SingleOutcomeRoll[float])
        assert_type(roll // 2, SingleOutcomeRoll[int])
        assert_type(roll % 2, SingleOutcomeRoll[int])
        assert_type(power_roll**2, SingleOutcomeRoll[_PowerOutcome])
        assert_type(roll << 2, SingleOutcomeRoll[int])
        assert_type(roll >> 2, SingleOutcomeRoll[int])
        assert_type(roll & 2, SingleOutcomeRoll[int])
        assert_type(roll | 2, SingleOutcomeRoll[int])
        assert_type(roll ^ 2, SingleOutcomeRoll[int])

        assert_type(2 * roll, SingleOutcomeRoll[int])
        assert_type(12 / roll, SingleOutcomeRoll[float])
        assert_type(12 // roll, SingleOutcomeRoll[int])
        assert_type(12 % roll, SingleOutcomeRoll[int])
        assert_type(2**power_roll, SingleOutcomeRoll[_PowerOutcome])
        assert_type(2 << roll, SingleOutcomeRoll[int])
        assert_type(12 >> roll, SingleOutcomeRoll[int])
        assert_type(2 & roll, SingleOutcomeRoll[int])
        assert_type(2 | roll, SingleOutcomeRoll[int])
        assert_type(2 ^ roll, SingleOutcomeRoll[int])

    def test_unary_operator_types(self) -> None:
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

    def test_literal_plus_roll_is_serializable(self) -> None:
        roll = 2 + HRoller(H(6), name="d6").roll()

        assert roll.outcome in 2 + H(6)
        assert json.loads(json.dumps(roll.trace())) == roll.trace()

    def test_trace_distinguishes_independent_and_shared_rolls(self) -> None:
        d6 = HRoller(H(6), name="d6")
        independent = d6.roll() + d6.roll()
        shared_source = d6.roll()
        shared = shared_source + shared_source

        independent_trace = independent.trace()
        shared_trace = shared.trace()
        assert independent_trace["root"] == "roll0"
        assert shared_trace["root"] == "roll0"
        independent_rolls = independent_trace["rolls"]
        shared_rolls = shared_trace["rolls"]
        independent_rollers = independent_trace["rollers"]
        shared_rollers = shared_trace["rollers"]

        assert isinstance(independent_rolls, dict)
        assert isinstance(shared_rolls, dict)
        assert isinstance(independent_rollers, dict)
        assert isinstance(shared_rollers, dict)
        assert independent_rolls["roll0"]["roller"] == "roller0"
        assert shared_rolls["roll0"]["roller"] == "roller0"
        assert independent_rolls["roll0"]["operands"] == ["roll1", "roll2"]
        assert shared_rolls["roll0"]["operands"] == ["roll1", "roll1"]
        assert independent_rollers["roller0"]["operands"] == ["roller1", "roller1"]
        assert shared_rollers["roller0"]["operands"] == ["roller1", "roller1"]


class TestMultiOutcomeRoll:
    def test_sum_bridges_to_single_roll(self) -> None:
        pool_roll = PRoller(P(H({1: 1}), H({2: 1})), name="pool").roll()
        roll = pool_roll.sum()

        assert_type(roll, SingleOutcomeRoll[int])
        assert roll.outcome == 3
        assert roll.operands == (pool_roll,)

    def test_empty_sum_raises(self) -> None:
        pool_roll: MultiOutcomeRoll[Never] = MultiOutcomeRoll((), PRoller(P()))

        assert_type(pool_roll, MultiOutcomeRoll[Never])
        with pytest.raises(ValueError, match="no outcomes to sum"):
            pool_roll.sum()


class TestMixedRollArithmetic:
    def test_mixed_operator_types(self) -> None:
        single = LiteralRoller(4)
        multi = PRoller(P(H({1: 1}), H({3: 1})))
        single_roll = LiteralRoller(9).roll()
        multi_roll = PRoller(P(H({2: 1}), H({7: 1}))).roll()

        assert_type(single + single_roll, SingleOutcomeRoller[int])
        assert_type(single_roll + single, SingleOutcomeRoller[int])
        assert_type(single + multi_roll, SingleOutcomeRoller[int])
        assert_type(multi_roll + single, SingleOutcomeRoller[int])
        assert_type(multi + single_roll, SingleOutcomeRoller[int])
        assert_type(single_roll + multi, SingleOutcomeRoller[int])
        assert_type(multi + multi_roll, SingleOutcomeRoller[int])
        assert_type(multi_roll + multi, SingleOutcomeRoller[int])
        assert_type(single_roll + multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll + single_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll + multi_roll, SingleOutcomeRoll[int])

        assert_type(single - single_roll, SingleOutcomeRoller[int])
        assert_type(single_roll - single, SingleOutcomeRoller[int])
        assert_type(single - multi_roll, SingleOutcomeRoller[int])
        assert_type(multi_roll - single, SingleOutcomeRoller[int])
        assert_type(multi - single_roll, SingleOutcomeRoller[int])
        assert_type(single_roll - multi, SingleOutcomeRoller[int])
        assert_type(multi - multi_roll, SingleOutcomeRoller[int])
        assert_type(multi_roll - multi, SingleOutcomeRoller[int])
        assert_type(single_roll - multi_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll - single_roll, SingleOutcomeRoll[int])
        assert_type(multi_roll - multi_roll, SingleOutcomeRoll[int])

    @pytest.mark.parametrize("op", [operator.add, operator.sub], ids=["add", "sub"])
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
    def test_roller_and_roll(
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

        assert isinstance(combined, SingleOutcomeRoller)
        assert combined.roll().outcome == (op(9, 4) if reverse else op(4, 9))

    @pytest.mark.parametrize("op", [operator.add, operator.sub], ids=["add", "sub"])
    @pytest.mark.parametrize(
        ("left_multi", "right_multi"),
        [(False, True), (True, False), (True, True)],
        ids=["single-multi", "multi-single", "multi-multi"],
    )
    def test_rolls_with_multi_outcomes(
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


class TestRollerRollEquivalence:
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

        deferred_roll = op(left_roller, right_roller).roll()
        realized_roll = op(left_roller.roll(), right_roller.roll())
        reflected_deferred_roll = op(lhs, right_roller).roll()
        reflected_realized_roll = op(lhs, right_roller.roll())

        assert deferred_roll.trace() == realized_roll.trace()
        assert reflected_deferred_roll.trace() == reflected_realized_roll.trace()

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

        deferred_roll = pool.select(-1, 0).sum().roll()
        realized_roll = pool.select(-1, 0).roll().sum()

        assert deferred_roll.trace() == realized_roll.trace()

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

    def test_addition(self, monkeypatch: pytest.MonkeyPatch) -> None:
        d6 = HRoller(H(6), name="d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 + d6).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() + d6.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.trace() == realized_roll.trace()

    def test_subtraction(self, monkeypatch: pytest.MonkeyPatch) -> None:
        d6 = HRoller(H(6), name="d6")
        d4 = HRoller(H(4), name="d4")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 - d4).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() - d4.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.trace() == realized_roll.trace()
        rollers = deferred_roll.trace()["rollers"]
        assert isinstance(rollers, dict)
        assert rollers["roller0"]["operator"] == "sub"

    def test_reflected_subtraction_preserves_operand_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (2 - d6).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = 2 - d6.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.trace() == realized_roll.trace()

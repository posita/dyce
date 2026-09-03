# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import json
import operator
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar, assert_type

import pytest

from dyce import H, HableT, P, rng
from dyce.roller import (
    HableRoller,
    HRoller,
    LiteralRoller,
    PoolRoll,
    PoolRoller,
    Roll,
    Roller,
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
class _AdditionCountingOutcome:
    value: int
    times_added: ClassVar[int] = 0

    def __add__(self, other: "_AdditionCountingOutcome") -> "_AdditionCountingOutcome":
        type(self).times_added += 1
        return _AdditionCountingOutcome(self.value + other.value)


class _ConstantRoller(Roller[int]):
    def __init__(self, value: int) -> None:
        self._value = value

    def h(self) -> H[int]:
        return H({self._value: 1})

    def roll(self) -> Roll[int]:
        return Roll(self._value, self)

    def provenance(self) -> dict[str, object]:
        return {"kind": "constant", "value": self._value}


class _CountingHable(HableT[int]):
    def __init__(self, h: H[int]) -> None:
        self._h = h
        self.h_calls = 0

    def h(self) -> H[int]:
        self.h_calls += 1
        return self._h


@dataclass(frozen=True)
class _PowerOutcome:
    value: int

    def __pow__(self, rhs: int) -> "_PowerOutcome":
        return _PowerOutcome(self.value**rhs)

    def __rpow__(self, lhs: int) -> "_PowerOutcome":
        return _PowerOutcome(lhs**self.value)


class TestRoller:
    def test_binary_operator_types(self) -> None:
        d6 = HRoller(H(6), name="d6")
        power_roller = HRoller(H({_PowerOutcome(2): 1}))

        assert_type(d6 + H(6), Roller[int])
        assert_type(d6 + P(6), Roller[int])
        assert_type(d6 - H(6), Roller[int])
        assert_type(d6 - P(6), Roller[int])
        assert_type(d6 * H(2), Roller[int])
        assert_type(d6 / H(2), Roller[float])
        assert_type(d6 // H(2), Roller[int])
        assert_type(d6 % H(2), Roller[int])
        assert_type(power_roller**2, Roller[_PowerOutcome])
        assert_type(d6 << H(2), Roller[int])
        assert_type(d6 >> H(2), Roller[int])
        assert_type(d6 & H(2), Roller[int])
        assert_type(d6 | H(2), Roller[int])
        assert_type(d6 ^ H(2), Roller[int])

        assert_type(2 * d6, Roller[int])
        assert_type(12 / d6, Roller[float])
        assert_type(12 // d6, Roller[int])
        assert_type(12 % d6, Roller[int])
        assert_type(2**power_roller, Roller[_PowerOutcome])
        assert_type(2 << d6, Roller[int])
        assert_type(12 >> d6, Roller[int])
        assert_type(2 & d6, Roller[int])
        assert_type(2 | d6, Roller[int])
        assert_type(2 ^ d6, Roller[int])

    def test_unary_operator_types(self) -> None:
        roller = _ConstantRoller(-2)

        assert_type(-roller, Roller[int])
        assert_type(+roller, Roller[int])
        assert_type(abs(roller), Roller[int])
        assert_type(~roller, Roller[int])

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

        assert isinstance(d6 + H(6), Roller)
        assert isinstance(H(6) + d6, Roller)
        assert isinstance(d6 + P(6), Roller)
        assert isinstance(P(6) + d6, Roller)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (H(6) + d6).h() == 2 @ H(6)
        assert (d6 + P(6)).h() == 2 @ H(6)
        assert (P(6) + d6).h() == 2 @ H(6)

    def test_hable_subtraction_preserves_operand_order(self) -> None:
        d6 = HRoller(H(6), name="d6")
        two = H({2: 1})

        assert isinstance(d6 - two, Roller)
        assert isinstance(d6 - P(4), Roller)
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
        left_roller = _ConstantRoller(lhs)
        right_roller = _ConstantRoller(rhs)
        combined = op(left_roller, right_roller)
        expected_h = H({op(lhs, rhs): 1})

        assert op(left_roller, right_h).h() == expected_h
        assert op(left_h, right_roller).h() == expected_h
        assert op(left_roller, right_p).h() == expected_h
        assert op(left_p, right_roller).h() == expected_h
        assert combined.h() == expected_h
        assert combined.provenance() == {"kind": "binary", "operator": name}
        assert combined.operands == (left_roller, right_roller)

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_distributions_and_provenance(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        roller = _ConstantRoller(value)
        combined = op(roller)
        expected_h = H({op(value): 1})

        assert combined.h() == expected_h
        assert combined.provenance() == {"kind": "unary", "operator": name}
        assert combined.operands == (roller,)

    def test_hable_promotion_is_lazy(self) -> None:
        d6 = HRoller(H(6), name="d6")
        hable = _CountingHable(H(6))

        combined = d6 + hable

        assert hable.h_calls == 0
        assert isinstance(combined.operands[1], HableRoller)
        assert combined.h() == 2 @ H(6)
        assert hable.h_calls == 1

    def test_hable_promotion_supports_rolls_and_provenance(self) -> None:
        hable = _CountingHable(H(6))

        roll = (HRoller(H(6), name="d6") + hable).roll()
        provenance = roll.to_dict()
        definitions = provenance["definitions"]

        assert roll.outcome in 2 @ H(6)
        assert hable.h_calls == 1
        assert isinstance(definitions, dict)
        assert definitions["d2"] == {"kind": "source", "name": str(hable)}

    def test_mixed_roller_addition(self) -> None:
        roll = (HRoller(H({1: 1}), name="one") + _ConstantRoller(2)).roll()

        assert roll.outcome == 3
        assert json.loads(json.dumps(roll.to_dict())) == roll.to_dict()

    def test_raw_histograms_are_promoted_to_named_sources(self) -> None:
        combined = HRoller(H(6), name="d6") + H(8)
        promoted = combined.operands[1]

        assert promoted.provenance() == {"kind": "source", "name": str(H(8))}


class TestHRoller:
    def test_addition_preserves_distribution(self) -> None:
        d6 = HRoller(H(6), name="d6")

        assert d6.name == "d6"
        assert (d6 + d6).h() == 2 @ H(6)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (d6 + 2).h() == H(6) + 2
        assert (2 + d6).h() == 2 + H(6)

    def test_distribution_is_computed_lazily(self) -> None:
        _AdditionCountingOutcome.times_added = 0
        source = HRoller(H({_AdditionCountingOutcome(1): 1}), name="source")
        combined = source + source

        assert _AdditionCountingOutcome.times_added == 0
        assert combined.h() == H({_AdditionCountingOutcome(2): 1})
        assert _AdditionCountingOutcome.times_added == 1


class TestHableRoller:
    def test_exposes_hable_source(self) -> None:
        hable = _CountingHable(H(6))
        roller = HableRoller(hable, name="d6")

        assert_type(roller, HableRoller[int])
        assert roller.hable is hable
        assert roller.name == "d6"
        assert roller.h() == H(6)
        assert roller.provenance() == {"kind": "source", "name": "d6"}

    def test_uses_hable_representation_as_default_name(self) -> None:
        hable = _CountingHable(H(6))
        roller = HableRoller(hable)

        assert roller.name is None
        assert roller.provenance() == {"kind": "source", "name": str(hable)}


class TestLiteralRoller:
    def test_exposes_and_rolls_value(self) -> None:
        roller = LiteralRoller(3)
        roll = roller.roll()

        assert_type(roller, LiteralRoller[int])
        assert roller.value == 3
        assert roller.h() == H({3: 1})
        assert roller.provenance() == {"kind": "literal", "value": 3}
        assert roll.outcome == 3
        assert roll.roller is roller


class TestPoolRoller:
    def test_is_hable_as_aggregate_distribution(self) -> None:
        p = P(H({1: 1}), H({2: 1}))
        pool = PoolRoller(p, name="pool")

        assert isinstance(pool, HableT)
        assert pool.h() == p.h()

    def test_binary_operator_types(self) -> None:
        left = PoolRoller(P(H({2: 1})), name="left")
        right = PoolRoller(P(H({3: 1})), name="right")
        scalar = HRoller(H({5: 1}), name="scalar")
        power_pool = PoolRoller(P(H({_PowerOutcome(2): 1})), name="power_pool")

        assert_type(left + right, Roller[int])
        assert_type(left + scalar, Roller[int])
        assert_type(scalar + left, Roller[int])
        assert_type(left + P(H({5: 1})), Roller[int])
        assert_type(left - right, Roller[int])
        assert_type(right - left, Roller[int])
        assert_type(10 - left, Roller[int])
        assert_type(left * 2, Roller[int])
        assert_type(left / 2, Roller[float])
        assert_type(left // 2, Roller[int])
        assert_type(left % 2, Roller[int])
        assert_type(power_pool**2, Roller[_PowerOutcome])
        assert_type(left << 2, Roller[int])
        assert_type(left >> 2, Roller[int])
        assert_type(left & 2, Roller[int])
        assert_type(left | 2, Roller[int])
        assert_type(left ^ 2, Roller[int])

        assert_type(2 * left, Roller[int])
        assert_type(12 / left, Roller[float])
        assert_type(12 // left, Roller[int])
        assert_type(12 % left, Roller[int])
        assert_type(2**power_pool, Roller[_PowerOutcome])
        assert_type(2 << left, Roller[int])
        assert_type(12 >> left, Roller[int])
        assert_type(2 & left, Roller[int])
        assert_type(2 | left, Roller[int])
        assert_type(2 ^ left, Roller[int])

    def test_addition_aggregates_pool_operands(self) -> None:
        left = PoolRoller(P(H({1: 1}), H({2: 1})), name="left")
        right = PoolRoller(P(H({3: 1}), H({4: 1})), name="right")
        scalar = HRoller(H({5: 1}), name="scalar")

        assert (left + right).h() == H({10: 1})
        assert (left + scalar).h() == H({8: 1})
        assert (scalar + left).h() == H({8: 1})
        assert (left + P(H({5: 1}))).h() == H({8: 1})
        assert (P(H({5: 1})) + left).h() == H({8: 1})

    def test_subtraction_aggregates_pools_and_preserves_order(self) -> None:
        left = PoolRoller(P(H({1: 1}), H({2: 1})), name="left")
        right = PoolRoller(P(H({3: 1}), H({4: 1})), name="right")

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
        left = PoolRoller(P(H({lhs: 1})), name="left")
        right = PoolRoller(P(H({rhs: 1})), name="right")
        expected = H({op(lhs, rhs): 1})
        combined = op(left, right)

        assert combined.h() == expected
        assert combined.provenance() == {"kind": "binary", "operator": name}
        assert op(lhs, right).h() == expected
        assert op(P(H({lhs: 1})), right).h() == expected
        assert op(left, P(H({rhs: 1}))).h() == expected

    def test_unary_operator_types_and_distributions(self) -> None:
        pool = PoolRoller(P(H({-2: 1})), name="pool")

        assert_type(-pool, Roller[int])
        assert_type(+pool, Roller[int])
        assert_type(abs(pool), Roller[int])
        assert_type(~pool, Roller[int])
        assert (-pool).h() == H({2: 1})
        assert (+pool).h() == H({-2: 1})
        assert abs(pool).h() == H({2: 1})
        assert (~pool).h() == H({1: 1})

    def test_raw_pool_promotion_preserves_pool_provenance(self) -> None:
        combined = HRoller(H({1: 1}), name="one") + P(H({2: 1}), H({3: 1}))
        provenance = combined.roll().to_dict()
        definitions = provenance["definitions"]

        assert isinstance(definitions, dict)
        assert definitions["d2"] == {
            "kind": "pool-sum",
            "operands": ["d3"],
        }
        assert definitions["d3"]["kind"] == "pool-source"

    def test_roll_preserves_sorted_constituent_outcomes(self) -> None:
        pool = PoolRoller(P(H({2: 1}), H({1: 1})), name="pool")
        roll = pool.roll()

        assert_type(pool, PoolRoller[int])
        assert_type(roll, PoolRoll[int])
        assert pool.p == P(H({2: 1}), H({1: 1}))
        assert pool.name == "pool"
        assert roll.outcomes == (1, 2)
        assert tuple(constituent.outcome for constituent in roll.rolls) == (1, 2)
        assert roll.roller is pool

    def test_roll_uses_natural_order_for_incomparable_outcomes(self) -> None:
        pool = PoolRoller(P(H({2j: 1}), H({1j: 1})))

        assert pool.roll().outcomes == (1j, 2j)

    def test_sum_bridges_to_scalar_roller(self) -> None:
        pool = PoolRoller(P(H({1: 1}), H({2: 1})), name="pool")
        summed = pool.sum()

        assert_type(summed, Roller[int])
        assert summed.h() == H({3: 1})
        assert_type(summed.roll(), Roll[int])
        assert summed.roll().outcome == 3

    def test_select_creates_deferred_pool_definition(self) -> None:
        pool = PoolRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        selected = pool.select(-1, 0)
        roll = selected.roll()
        provenance = roll.to_dict()
        definitions = provenance["definitions"]
        events = provenance["events"]

        assert_type(selected, PoolRoller[int])
        assert roll.outcomes == (3, 1)
        assert isinstance(definitions, dict)
        assert definitions["d0"] == {
            "kind": "pool-selection",
            "positions": [2, 0],
            "operands": ["d1"],
        }
        assert isinstance(events, dict)
        assert events["e0"]["outcomes"] == [3, 1]
        assert events["e0"]["operands"] == ["e1"]
        assert events["e1"]["outcomes"] == [1, 2, 3]

    def test_nested_selection_uses_positions_from_selected_pool(self) -> None:
        pool = PoolRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")
        selected = pool.select(slice(1, None)).select(-1)

        assert selected.name is None
        assert selected.roll().outcomes == (3,)
        assert selected.sum().h() == H({3: 1})

    def test_empty_selection_has_empty_distribution(self) -> None:
        pool = PoolRoller(P(H({1: 1})), name="pool")

        assert pool.select(slice(0)).roll().outcomes == ()
        assert pool.select(slice(0)).sum().h() == H({})

    def test_at_composes_selection_and_sum(self) -> None:
        pool = PoolRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")

        assert_type(pool.at(-1, 0), Roller[int])
        assert pool.at(-1, 0).h() == H({4: 1})
        assert pool.at(-1, 0).roll().outcome == 4


class TestRoll:
    def test_roll_binary_operator_types(self) -> None:
        roll = _ConstantRoller(2).roll()
        power_roll = HRoller(H({_PowerOutcome(2): 1})).roll()

        assert_type(roll * 2, Roll[int])
        assert_type(roll / 2, Roll[float])
        assert_type(roll // 2, Roll[int])
        assert_type(roll % 2, Roll[int])
        assert_type(power_roll**2, Roll[_PowerOutcome])
        assert_type(roll << 2, Roll[int])
        assert_type(roll >> 2, Roll[int])
        assert_type(roll & 2, Roll[int])
        assert_type(roll | 2, Roll[int])
        assert_type(roll ^ 2, Roll[int])

        assert_type(2 * roll, Roll[int])
        assert_type(12 / roll, Roll[float])
        assert_type(12 // roll, Roll[int])
        assert_type(12 % roll, Roll[int])
        assert_type(2**power_roll, Roll[_PowerOutcome])
        assert_type(2 << roll, Roll[int])
        assert_type(12 >> roll, Roll[int])
        assert_type(2 & roll, Roll[int])
        assert_type(2 | roll, Roll[int])
        assert_type(2 ^ roll, Roll[int])

    def test_unary_operator_types(self) -> None:
        roll = _ConstantRoller(-2).roll()

        assert_type(-roll, Roll[int])
        assert_type(+roll, Roll[int])
        assert_type(abs(roll), Roll[int])
        assert_type(~roll, Roll[int])

    @pytest.mark.parametrize(("op", "name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators_preserve_outcomes_and_provenance(
        self,
        op: Callable[[Any, Any], Any],
        name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roll = _ConstantRoller(lhs).roll()
        right_roll = _ConstantRoller(rhs).roll()
        combined = op(left_roll, right_roll)
        provenance = combined.to_dict()
        definitions = provenance["definitions"]
        events = provenance["events"]

        assert combined.outcome == op(lhs, rhs)
        assert isinstance(definitions, dict)
        assert definitions["d0"] == {
            "kind": "binary",
            "operator": name,
            "operands": ["d1", "d2"],
        }
        assert isinstance(events, dict)
        assert events["e0"]["operands"] == ["e1", "e2"]

    @pytest.mark.parametrize(("op", "name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators_preserve_outcomes_and_provenance(
        self,
        op: Callable[[Any], Any],
        name: str,
        value: int,
    ) -> None:
        combined = op(_ConstantRoller(value).roll())
        provenance = combined.to_dict()
        definitions = provenance["definitions"]
        events = provenance["events"]

        assert combined.outcome == op(value)
        assert isinstance(definitions, dict)
        assert definitions["d0"] == {
            "kind": "unary",
            "operator": name,
            "operands": ["d1"],
        }
        assert isinstance(events, dict)
        assert events["e0"]["operands"] == ["e1"]

    def test_literal_plus_roll_is_serializable(self) -> None:
        roll = 2 + HRoller(H(6), name="d6").roll()

        assert roll.outcome in 2 + H(6)
        assert json.loads(json.dumps(roll.to_dict())) == roll.to_dict()

    def test_provenance_distinguishes_independent_and_shared_events(self) -> None:
        d6 = HRoller(H(6), name="d6")
        independent = d6.roll() + d6.roll()
        shared_source = d6.roll()
        shared = shared_source + shared_source

        independent_provenance = independent.to_dict()
        shared_provenance = shared.to_dict()
        independent_events = independent_provenance["events"]
        shared_events = shared_provenance["events"]
        independent_definitions = independent_provenance["definitions"]
        shared_definitions = shared_provenance["definitions"]

        assert isinstance(independent_events, dict)
        assert isinstance(shared_events, dict)
        assert isinstance(independent_definitions, dict)
        assert isinstance(shared_definitions, dict)
        assert independent_events["e0"]["operands"] == ["e1", "e2"]
        assert shared_events["e0"]["operands"] == ["e1", "e1"]
        assert independent_definitions["d0"]["operands"] == ["d1", "d1"]
        assert shared_definitions["d0"]["operands"] == ["d1", "d1"]


class TestPoolRoll:
    def test_sum_bridges_to_scalar_roll(self) -> None:
        pool_roll = PoolRoller(P(H({1: 1}), H({2: 1})), name="pool").roll()
        roll = pool_roll.sum()

        assert_type(roll, Roll[int])
        assert roll.outcome == 3
        assert roll.operands == (pool_roll,)


class TestRollerRollEquivalence:
    @pytest.mark.parametrize(("op", "_name", "lhs", "rhs"), _BINARY_OPERATOR_CASES)
    def test_binary_operators(
        self,
        op: Callable[[Any, Any], Any],
        _name: str,
        lhs: int,
        rhs: int,
    ) -> None:
        left_roller = _ConstantRoller(lhs)
        right_roller = _ConstantRoller(rhs)

        deferred_roll = op(left_roller, right_roller).roll()
        realized_roll = op(left_roller.roll(), right_roller.roll())
        reflected_deferred_roll = op(lhs, right_roller).roll()
        reflected_realized_roll = op(lhs, right_roller.roll())

        assert deferred_roll.to_dict() == realized_roll.to_dict()
        assert reflected_deferred_roll.to_dict() == reflected_realized_roll.to_dict()

    @pytest.mark.parametrize(("op", "_name", "value"), _UNARY_OPERATOR_CASES)
    def test_unary_operators(
        self,
        op: Callable[[Any], Any],
        _name: str,
        value: int,
    ) -> None:
        roller = _ConstantRoller(value)

        assert op(roller).roll().to_dict() == op(roller.roll()).to_dict()

    def test_pool_selection_and_sum(self) -> None:
        pool = PoolRoller(P(H({1: 1}), H({2: 1}), H({3: 1})), name="pool")

        deferred_roll = pool.select(-1, 0).sum().roll()
        realized_roll = pool.select(-1, 0).roll().sum()

        assert deferred_roll.to_dict() == realized_roll.to_dict()

    def test_adding_after_roll_matches_rolling_after_addition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() + 2
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 + 2).roll()

        assert realized_roll.outcome == deferred_roll.outcome
        assert realized_roll.to_dict() == deferred_roll.to_dict()

    def test_deferred_and_realized_addition_are_equivalent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 + d6).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() + d6.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.to_dict() == realized_roll.to_dict()

    def test_deferred_and_realized_subtraction_are_equivalent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")
        d4 = HRoller(H(4), name="d4")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 - d4).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() - d4.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.to_dict() == realized_roll.to_dict()
        definitions = deferred_roll.to_dict()["definitions"]
        assert isinstance(definitions, dict)
        assert definitions["d0"]["operator"] == "sub"

    def test_reflected_subtraction_preserves_operand_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), name="d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (2 - d6).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = 2 - d6.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.to_dict() == realized_roll.to_dict()

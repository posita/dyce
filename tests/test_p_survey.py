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

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar
from unittest.mock import Mock

import pytest

from dyce import H, P
from dyce.p import (
    AscendingSurveyorBase,
    DescendingSurveyorBase,
    ParameterizedSurveyor,
    SurveyorBase,
    _WhichHSurveyor,
    survey_outcome_order_ascending,
    survey_outcome_order_descending,
)

from ._helpers import enumerate_weighted_unsorted_rolls_brute_force

_StateT = TypeVar("_StateT")


class Mechanic(ABC, Generic[_StateT]):
    name: str
    initial: _StateT | None = None

    @abstractmethod
    def accumulate(
        self, state: _StateT | None, outcome: int, count: int
    ) -> _StateT: ...

    @abstractmethod
    def roll(self, roll: tuple[int, ...]) -> int: ...

    def order(self, outcomes: Iterable[int]) -> Iterable[int]:
        return survey_outcome_order_ascending(outcomes)

    @abstractmethod
    def settle(self, state: _StateT) -> int: ...


class SumMechanic(Mechanic[int]):
    name = "sum"
    initial = 0

    def accumulate(self, state: int | None, outcome: int, count: int) -> int:
        return outcome * count if state is None else state + outcome * count

    def roll(self, roll: tuple[int, ...]) -> int:
        return sum(roll)

    def settle(self, state: int) -> int:
        return state


class SuccessesMechanic(Mechanic[int]):
    name = "successes_ge5"
    initial = 0

    def accumulate(self, state: int | None, outcome: int, count: int) -> int:
        running = 0 if state is None else state
        return running + (count if outcome >= 5 else 0)

    def roll(self, roll: tuple[int, ...]) -> int:
        return sum(1 for outcome in roll if outcome >= 5)

    def settle(self, state: int) -> int:
        return state


class LargestMatchingSetMechanic(Mechanic[int]):
    name = "largest_matching_set"

    def accumulate(
        self,
        state: int | None,
        outcome: int,  # ruff: ignore[unused-method-argument]
        count: int,
    ) -> int:
        return max(0 if state is None else state, count)

    def roll(self, roll: tuple[int, ...]) -> int:
        return max((roll.count(outcome) for outcome in set(roll)), default=0)

    def settle(self, state: int) -> int:
        return state


class KeepTwoMechanic(Mechanic[tuple[int, int]]):
    def accumulate(
        self, state: tuple[int, int] | None, outcome: int, count: int
    ) -> tuple[int, int]:
        kept, total = (0, 0) if state is None else state
        take = min(count, 2 - kept)
        return kept + take, total + outcome * take

    def settle(self, state: tuple[int, int]) -> int:
        return state[1]


class KeepHighestTwoMechanic(KeepTwoMechanic):
    name = "keep_highest_2"

    def roll(self, roll: tuple[int, ...]) -> int:
        return sum(sorted(roll, reverse=True)[:2])

    def order(self, outcomes: Iterable[int]) -> Iterable[int]:
        return survey_outcome_order_descending(outcomes)


class KeepLowestTwoMechanic(KeepTwoMechanic):
    name = "keep_lowest_2"

    def roll(self, roll: tuple[int, ...]) -> int:
        return sum(sorted(roll)[:2])


class MaxMechanic(Mechanic[int]):
    name = "max"

    def accumulate(
        self,
        state: int | None,
        outcome: int,
        count: int,  # ruff: ignore[unused-method-argument]
    ) -> int:
        # This function is only ever called for outcomes with positive counts. Checking
        # count is not needed to determine which outcome is largest.
        return outcome if state is None else max(state, outcome)

    def roll(self, roll: tuple[int, ...]) -> int:
        return max(roll)

    def settle(self, state: int) -> int:
        return state


class MinMechanic(Mechanic[int]):
    name = "min"

    def accumulate(
        self,
        state: int | None,
        outcome: int,
        count: int,  # ruff: ignore[unused-method-argument]
    ) -> int:
        # This function is only ever called for outcomes with positive counts. Checking
        # count is not needed to determine which outcome is smallest.
        return outcome if state is None else min(state, outcome)

    def roll(self, roll: tuple[int, ...]) -> int:
        return min(roll)

    def settle(self, state: int) -> int:
        return state


MECHANICS: list[Mechanic[Any]] = [
    SumMechanic(),
    SuccessesMechanic(),
    LargestMatchingSetMechanic(),
    KeepHighestTwoMechanic(),
    KeepLowestTwoMechanic(),
    MaxMechanic(),
    MinMechanic(),
]

# Homogeneous, heterogeneous+weighted+gap-bearing, mixed sizes, negatives, and a
# singleton.
POOLS: list[tuple[str, P[int]]] = [
    ("3d6", 3 @ P(6)),
    ("hetero_weighted_gap", P(2 @ P(H({2: 1, 4: 2, 6: 3})), 2 @ P(6))),
    ("4d4", 4 @ P(4)),
    ("mixed_sizes", P(H(4), H(6), H(8))),
    ("fudge3", 3 @ P(H({-1: 1, 0: 1, 1: 1}))),
    ("single_d6", P(6)),
]


class TestPSurvey:
    @pytest.mark.parametrize("mech", MECHANICS, ids=[m.name for m in MECHANICS])
    @pytest.mark.parametrize("pool", [p for _, p in POOLS], ids=[n for n, _ in POOLS])
    def test_survey_matches_oracle(self, pool: P[int], mech: Mechanic[Any]) -> None:
        survey_h = pool.survey(
            accumulate=mech.accumulate,
            initial=mech.initial,
            order=mech.order,
            settle=mech.settle,
        )
        assert survey_h == _brute_force_oracle(pool, mech.roll)
        assert survey_h.total == pool.total

    def test_sum_matches_native_h(self) -> None:
        for _, pool in POOLS:
            assert (
                pool.survey(
                    accumulate=SumMechanic().accumulate,
                    initial=0,
                    order=survey_outcome_order_ascending,
                )
                == pool.h()
            )

    def test_keep_highest_two_matches_native_h(self) -> None:
        for _, pool in POOLS:
            survey_h = pool.survey(
                accumulate=KeepHighestTwoMechanic().accumulate,
                order=survey_outcome_order_descending,
                settle=KeepHighestTwoMechanic().settle,
            )
            assert survey_h == pool.at(slice(-2, None))

    def test_keep_lowest_two_matches_native_h(self) -> None:
        for _, pool in POOLS:
            survey_h = pool.survey(
                accumulate=KeepLowestTwoMechanic().accumulate,
                order=survey_outcome_order_ascending,
                settle=KeepLowestTwoMechanic().settle,
            )
            assert survey_h == pool.at(slice(0, 2))

    def test_max_matches_native_h(self) -> None:
        for _, pool in POOLS:
            assert pool.survey(
                accumulate=MaxMechanic().accumulate,
                order=survey_outcome_order_ascending,
            ) == pool.at(-1)

    def test_min_matches_native_h(self) -> None:
        for _, pool in POOLS:
            assert pool.survey(
                accumulate=MinMechanic().accumulate,
                order=survey_outcome_order_ascending,
            ) == pool.at(0)

    def test_order_agnostic_mechanic_is_direction_invariant(self) -> None:
        # Summing outcomes should give the same result in ascending and descending order
        for _, pool in POOLS:
            ascending = pool.survey(
                accumulate=SumMechanic().accumulate,
                initial=0,
                order=survey_outcome_order_ascending,
            )
            descending = pool.survey(
                accumulate=SumMechanic().accumulate,
                initial=0,
                order=survey_outcome_order_descending,
            )
            assert ascending == descending

    def test_accumulate_never_invoked_with_zero_count(self) -> None:
        def accumulate(state: int | None, outcome: int, count: int) -> int:
            return (0 if state is None else state) + outcome * count

        accumulate_mock = Mock(wraps=accumulate)
        (2 @ P(H({1: 1, 2: 1}))).survey(
            accumulate=accumulate_mock,
            initial=0,
            order=survey_outcome_order_ascending,
        )
        accumulate_mock.assert_called()
        assert all(
            invocation.args[2] > 0 for invocation in accumulate_mock.call_args_list
        )

    def test_empty_pool_returns_empty_h(self) -> None:
        assert P().survey(
            accumulate=SumMechanic().accumulate,
            initial=0,
            order=survey_outcome_order_ascending,
        ) == H({})

    def test_survey_without_surveyor_or_accumulate_raises(self) -> None:
        with pytest.raises(
            ValueError, match=r"must provide surveyor or accumulate and order"
        ):
            P(6).survey()  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    def test_survey_with_both_surveyor_and_kwargs_raises(self) -> None:
        surveyor = ParameterizedSurveyor(
            accumulate=SumMechanic().accumulate, order=survey_outcome_order_ascending
        )
        survey: Any = P(6).survey
        with pytest.raises(
            ValueError,
            match=r"must not provide accumulate, initial, order, or settle with surveyor",
        ):
            survey(
                surveyor,
                accumulate=SumMechanic().accumulate,
                order=survey_outcome_order_ascending,
            )

    def test_which_surveyor_requires_a_selection(self) -> None:
        with pytest.raises(ValueError, match=r"requires at least one selection"):
            _WhichHSurveyor(P(6), ())

    def test_surveyor_base_default_initial_and_settle(self) -> None:
        # A minimal SurveyorBase subclass overriding only the two abstract methods,
        # exercising the base initial (None) and settle (identity) defaults
        class _SumSurveyor(SurveyorBase[int, int, int]):
            def accumulate(self, state: int | None, outcome: int, count: int) -> int:
                return (0 if state is None else state) + outcome * count

            def order(self, outcomes: Iterable[int]) -> Iterable[int]:
                return survey_outcome_order_ascending(outcomes)

        pool = 2 @ P(6)
        assert pool.survey(_SumSurveyor()) == pool.h()

    def test_ascending_descending_surveyor_bases_supply_order(self) -> None:
        # The two order-mixin bases just delegate to the module order helpers.
        class _Asc(AscendingSurveyorBase[int, int, int]):
            def accumulate(
                self,
                state: int | None,  # ruff: ignore[unused-method-argument]
                outcome: int,
                count: int,  # ruff: ignore[unused-method-argument]
            ) -> int:
                return outcome

        class _Desc(DescendingSurveyorBase[int, int, int]):
            def accumulate(
                self,
                state: int | None,  # ruff: ignore[unused-method-argument]
                outcome: int,
                count: int,  # ruff: ignore[unused-method-argument]
            ) -> int:
                return outcome

        assert list(_Asc().order([3, 1, 2])) == [1, 2, 3]
        assert list(_Desc().order([3, 1, 2])) == [3, 2, 1]


# ---- Helpers -------------------------------------------------------------------------


def _brute_force_oracle(
    pool: P[int], mechanic: Callable[[tuple[int, ...]], Any]
) -> H[Any]:
    r"""
    Reduces *mechanic* over every weighted roll of *pool*.

    This deliberately uses an independently verified, brute-force mechanism to enumerate rolls and weights.
    """
    acc: dict[Any, int] = defaultdict(int)
    for roll, weight in enumerate_weighted_unsorted_rolls_brute_force(pool):
        acc[mechanic(roll)] += weight
    return H(acc)

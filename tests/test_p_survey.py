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

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from itertools import product as iproduct
from math import prod
from typing import Any

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

# ---- Brute-force oracle ----------------------------------------------------------------


def _oracle(pool: "P[int]", mechanic: Callable[[tuple[int, ...]], Any]) -> "H[Any]":
    r"""
    Independent ground truth: enumerate every weighted face combination across all dice.

    This deliberately shares nothing with [`P.survey`][dyce.P.survey]’s state-collapse machinery.
    It is a flat cartesian product over each die’s (outcome, count) faces, accumulating the product of face weights for each distinct mechanic result.
    """
    faces_per_die: list[list[tuple[int, int]]] = []
    for h, n in pool._h_groups.items():  # ruff: ignore[private-member-access]
        faces = list(h.items())
        faces_per_die.extend([faces] * n)
    acc: dict[Any, int] = defaultdict(int)
    for combo in iproduct(*faces_per_die):
        roll = tuple(outcome for outcome, _ in combo)
        weight = prod(count for _, count in combo)
        acc[mechanic(roll)] += weight
    return H(acc)


# ---- Mechanics, expressed both as transition functions and as roll oracles --------------


def _sum_next(state: int | None, outcome: int, count: int) -> int:
    return outcome * count if state is None else state + outcome * count


def _sum_roll(roll: tuple[int, ...]) -> int:
    return sum(roll)


def _successes_next(state: int | None, outcome: int, count: int) -> int:
    running = 0 if state is None else state
    return running + (count if outcome >= 5 else 0)


def _successes_roll(roll: tuple[int, ...]) -> int:
    return sum(1 for outcome in roll if outcome >= 5)


def _largest_set_next(
    state: int | None,
    outcome: int,  # ruff: ignore[unused-function-argument]
    count: int,
) -> int:
    return max(0 if state is None else state, count)


def _largest_set_roll(roll: tuple[int, ...]) -> int:
    return max((roll.count(outcome) for outcome in set(roll)), default=0)


def _keep_two_next(
    state: tuple[int, int] | None, outcome: int, count: int
) -> tuple[int, int]:
    kept, total = (0, 0) if state is None else state
    take = min(count, 2 - kept)
    return kept + take, total + outcome * take


def _keep_two_settle(state: tuple[int, int]) -> int:  # ruff: ignore[reimplemented-operator]
    return state[1]


def _keep_highest_two_roll(roll: tuple[int, ...]) -> int:
    return sum(sorted(roll, reverse=True)[:2])


def _keep_lowest_two_roll(roll: tuple[int, ...]) -> int:
    return sum(sorted(roll)[:2])


def _max_next(
    state: int | None,
    outcome: int,
    count: int,  # ruff: ignore[unused-function-argument]
) -> int:
    # A presence mechanic: under positive-only calls, accumulate sees only outcomes
    # that appeared, so count need not be consulted.
    return outcome if state is None else max(state, outcome)


def _max_roll(roll: tuple[int, ...]) -> int:
    return max(roll)


def _min_next(
    state: int | None,
    outcome: int,
    count: int,  # ruff: ignore[unused-function-argument]
) -> int:
    return outcome if state is None else min(state, outcome)


def _min_roll(roll: tuple[int, ...]) -> int:
    return min(roll)


@dataclass(frozen=True)
class Mechanic:
    name: str
    accumulate: Callable[[Any, Any, int], Any]
    roll: Callable[[tuple[int, ...]], Any]
    initial: Any = None
    order: Callable[[Iterable[Any]], Iterable[Any]] | None = None
    settle: Callable[[Any], Any] | None = None


MECHANICS: list[Mechanic] = [
    Mechanic("sum", _sum_next, _sum_roll, initial=0),
    Mechanic("successes_ge5", _successes_next, _successes_roll, initial=0),
    Mechanic("largest_matching_set", _largest_set_next, _largest_set_roll),
    Mechanic(
        "keep_highest_2",
        _keep_two_next,
        _keep_highest_two_roll,
        order=survey_outcome_order_descending,
        settle=_keep_two_settle,
    ),
    Mechanic(
        "keep_lowest_2",
        _keep_two_next,
        _keep_lowest_two_roll,
        settle=_keep_two_settle,
    ),
    Mechanic("max", _max_next, _max_roll),
    Mechanic("min", _min_next, _min_roll),
]

# Homogeneous, heterogeneous+weighted+gap-bearing, mixed sizes, negatives, and a singleton.
POOLS: list[tuple[str, "P[int]"]] = [
    ("3d6", 3 @ P(6)),
    ("hetero_weighted_gap", P(2 @ P(H({2: 1, 4: 2, 6: 3})), 2 @ P(6))),
    ("4d4", 4 @ P(4)),
    ("mixed_sizes", P(H(4), H(6), H(8))),
    ("fudge3", 3 @ P(H({-1: 1, 0: 1, 1: 1}))),
    ("single_d6", P(6)),
]


# ---- Tests -----------------------------------------------------------------------------


def _mech(name: str) -> Mechanic:
    return next(m for m in MECHANICS if m.name == name)


@pytest.mark.parametrize("mech", MECHANICS, ids=[m.name for m in MECHANICS])
@pytest.mark.parametrize("pool", [p for _, p in POOLS], ids=[n for n, _ in POOLS])
def test_survey_matches_oracle(pool: "P[int]", mech: Mechanic) -> None:
    order = mech.order if mech.order is not None else survey_outcome_order_ascending
    got = pool.survey(
        accumulate=mech.accumulate,
        initial=mech.initial,
        order=order,
        settle=mech.settle,
    )
    assert got == _oracle(pool, mech.roll)
    # No mass created or lost: the result totals exactly the pool's.
    assert got.total == pool.total


def test_sum_matches_native_h() -> None:
    for _, pool in POOLS:
        assert (
            pool.survey(
                accumulate=_sum_next,
                initial=0,
                order=survey_outcome_order_ascending,
            )
            == pool.h()
        )


def test_keep_highest_two_matches_native_h() -> None:
    for _, pool in POOLS:
        got = pool.survey(
            accumulate=_keep_two_next,
            order=survey_outcome_order_descending,
            settle=_keep_two_settle,
        )
        assert got == pool.h(slice(-2, None))


def test_keep_lowest_two_matches_native_h() -> None:
    for _, pool in POOLS:
        got = pool.survey(
            accumulate=_keep_two_next,
            order=survey_outcome_order_ascending,
            settle=_keep_two_settle,
        )
        assert got == pool.h(slice(0, 2))


def test_max_matches_native_h() -> None:
    for _, pool in POOLS:
        assert pool.survey(
            accumulate=_mech("max").accumulate,
            order=survey_outcome_order_ascending,
        ) == pool.h(-1)


def test_min_matches_native_h() -> None:
    for _, pool in POOLS:
        assert pool.survey(
            accumulate=_mech("min").accumulate,
            order=survey_outcome_order_ascending,
        ) == pool.h(0)


def test_order_agnostic_mechanic_is_direction_invariant() -> None:
    # A mechanic that folds symmetrically (sum) must give the same result either
    # sweep direction; an order-sensitive one (keep-highest) need not.
    for _, pool in POOLS:
        ascending = pool.survey(
            accumulate=_sum_next,
            initial=0,
            order=survey_outcome_order_ascending,
        )
        descending = pool.survey(
            accumulate=_sum_next,
            initial=0,
            order=survey_outcome_order_descending,
        )
        assert ascending == descending


def test_count_blindness_is_safe_for_presence_but_not_multiplicity() -> None:
    # Under positive-only calls, ignoring count is SAFE for a presence mechanic
    # (max is only told about outcomes that actually appeared) ...
    pool = 2 @ P(6)
    assert pool.survey(
        accumulate=_max_next,
        order=survey_outcome_order_ascending,
    ) == pool.h(-1)

    # ... but WRONG for a multiplicity mechanic: a count-blind sum adds each present
    # outcome once, dropping the extra dice on any doubled face.
    def count_blind_sum(
        state: int | None,
        outcome: int,
        count: int,  # ruff: ignore[unused-function-argument]
    ) -> int:
        return outcome if state is None else state + outcome

    assert pool.survey(
        accumulate=count_blind_sum,
        initial=0,
        order=survey_outcome_order_ascending,
    ) != pool.survey(
        accumulate=_sum_next,
        initial=0,
        order=survey_outcome_order_ascending,
    )


def test_accumulate_never_invoked_with_zero_count() -> None:
    # The positive-only contract: accumulate is called only for outcomes at least one
    # die shows, never for outcomes a branch places no dice on.
    seen: list[tuple[int, int]] = []

    def spy(state: int | None, outcome: int, count: int) -> int:
        seen.append((outcome, count))
        return (0 if state is None else state) + outcome * count

    (2 @ P(H({1: 1, 2: 1}))).survey(
        accumulate=spy,
        initial=0,
        order=survey_outcome_order_ascending,
    )
    assert seen  # it was called
    assert all(count > 0 for _, count in seen)


def test_empty_pool_returns_empty_h() -> None:
    assert P().survey(
        accumulate=_sum_next,
        initial=0,
        order=survey_outcome_order_ascending,
    ) == H({})


def test_repeated_invocation_is_stable() -> None:
    # The memo is scoped per top-level call; repeated calls must be identical.
    pool = P(2 @ P(H({2: 1, 4: 2, 6: 3})), 2 @ P(6))
    surveyor = ParameterizedSurveyor(
        accumulate=_largest_set_next,
        order=survey_outcome_order_ascending,
    )
    assert pool.survey(surveyor) == pool.survey(surveyor)


def test_survey_without_surveyor_or_accumulate_raises() -> None:
    # Deliberately-invalid calls, routed through an Any reference so the static
    # checkers don't (correctly) reject them before the runtime guard fires.
    survey: Any = P(6).survey
    with pytest.raises(ValueError, match=r"must provide a surveyor or an accumulate"):
        survey()


def test_survey_with_both_surveyor_and_kwargs_raises() -> None:
    surveyor = ParameterizedSurveyor(
        accumulate=_sum_next, order=survey_outcome_order_ascending
    )
    survey: Any = P(6).survey
    with pytest.raises(ValueError, match=r"must not provide an accumulate"):
        survey(
            surveyor,
            accumulate=_sum_next,
            order=survey_outcome_order_ascending,
        )


def test_which_surveyor_requires_a_selection() -> None:
    with pytest.raises(ValueError, match=r"requires at least one selection"):
        _WhichHSurveyor(P(6), ())


def test_surveyor_base_default_initial_and_settle() -> None:
    # A minimal SurveyorBase subclass overriding only the two abstract methods,
    # exercising the base initial (None) and settle (identity) defaults.
    class _SumSurveyor(SurveyorBase[int, int, int]):
        def accumulate(self, state: int | None, outcome: int, count: int) -> int:
            return (0 if state is None else state) + outcome * count

        def order(self, outcomes: Iterable[int]) -> Iterable[int]:
            return survey_outcome_order_ascending(outcomes)

    pool = 2 @ P(6)
    assert pool.survey(_SumSurveyor()) == pool.h()


def test_ascending_descending_surveyor_bases_supply_order() -> None:
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

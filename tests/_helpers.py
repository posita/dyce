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

import contextlib
from collections.abc import Iterable, Iterator, Sequence
from decimal import Decimal
from fractions import Fraction
from itertools import chain, combinations_with_replacement, groupby, product
from math import factorial, prod
from typing import Any, TypeVar

from dyce import H
from dyce.p import RollCountT
from dyce.types import GetItemT, getitems, natural_key

__all__ = (
    "SAMPLE_OUTCOME_TYPES",
    "NoCompare",
    "NoCompareCanOnlyAdd",
    "enumerate_weighted_unsorted_rolls_brute_force",
    "enumerate_weighted_unsorted_rolls_multinomial_coefficient",
    "sort_and_select_from_rolls",
)

_T = TypeVar("_T")

# ---- Outcome types for parametrized construction tests -------------------------------

SAMPLE_OUTCOME_TYPES: tuple[type, ...] = (
    int,
    float,
    Decimal,
    Fraction,
)

with contextlib.suppress(ImportError):
    import numpy as np

    SAMPLE_OUTCOME_TYPES += (
        np.longlong,
        np.longdouble,
    )

with contextlib.suppress(ImportError):
    import sympy  # type: ignore[import-untyped]

    SAMPLE_OUTCOME_TYPES += (
        sympy.Integer,
        sympy.Number,
        sympy.Rational,
    )

# ---- Comparison-averse outcome stand-ins ---------------------------------------------


class NoCompare:
    r"""
    For testing natural_key sorting and other places where outcomes ignorant of mathematical operations is required.
    """

    def __init__(self, val: str) -> None:
        self.val = val

    def __lt__(self, other: object) -> bool:
        raise TypeError

    def __str__(self) -> str:
        return self.val

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.val!r})"


class NoCompareCanOnlyAdd(NoCompare):
    def __add__(self, other: Any) -> "NoCompareCanOnlyAdd":  # ruff: ignore[any-type]
        return NoCompareCanOnlyAdd(f"{self.val}+{other}")


# ---- Brute-force roll enumeration ----------------------------------------------------


def enumerate_weighted_unsorted_rolls_multinomial_coefficient(
    hs: Sequence[H[_T]],
) -> Iterator[RollCountT[_T]]:
    r"""
    Yield every `(roll, weight)` via Cartesian product of the multinomial coefficient of like groups within *hs*.

    *roll* is one outcome per die, in undefined order (unsorted).
    *weight* is the product of the per-die counts.
    Consumers must aggregate counts over yielded rolls, which are not guaranteed to be sorted or unique.
    """
    per_group_rolls = [
        list(_rwc_n_h_multinomial_coefficient(sum(1 for _ in g), h))
        for h, g in groupby(hs)
    ]
    for combo in product(*per_group_rolls):
        roll = tuple(chain.from_iterable(roll for roll, _ in combo))
        weight = prod(w for _, w in combo)
        yield roll, weight


def enumerate_weighted_unsorted_rolls_brute_force(
    hs: Iterable[H[_T]],
) -> Iterator[tuple[tuple[_T, ...], int]]:
    r"""
    Yield every `(roll, weight)` over *hs* by brute force Cartesian product.

    *roll* is one outcome per die, in die order (unsorted).
    *weight* is the product of the per-die counts.
    Consumers must aggregate counts over yielded rolls, which are not guaranteed to be sorted or unique.
    """
    faces_per_die: list[list[tuple[_T, int]]] = [list(h.items()) for h in hs]
    for combo in product(*faces_per_die):
        roll: tuple[_T, ...] = tuple(outcome for outcome, _ in combo)
        weight = prod(count for _, count in combo)
        yield roll, weight


def sort_and_select_from_rolls(
    unsorted_roll_counts: Iterable[RollCountT[_T]], *which: GetItemT
) -> Iterator[RollCountT[_T]]:
    for unsorted_roll, count in unsorted_roll_counts:
        try:
            roll = tuple(sorted(unsorted_roll))  # type: ignore[type-var]
        except TypeError:
            roll = tuple(sorted(unsorted_roll, key=natural_key))
        roll = tuple(getitems(roll, which)) if which else roll
        if roll:
            yield roll, count


def _rwc_n_h_multinomial_coefficient(
    n: int,
    h: H[_T],
    *which: GetItemT,
) -> Iterator[RollCountT[_T]]:
    r"""Independent reference implementation using multinomial coefficients."""
    multinomial_coefficient_numerator = factorial(n)
    for sorted_outcomes_for_roll in combinations_with_replacement(h, n):
        count_scalar = prod(h[outcome] for outcome in sorted_outcomes_for_roll)
        multinomial_coefficient_denominator = prod(
            factorial(sum(1 for _ in g)) for _, g in groupby(sorted_outcomes_for_roll)
        )
        roll_selection = (
            tuple(getitems(sorted_outcomes_for_roll, which))
            if which
            else sorted_outcomes_for_roll
        )
        if roll_selection:
            yield (
                roll_selection,
                count_scalar
                * multinomial_coefficient_numerator
                // multinomial_coefficient_denominator,
            )

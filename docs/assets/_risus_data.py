# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum
from fractions import Fraction
from typing import TypeVar

from dyce import H

__all__ = (
    "ThemTable",
    "UsRow",
    "Versus",
    "VersusFuncT",
    "scenarios",
)

T = TypeVar("T")
VersusFuncT = Callable[[int, int], H["Versus"]]

d6 = H(6)


class Versus(IntEnum):
    LOSE = -1
    DRAW = 0
    WIN = 1

    @staticmethod
    def raw_vs(us_outcome: int, them_outcome: int) -> "Versus":
        return (
            Versus.LOSE
            if us_outcome < them_outcome
            else Versus.WIN
            if us_outcome > them_outcome
            else Versus.DRAW
        )

    @staticmethod
    def us_vs_them(our_pool_size: int, their_pool_size: int) -> H["Versus"]:
        return (our_pool_size @ d6).apply(Versus.raw_vs, their_pool_size @ d6)


@dataclass
class UsRow:
    our_pool_size: int
    data: Mapping[Versus, Fraction]


@dataclass
class ThemTable:
    their_pool_size: int
    results: Sequence[UsRow]


def scenarios(
    us_vs_them_func: VersusFuncT,
    *,
    our_pool_rel_sizes: Sequence[int] = tuple(range(3)),
    their_pool_sizes: Sequence[int] = tuple(range(3, 6)),
) -> Sequence[ThemTable]:
    scenario_data: list[ThemTable] = []

    for their_pool_size in their_pool_sizes:
        us_rows: list[UsRow] = []
        for our_pool_rel_size in our_pool_rel_sizes:
            our_pool_size = their_pool_size + our_pool_rel_size
            results = us_vs_them_func(our_pool_size, their_pool_size).zero_fill(Versus)
            prob_data = dict(results.probability_items())
            us_row = UsRow(our_pool_size, data=prob_data)
            us_rows.append(us_row)
        them_table = ThemTable(their_pool_size, results=us_rows)
        scenario_data.append(them_table)

    return scenario_data

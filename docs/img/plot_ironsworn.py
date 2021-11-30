# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from collections import defaultdict
from enum import IntEnum, auto
from typing import Iterator, Tuple, cast

from dyce import H, P


class IronSoloResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = auto()
    WEAK_SUCCESS = auto()
    STRONG_SUCCESS = auto()
    SPECTACULAR_SUCCESS = auto()


def iron_solo_results(mod: int = 0):
    d6 = H(6)
    d10_2 = 2 @ P(10)
    modded_d6 = d6 + mod

    for d6_outcome, d6_count in cast(Iterator[Tuple[int, int]], modded_d6.items()):
        for (d10_2_roll, d10_2_count) in cast(
            Iterator[Tuple[Tuple[int, int], int]], d10_2.rolls_with_counts()
        ):
            lower_d10, higher_d10 = d10_2_roll
            if d6_outcome > higher_d10:
                outcome = (
                    IronSoloResult.SPECTACULAR_SUCCESS
                    if higher_d10 == lower_d10
                    else IronSoloResult.STRONG_SUCCESS
                )
            elif d6_outcome > lower_d10:
                outcome = IronSoloResult.WEAK_SUCCESS
            else:
                outcome = (
                    IronSoloResult.SPECTACULAR_FAILURE
                    if higher_d10 == lower_d10
                    else IronSoloResult.FAILURE
                )
            yield outcome, d6_count * d10_2_count


def do_it(__: str) -> None:
    import matplotlib.pyplot

    fig, axes = matplotlib.pyplot.subplots()
    by_result = defaultdict(list)
    mods = list(range(-2, 5))

    for mod in mods:
        results_for_mod = dict(H(iron_solo_results(mod)).distribution())

        for result in IronSoloResult:
            result_val = float(results_for_mod.get(result, 0))
            by_result[result].append(result_val)

    labels = [str(mod) for mod in mods]
    bottoms = [0.0 for _ in mods]

    for result in IronSoloResult:
        result_vals = by_result[result]
        assert len(result_vals) == len(mods)
        axes.bar(labels, result_vals, bottom=bottoms, label=result.name)
        bottoms = [
            bottom + result_val for bottom, result_val in zip(bottoms, result_vals)
        ]

    axes.legend()
    axes.set_xlabel("modifier")
    # Should match the corresponding img[alt] text
    axes.set_title("Ironsworn distributions")
    fig.tight_layout()

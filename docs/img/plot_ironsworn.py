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
from functools import partial

from dyce import H


class IronSoloResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = auto()
    WEAK_SUCCESS = auto()
    STRONG_SUCCESS = auto()
    SPECTACULAR_SUCCESS = auto()


d6 = H(6)
d10 = H(10)


def sub_d6(__, d6_outcome, mod=0):
    def sub_first_d10(__, first_challenge):
        def sub_second_d10(__, second_challenge):
            action = d6_outcome + mod
            action_beats_first = action > first_challenge
            action_beats_second = action > second_challenge
            doubles = first_challenge == second_challenge
            if action_beats_first and action_beats_second:
                return (
                    IronSoloResult.SPECTACULAR_SUCCESS
                    if doubles
                    else IronSoloResult.STRONG_SUCCESS
                )
            elif action_beats_first or action_beats_second:
                return IronSoloResult.WEAK_SUCCESS
            else:
                return (
                    IronSoloResult.SPECTACULAR_FAILURE
                    if doubles
                    else IronSoloResult.FAILURE
                )

        return d10.substitute(sub_second_d10)

    return d10.substitute(sub_first_d10)


def do_it(__: str) -> None:
    import matplotlib.pyplot

    fig, axes = matplotlib.pyplot.subplots()
    by_result = defaultdict(list)
    mods = list(range(-2, 5))

    for mod in mods:
        results_for_mod = d6.substitute(partial(sub_d6, mod=mod))
        distribution_for_mod = dict(results_for_mod.distribution())

        for result in IronSoloResult:
            result_val = float(distribution_for_mod.get(result, 0))
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

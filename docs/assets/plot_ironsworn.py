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
from dyce.h import resolve_dependent_probability


class IronSoloResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = auto()
    WEAK_SUCCESS = auto()
    STRONG_SUCCESS = auto()
    SPECTACULAR_SUCCESS = auto()


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker

    d6 = H(6)
    d10 = H(10)

    def iron_solo_dependent_term(action, first_challenge, second_challenge, mod=0):
        modded_action = action + mod
        beats_first = modded_action > first_challenge
        beats_second = modded_action > second_challenge
        doubles = first_challenge == second_challenge

        if beats_first and beats_second:
            return (
                IronSoloResult.SPECTACULAR_SUCCESS
                if doubles
                else IronSoloResult.STRONG_SUCCESS
            )
        elif beats_first or beats_second:
            return IronSoloResult.WEAK_SUCCESS
        else:
            return (
                IronSoloResult.SPECTACULAR_FAILURE
                if doubles
                else IronSoloResult.FAILURE
            )

    fig, ax = matplotlib.pyplot.subplots()
    by_result = defaultdict(list)
    mods = list(range(0, 5))
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))

    for mod in mods:
        results_for_mod = resolve_dependent_probability(
            partial(iron_solo_dependent_term, mod=mod),
            action=d6,
            first_challenge=d10,
            second_challenge=d10,
        )
        distribution_for_mod = dict(results_for_mod.distribution())

        for result in IronSoloResult:
            result_val = float(distribution_for_mod.get(result, 0))
            by_result[result].append(result_val)

    labels = [str(mod) for mod in mods]
    bottoms = [0.0 for _ in mods]

    for result in IronSoloResult:
        result_vals = by_result[result]
        assert len(result_vals) == len(mods)
        ax.bar(labels, result_vals, bottom=bottoms, label=result.name)
        bottoms = [
            bottom + result_val for bottom, result_val in zip(bottoms, result_vals)
        ]

    ax.legend()
    ax.set_xlabel("Modifier", color=text_color)
    ax.set_title("Ironsworn distributions", color=text_color)
    fig.tight_layout()

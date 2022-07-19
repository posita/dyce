# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from enum import IntEnum, auto
from functools import partial

from dyce import H


class IronSoloResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = auto()
    WEAK_SUCCESS = auto()
    STRONG_SUCCESS = auto()
    SPECTACULAR_SUCCESS = auto()


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker
    import pandas

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

    mods = list(range(0, 5))
    df = pandas.DataFrame(columns=IronSoloResult)

    for mod in mods:
        res_for_mod = H.foreach(
            partial(iron_solo_dependent_term, mod=mod),
            action=d6,
            first_challenge=d10,
            second_challenge=d10,
        ).zero_fill(IronSoloResult)
        results_for_mod = dict(res_for_mod.distribution(rational_t=lambda n, d: n / d))
        row = pandas.DataFrame(results_for_mod, columns=IronSoloResult, index=[mod])
        df = pandas.concat((df, row))

    df.index.name = "Modifier"
    # DataFrames use enum's values for displaying column names, so we convert them to
    # names
    df = df.rename(columns={v: v.name for v in IronSoloResult})

    ax = df.plot(kind="barh", stacked=True)
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ylabel = ax.get_ylabel()
    ax.set_ylabel(ylabel, color=text_color)

    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
    ax.legend()
    ax.set_title("Ironsworn distributions", color=text_color)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from enum import IntEnum, auto
from functools import partial

from dyce import H, P
from dyce.evaluation import HResult, PResult, foreach


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

    def iron_solo_dependent_term(
        action: HResult,
        challenges: PResult,
        mod=0,
    ):
        modded_action = action.outcome + mod
        first_challenge_outcome, second_challenge_outcome = challenges.roll
        beats_first_challenge = modded_action > first_challenge_outcome
        beats_second_challenge = modded_action > second_challenge_outcome
        doubles = first_challenge_outcome == second_challenge_outcome
        if beats_first_challenge and beats_second_challenge:
            return (
                IronSoloResult.SPECTACULAR_SUCCESS
                if doubles
                else IronSoloResult.STRONG_SUCCESS
            )
        elif beats_first_challenge or beats_second_challenge:
            return IronSoloResult.WEAK_SUCCESS
        else:
            return (
                IronSoloResult.SPECTACULAR_FAILURE
                if doubles
                else IronSoloResult.FAILURE
            )

    mods = list(range(0, 5))
    # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
    df = pandas.DataFrame(columns=[v.name for v in IronSoloResult])

    for mod in mods:
        h_for_mod = foreach(
            partial(iron_solo_dependent_term, mod=mod),
            action=d6,
            challenges=2 @ P(d10),
        )
        # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
        results_for_mod = {
            outcome.name: count  # type: ignore
            for outcome, count in h_for_mod.zero_fill(IronSoloResult).distribution(
                rational_t=lambda n, d: n / d
            )
        }
        row = pandas.DataFrame(
            # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
            results_for_mod,
            columns=[v.name for v in IronSoloResult],
            index=[mod],
        )
        df = pandas.concat((df, row))

    df.index.name = "Modifier"
    # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
    # # DataFrames use enum's values for displaying column names, so we convert them to
    # # names
    # df = df.rename(columns={v: v.name for v in IronSoloResult})
    print(df.style.format("{:.2%}").to_html())

    ax = df.plot(kind="barh", stacked=True)
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ylabel = ax.get_ylabel()
    ax.set_ylabel(ylabel, color=text_color)

    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
    ax.legend()
    ax.set_title("Ironsworn distributions", color=text_color)

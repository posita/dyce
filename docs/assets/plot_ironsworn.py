# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from argparse import Namespace
from enum import IntEnum, auto
from pathlib import Path
from typing import cast

import pandas as pd
from _plot import main, name_from_path  # pyrefly: ignore[missing-import]
from matplotlib import ticker

from dyce import H, HResult, P, PResult, expand

_LOGGER = logging.getLogger(__name__)


class IronSoloResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = auto()
    WEAK_SUCCESS = auto()
    STRONG_SUCCESS = auto()
    SPECTACULAR_SUCCESS = auto()


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    d6 = H(6)
    d10 = H(10)

    def iron_solo_dependent_term(
        action: HResult[int],
        challenges: PResult[int],
        mod: int = 0,
    ) -> IronSoloResult:
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

    categories = [v.name for v in IronSoloResult]
    mods = list(range(5))
    # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
    df = pd.DataFrame(columns=categories)

    for mod in mods:
        h_for_mod = expand(
            iron_solo_dependent_term,
            d6,
            2 @ P(d10),
            mod=mod,
        )
        probs = {
            cast("IronSoloResult", outcome).name: float(prob)
            for outcome, prob in h_for_mod.zero_fill(IronSoloResult).probability_items()
        }
        row = pd.DataFrame(
            probs,
            # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
            columns=categories,
            index=[mod],
        )
        df = pd.concat((df, row))

    df.index.name = "Modifier"
    df.style.format("{:.2%}").to_html()  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]
    ax = df.plot(kind="barh", stacked=True)
    text_color = "white" if args.style == "dark" else "black"

    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.set_ylabel(ax.get_ylabel(), color=text_color)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    ax.legend()
    ax.set_title("Ironsworn distributions", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

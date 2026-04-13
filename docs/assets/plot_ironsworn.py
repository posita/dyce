# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from argparse import Namespace
from enum import IntEnum
from pathlib import Path

import pandas as pd
from _plot import main, name_from_path  # pyrefly: ignore[missing-import]
from matplotlib import ticker

from dyce import H, HResult, P, PResult, expand

_LOGGER = logging.getLogger(__name__)


class IronDramaticResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = 0
    WEAK_SUCCESS = 1
    STRONG_SUCCESS = 2
    SPECTACULAR_SUCCESS = 3


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    d6 = H(6)
    d10 = H(10)

    def iron_dramatic_dependent_term(
        action: HResult[int],
        challenges: PResult[int],
        *,
        mod: int = 0,
    ) -> IronDramaticResult:
        modded_action = action.outcome + mod
        first_challenge_outcome, second_challenge_outcome = challenges.roll
        beats_first_challenge = modded_action > first_challenge_outcome
        beats_second_challenge = modded_action > second_challenge_outcome
        doubles = first_challenge_outcome == second_challenge_outcome
        if beats_first_challenge and beats_second_challenge:
            return (
                IronDramaticResult.SPECTACULAR_SUCCESS
                if doubles
                else IronDramaticResult.STRONG_SUCCESS
            )
        elif beats_first_challenge or beats_second_challenge:
            return IronDramaticResult.WEAK_SUCCESS
        else:
            return (
                IronDramaticResult.SPECTACULAR_FAILURE
                if doubles
                else IronDramaticResult.FAILURE
            )

    # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
    categories = [v.name for v in IronDramaticResult]
    mods = list(range(5))
    data: list[dict[str, float]] = []

    for mod in mods:
        h_for_mod = expand(
            iron_dramatic_dependent_term,
            d6,
            2 @ P(d10),
            mod=mod,
        )
        probs = {
            outcome.name: float(prob)
            for outcome, prob in h_for_mod.zero_fill(
                IronDramaticResult
            ).probability_items()
        }
        data.append(probs)

    df = pd.DataFrame(data, columns=categories, index=mods)
    df.index.name = "Modifier"
    print(df.style.format("{:.2%}").to_html())  # noqa: T201 # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]

    text_color = "white" if args.style == "dark" else "black"
    ax = df.plot(kind="barh", stacked=True)
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.set_ylabel(ax.get_ylabel(), color=text_color)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    ax.legend()
    ax.set_title("Ironsworn distributions", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

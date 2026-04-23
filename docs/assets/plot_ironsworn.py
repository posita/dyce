# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:core]
    from enum import IntEnum

    from dyce import HResult, PResult, expand
    from dyce.d import d6, p2d10

    class IronDramaticResult(IntEnum):
        SPECTACULAR_FAILURE = -1
        FAILURE = 0
        WEAK_SUCCESS = 1
        STRONG_SUCCESS = 2
        SPECTACULAR_SUCCESS = 3

    def iron_dramatic_dependent_term(
        action: HResult[int],
        challenges: PResult[int],
        *,
        action_mod: int = 0,
    ) -> IronDramaticResult:
        modded_action = action.outcome + action_mod
        assert len(challenges.roll) == 2, "pool must have exactly 2 challenge dice"
        first_challenge_outcome, second_challenge_outcome = challenges.roll
        challenge_doubles = first_challenge_outcome == second_challenge_outcome
        modded_action_beats_first_challenge = modded_action > first_challenge_outcome
        modded_action_beats_second_challenge = modded_action > second_challenge_outcome

        if modded_action_beats_first_challenge and modded_action_beats_second_challenge:
            return (
                IronDramaticResult.SPECTACULAR_SUCCESS
                if challenge_doubles
                else IronDramaticResult.STRONG_SUCCESS
            )
        elif (
            modded_action_beats_first_challenge or modded_action_beats_second_challenge
        ):
            return IronDramaticResult.WEAK_SUCCESS
        else:
            return (
                IronDramaticResult.SPECTACULAR_FAILURE
                if challenge_doubles
                else IronDramaticResult.FAILURE
            )

    action_mods = list(range(-1, 4))
    results_by_action_mod = {
        action_mod: expand(
            iron_dramatic_dependent_term, d6, p2d10, action_mod=action_mod
        )
        for action_mod in action_mods
    }

    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:table]
    import pandas as pd

    data = [
        {
            outcome.name: float(prob)
            for outcome, prob in result.zero_fill(
                IronDramaticResult
            ).probability_items()
        }
        for result in results_by_action_mod.values()
    ]

    df = pd.DataFrame(
        data,
        # TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
        columns=[v.name for v in IronDramaticResult],
        index=action_mods,
    )
    df.index.name = "Action Modifier"
    # --8<-- [end:table]

    # NOTE: Translates to df.style.format("{:.2%}") in docs/assets/nb_ironsworn.py
    print(df.style.format("{:.2%}").to_html())  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:viz]
    from matplotlib import ticker

    ax = df.plot(kind="barh", stacked=True)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    ax.set_title("Ironsworn distributions")
    ax.legend(loc="center")
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.yaxis.label.set_color(line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

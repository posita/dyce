# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs-src/nb_ironsworn.py
    # --8<-- [start:core]
    from enum import IntEnum

    from dyce import H, HResult, PResult, expand
    from dyce.d import d6, p2d10

    class IronDramaticResult(IntEnum):
        SPECTACULAR_FAILURE = -1
        FAILURE = 0
        WEAK_SUCCESS = 1
        STRONG_SUCCESS = 2
        SPECTACULAR_SUCCESS = 3

        def __repr__(self) -> str:
            return self.name

    def iron_dramatic_dependent_term(
        action: HResult[int],
        challenges: PResult[int],
        *,
        action_mod: int = 0,
    ) -> IronDramaticResult:
        modded_act = action.outcome + action_mod
        assert len(challenges.roll) == 2, "pool must have exactly 2 challenge dice"
        ch1_outcome, ch2_outcome = challenges.roll
        doubles = ch1_outcome == ch2_outcome
        modded_act_beats_ch1 = modded_act > ch1_outcome
        modded_act_beats_ch2 = modded_act > ch2_outcome
        if modded_act_beats_ch1 and modded_act_beats_ch2:
            return (
                IronDramaticResult.SPECTACULAR_SUCCESS
                if doubles
                else IronDramaticResult.STRONG_SUCCESS
            )
        elif modded_act_beats_ch1 or modded_act_beats_ch2:
            return IronDramaticResult.WEAK_SUCCESS
        else:
            return (
                IronDramaticResult.SPECTACULAR_FAILURE
                if doubles
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

    # NOTE: Changes to this section should be propagated to docs-src/nb_ironsworn.py
    # --8<-- [start:table]
    import pandas as pd

    data = [
        {
            outcome.name: float(prob)
            for outcome, prob in H.from_counts(
                result, dict.fromkeys(IronDramaticResult, 0), preserve_zero_counts=True
            ).probability_items()
        }
        for result in results_by_action_mod.values()
    ]

    df = pd.DataFrame(data, index=action_mods)
    df.index.name = "Action Modifier"
    # --8<-- [end:table]

    # Display df as table
    import jinja2  # ruff: ignore[unused-import]

    # NOTE: Translates to df.style.format("{:.2%}") in docs-src/nb_ironsworn.py
    print(df.style.format("{:.2%}").to_html())

    # NOTE: Changes to this section should be propagated to docs-src/nb_ironsworn.py
    # --8<-- [start:viz]
    import matplotlib.ticker as mticker

    ax = df.plot(kind="barh", stacked=True, colormap="RdYlGn")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_title("Ironsworn distributions")
    ax.legend(loc="center")
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot import main

    main(fig_callback)

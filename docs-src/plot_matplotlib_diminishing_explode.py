# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs-src/nb_diminishing_explode.py
    # --8<-- [start:core]
    from dyce import H, HResult
    from dyce.d import d4, d6, d8, d10, d12, d20

    progression = {
        d6: d4,
        d8: d6,
        d10: d8,
        d12: d10,
        d20: d12,
    }

    def diminishing_returns_resolver(
        result: HResult[int],
        _n_left: int,
        _n_done: int,
        *,
        progression: dict[H[int], H[int]],
    ) -> H[int] | int:
        if result.outcome == max(result.h) and result.h in progression:
            return progression[result.h]
        return result.outcome

    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs-src/nb_diminishing_explode.py
    # --8<-- [start:viz]
    import sys
    from functools import partial

    import matplotlib.ticker as mticker

    from dyce import explode_n
    from dyce.viz.matplotlib import plot_ridge

    ax = plot_ridge(
        *(
            explode_n(
                d,
                n=sys.maxsize,  # unrestricted recursion, since our resolver determines how deep we go
                resolver=partial(
                    diminishing_returns_resolver,
                    progression=progression,
                ),
            )
            for d in progression
        ),
        labels=("d6", "d8", "d10", "d12", "d20"),
        cmap="coolwarm",
    )
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    ax.tick_params(axis="x", labelrotation=60)
    ax.set_title("Diminishing explode mechanic for polygonal dice")
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot_matplotlib import main

    main(fig_callback)

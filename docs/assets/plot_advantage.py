# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_advantage.py
    # --8<-- [start:core]
    from dyce import H, HResult, P, expand

    normal_hit = H(12) + 5
    critical_hit = 3 @ H(12) + 5
    advantage = (2 @ P(20)).h(-1)

    def crit(result: HResult[int]) -> H[int] | int:
        if result.outcome == 20:
            return critical_hit
        elif result.outcome + 5 >= 14:
            return normal_hit
        else:
            return 0

    advantage_weighted = expand(crit, advantage)
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_advantage.py
    # --8<-- [start:viz]
    from matplotlib import ticker

    from dyce.viz import plot_line

    ax = plot_line(
        normal_hit,
        critical_hit,
        advantage_weighted,
        labels=["Normal hit", "Critical hit", "Advantage-weighted"],
    )
    ax.xaxis.set_major_locator(ticker.IndexLocator(base=2, offset=1))
    ax.set_title("Advantage-weighted attack with critical hits")
    ax.legend()
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

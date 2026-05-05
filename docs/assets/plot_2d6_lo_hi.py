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
    # NOTE: Changes to this section should be propagated to docs/assets/nb_2d6_lo_hi.py
    # --8<-- [start:core]
    from dyce.d import p2d6

    h2d6_lowest = p2d6.h(0)
    h2d6_highest = p2d6.h(-1)
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_2d6_lo_hi.py
    # --8<-- [start:viz]
    from dyce.viz import plot_bar

    ax = plot_bar(
        h2d6_lowest,
        h2d6_highest,
        labels=("Lowest", "Highest"),
    )
    ax.set_title("Taking the lowest or highest die of 2d6")
    ax.legend()
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

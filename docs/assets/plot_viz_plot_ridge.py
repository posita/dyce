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
    # --8<-- [start:viz]
    from dyce import H
    from dyce.viz.matplotlib import plot_ridge

    ax = plot_ridge(
        2 @ H(10),
        H(8) + H(12),
        labels=["2d10", "d8 + d12"],
    )
    ax.set_title("2d10 vs. d8 + d12")
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

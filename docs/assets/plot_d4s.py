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


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_d4s.py
    # --8<-- [start:core]
    from dyce import H

    d4 = H(4)
    h6d4p15 = 6 @ d4 + 15
    h8d4p10 = 8 @ d4 + 10
    h10d4p5 = 10 @ d4 + 5
    h12d4 = 12 @ d4
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_d4s.py
    # --8<-- [start:viz]
    from dyce.viz.matplotlib import plot_ridge

    ax = plot_ridge(
        h6d4p15,
        h8d4p10,
        h10d4p5,
        h12d4,
        labels=("6d4+15", "8d4+10", "10d4+5", "12d4"),
        cmap="plasma",
        overlap=4.0,
    )
    ax.tick_params(axis="x", labelrotation=60)
    ax.set_title("Various quantities of d4s")
    ax.legend()
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

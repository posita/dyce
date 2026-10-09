# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs-src/nb_3d6_selection.py
    # --8<-- [start:viz]
    from dyce.d import p3d6
    from dyce.viz.matplotlib import plot_ridge

    ax = plot_ridge(
        p3d6.at(0, 1),
        p3d6.at(0, -1),
        p3d6.at(slice(-2, None)),
        labels=("least two", "least and greatest", "greatest two"),
    )
    ax.set_title("Distributions for various selections from 3d6")
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot import main

    main(fig_callback)

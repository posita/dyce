# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs-src/nb_d20_success.py
    # --8<-- [start:core]
    from dyce import H, P

    d20 = H(20)  # shorthand for an evenly-weighted 20-sided die
    p2d20 = 2 @ P(d20)  # a pool of two such dice
    d20_disadvantage = p2d20.at(0)  # left-most index is lowest
    d20_advantage = p2d20.at(-1)  # right-most index is highest
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs-src/nb_d20_success.py
    # --8<-- [start:viz]
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib.patches import Wedge

    from dyce.viz.matplotlib import plot_burst

    _, axes = plt.subplots(1, 2)
    plot_burst(
        d20_advantage,
        d20,
        title="highest of 2d20\nor “advantage” (foreground)\nvs. d20 (background)",
        alpha=0.9,
        ax=axes[0],
        cmap="twilight_shifted",
        compare_cmap="twilight_r",
    )
    plot_burst(
        d20_disadvantage,
        d20,
        title="lowest of 2d20\nor “disadvantage” (foreground)\nvs. d20 (background)",
        alpha=0.9,
        ax=axes[1],
        cmap="twilight_shifted_r",
        compare_cmap="twilight",
    )
    for ax in axes:
        for wedge in (patch for patch in ax.patches if isinstance(patch, Wedge)):
            wedge.set_edgecolor(mpl.rcParams["patch.edgecolor"])
    plt.gcf().set_size_inches(9.6, 6.4)
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot import main

    main(fig_callback)

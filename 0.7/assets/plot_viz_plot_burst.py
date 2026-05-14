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
    from matplotlib import pyplot as plt

    from dyce import H
    from dyce.viz import plot_burst

    ax_d6 = plt.subplot2grid((1, 2), (0, 0))
    plot_burst(
        H(6),
        ax=ax_d6,
    )
    ax_d6.set_title("d6")

    ax_2d6_vs_d12 = plt.subplot2grid((1, 2), (0, 1))
    plot_burst(
        2 @ H(6),
        H(12),
        ax=ax_2d6_vs_d12,
    )
    ax_2d6_vs_d12.set_title("2d6 vs. d12")

    # Style (dark/light) tweaks
    for ax in (ax_d6, ax_2d6_vs_d12):
        ax.title.set_color(line_color)
        for text in ax.texts:
            text.set_color(line_color)  # wedge labels (both rings)
        for patch in ax.patches:
            patch.set_edgecolor(line_color)  # wedge edges (both rings)
    plt.gcf().set_size_inches(6.4, 3.2)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

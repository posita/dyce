# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from anydyce.viz import plot_bar

from dyce import H, P


def do_it(style: str) -> None:
    import matplotlib.pyplot

    p_2d6 = 2 @ P(H(6))
    p_2d6_lowest = p_2d6.h(0)
    p_2d6_highest = p_2d6.h(-1)

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    plot_bar(ax, [("Lowest", p_2d6_lowest), ("Highest", p_2d6_highest)])
    ax.legend()
    ax.set_title("Taking the lowest or highest die of 2d6", color=text_color)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H, P


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker

    p_2d6 = 2 @ P(H(6))

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))

    outcomes, probabilities = p_2d6.h(0).distribution_xy()
    matplotlib.pyplot.bar(
        [v - 0.125 for v in outcomes],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Lowest",
    )

    outcomes, probabilities = p_2d6.h(-1).distribution_xy()
    matplotlib.pyplot.bar(
        [v + 0.125 for v in outcomes],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Highest",
    )

    matplotlib.pyplot.legend()
    matplotlib.pyplot.title("Taking the lowest or highest die of 2d6", color=text_color)

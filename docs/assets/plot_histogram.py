# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
    outcomes, probabilities = (2 @ H(6)).distribution_xy()
    matplotlib.pyplot.bar([str(v) for v in outcomes], probabilities)
    matplotlib.pyplot.title("Distribution for 2d6", color=text_color)

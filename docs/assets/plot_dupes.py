# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from anydyce.viz import plot_scatter

from dyce import P
from dyce.evaluation import PResult, foreach


def do_it(style: str) -> None:
    import matplotlib.pyplot

    def dupes(result: PResult):
        dupes = 0
        for i in range(1, len(result.roll)):
            if result.roll[i] == result.roll[i - 1]:
                dupes += 1
        return dupes

    res_15d6 = foreach(dupes, result=15 @ P(6))
    res_8d10 = foreach(dupes, result=8 @ P(10))

    matplotlib.pyplot.rcParams["lines.markersize"] *= 2
    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    plot_scatter(ax, [("15d6", res_15d6), ("8d10", res_8d10)], alpha=1.0)
    ax.legend()
    ax.set_title("Chances of rolling $n$ duplicates", color=text_color)

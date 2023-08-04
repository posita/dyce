# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from anydyce.viz import plot_line

from dyce import H, P
from dyce.evaluation import HResult, foreach


def do_it(style: str) -> None:
    import matplotlib.pyplot

    normal_hit = H(12) + 5
    critical_hit = 3 @ H(12) + 5
    advantage = (2 @ P(20)).h(-1)

    def crit(result: HResult):
        if result.outcome == 20:
            return critical_hit
        elif result.outcome + 5 >= 14:
            return normal_hit
        else:
            return 0

    advantage_weighted = foreach(crit, result=advantage)

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    plot_line(
        ax,
        [
            ("Normal hit", normal_hit),
            ("Critical hit", critical_hit),
            ("Advantage-weighted", advantage_weighted),
        ],
    )
    ax.legend()
    ax.set_title("Advantage-weighted attack with critical hits", color=text_color)

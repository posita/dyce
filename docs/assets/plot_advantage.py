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

    normal_hit = H(12) + 5
    critical_hit = 3 @ H(12) + 5
    advantage = (2 @ P(20)).h(-1)

    def crit(__: H, outcome):
        if outcome == 20:
            return critical_hit
        elif outcome + 5 >= 14:
            return normal_hit
        else:
            return 0

    advantage_weighted = advantage.substitute(crit)

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
    matplotlib.pyplot.plot(
        *normal_hit.distribution_xy(),
        marker=".",
        label="Normal hit",
    )
    matplotlib.pyplot.plot(
        *critical_hit.distribution_xy(),
        marker=".",
        label="Critical hit",
    )
    matplotlib.pyplot.plot(
        *advantage_weighted.distribution_xy(),
        marker=".",
        label="Advantage-weighted",
    )
    matplotlib.pyplot.legend()
    matplotlib.pyplot.title(
        "Advantage-weighted attack with critical hits",
        color=text_color,
    )

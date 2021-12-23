# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H
from dyce.viz import display_burst


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker

    single_attack = 2 @ H(6) + 5

    def gwf(h: H, outcome):
        return h if outcome in (1, 2) else outcome

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5

    text_color = "white" if style == "dark" else "black"
    fig = matplotlib.pyplot.figure()
    fig.set_size_inches(11, 5.5, forward=True)
    ax_plot = matplotlib.pyplot.subplot2grid((1, 2), (0, 0))
    ax_burst = matplotlib.pyplot.subplot2grid((1, 2), (0, 1))
    label_sa = "Normal attack"
    ax_plot.tick_params(axis="x", colors=text_color)
    ax_plot.tick_params(axis="y", colors=text_color)
    ax_plot.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1))
    ax_plot.plot(
        *single_attack.distribution_xy(),
        color="tab:green",
        label=label_sa,
        marker=".",
    )
    label_gwf = "“Great Weapon Fighting”"
    ax_plot.plot(
        *great_weapon_fighting.distribution_xy(),
        color="tab:blue",
        label=label_gwf,
        marker=".",
    )
    ax_plot.legend()
    display_burst(
        ax_burst,
        h_inner=great_weapon_fighting,
        outer=single_attack,
        desc=f"{label_sa} vs. {label_gwf}",
        inner_color="RdYlBu_r",
        outer_color="RdYlGn_r",
        text_color=text_color,
        alpha=0.9,
    )
    fig.tight_layout()

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from anydyce.viz import plot_burst, plot_line

from dyce import H


def do_it(style: str) -> None:
    import matplotlib.pyplot
    import matplotlib.ticker

    single_attack = 2 @ H(6) + 5

    def gwf(h: H, outcome):
        return h if outcome in (1, 2) else outcome

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5

    text_color = "white" if style == "dark" else "black"
    label_sa = "Normal attack"
    label_gwf = "“Great Weapon Fighting”"
    ax_plot = matplotlib.pyplot.subplot2grid((1, 2), (0, 0))
    ax_plot.tick_params(axis="x", colors=text_color)
    ax_plot.tick_params(axis="y", colors=text_color)
    plot_line(ax_plot, [(label_sa, single_attack), (label_gwf, great_weapon_fighting)])
    ax_plot.lines[0].set_color("tab:green")
    ax_plot.lines[1].set_color("tab:blue")

    # so_far = 0

    # for count, color in zip(
    #     (len(h) for h in (single_attack, great_weapon_fighting)),
    #     ("tab:green", "tab:blue"),
    # ):
    #     for i in range(count):
    #         ax_plot.patches[i + so_far].set_color(color)

    #     so_far += count

    ax_plot.legend()
    ax_burst = matplotlib.pyplot.subplot2grid((1, 2), (0, 1))
    plot_burst(
        ax_burst,
        h_inner=great_weapon_fighting,
        h_outer=single_attack,
        title=f"{label_sa}\nvs.\n{label_gwf}",
        inner_color="RdYlBu_r",
        outer_color="RdYlGn_r",
        text_color=text_color,
    )

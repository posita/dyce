from __future__ import annotations, generator_stop

from dyce import H
from dyce.plt import display_burst


def do_it(style: str) -> None:
    import matplotlib.pyplot

    single_attack = 2 @ H(6) + 5

    def gwf(h: H, outcome):
        return h if outcome in (1, 2) else outcome

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5

    fig = matplotlib.pyplot.figure()
    fig.set_size_inches(10, 10, forward=True)
    plot_ax = matplotlib.pyplot.subplot2grid((2, 2), (0, 0), colspan=2)
    sa_burst_ax = matplotlib.pyplot.subplot2grid((2, 2), (1, 0), colspan=1)
    gwf_burst_ax = matplotlib.pyplot.subplot2grid((2, 2), (1, 1), colspan=1)
    sa_label = "Normal attack"
    plot_ax.plot(
        *single_attack.distribution_xy(),
        color="lightgreen" if style == "dark" else "tab:green",
        label=sa_label,
        marker=".",
    )
    gwf_label = "“Great Weapon Fighting”"
    plot_ax.plot(
        *great_weapon_fighting.distribution_xy(),
        color="lightblue" if style == "dark" else "tab:blue",
        label=gwf_label,
        marker=".",
    )
    plot_ax.legend()
    # Should match the corresponding img[alt] text
    plot_ax.set_title(r"Comparing a normal attack to an enhanced one")
    display_burst(
        sa_burst_ax,
        single_attack,
        desc=sa_label,
        graph_color="RdYlGn_r",
        text_color="white" if style == "dark" else "black",
    )
    display_burst(
        gwf_burst_ax,
        great_weapon_fighting,
        desc=gwf_label,
        graph_color="RdYlBu_r",
        text_color="white" if style == "dark" else "black",
    )

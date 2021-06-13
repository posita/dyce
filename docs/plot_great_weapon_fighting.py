from __future__ import annotations, generator_stop

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    single_attack = 2 @ H(6) + 5

    def gwf(h: H, outcome):
        return h if outcome in (1, 2) else outcome

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5

    outcomes, probabilities = single_attack.distribution_xy()
    matplotlib.pyplot.plot(  # .bar(
        outcomes,  # [v - 0.125 for v in outcomes],
        probabilities,
        marker=".",
        # alpha=0.75,
        # width=0.5,
        label="Normal attack",
    )
    outcomes, probabilities = great_weapon_fighting.distribution_xy()
    matplotlib.pyplot.plot(  # .bar(
        outcomes,  # [v + 0.125 for v in outcomes],
        probabilities,
        marker=".",
        # alpha=0.75,
        # width=0.5,
        label="“Great Weapon Fighting”",
    )
    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(r"Comparing a normal attack to an enhanced one")

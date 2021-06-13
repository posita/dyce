from __future__ import annotations, generator_stop

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    save_roll = H(20)
    burning_arch_damage = 10 @ H(6) + 10
    pass_save = save_roll.ge(10)
    damage_half_on_save = burning_arch_damage // (pass_save + 1)

    outcomes, probabilities = damage_half_on_save.distribution_xy()
    matplotlib.pyplot.plot(outcomes, probabilities, marker=".")
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(
        r"Expected outcomes for attack with saving throw for half damage"
    )

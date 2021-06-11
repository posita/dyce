from __future__ import annotations, generator_stop

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    save_roll = H(20)
    burning_arch_damage = 10 @ H(6) + 10
    pass_save = save_roll.ge(10)
    damage_half_on_save = burning_arch_damage // (pass_save + 1)
    res = damage_half_on_save
    faces, probabilities = res.data_xy()
    matplotlib.pyplot.plot(faces, probabilities, marker=".")

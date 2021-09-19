# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

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
        "Expected outcomes for attack with saving throw for half damage"
    )

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    def roll_and_keep(p: P, k: int):
        assert p.is_homogeneous
        max_d = max(p[-1]) if p else 0
        for roll, count in p.rolls_with_counts():
            total = sum(roll[-k:]) + sum(1 for outcome in roll[:-k] if outcome == max_d)
            yield total, count

    d, k = 6, 3

    for n in range(k + 1, k + 9):
        p = n @ P(d)
        res_roll_and_keep = H(roll_and_keep(p, k))
        matplotlib.pyplot.plot(
            *res_roll_and_keep.distribution_xy(),
            marker="o",
            label=f"{n}d{d} keep {k} add +1",
        )

    for n in range(k + 1, k + 9):
        p = n @ P(d)
        res_normal = p.h(slice(-k, None))
        matplotlib.pyplot.plot(
            *res_normal.distribution_xy(),
            marker="s",
            label=f"{n}d{d} keep {k}",
        )

    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title("Roll-and-keep mechanic comparison")

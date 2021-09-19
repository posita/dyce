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

    res1 = 3 @ H(6)
    p_4d6 = 4 @ P(6)
    res2 = p_4d6.h(slice(1, None))
    d6_reroll_first_one = H(6).substitute(
        lambda h, outcome: H(6) if outcome == 1 else outcome
    )
    p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
    res3 = p_4d6_reroll_first_one.h(slice(1, None))
    p_4d6_reroll_all_ones = 4 @ P(H((2, 3, 4, 5, 6)))
    res4 = p_4d6_reroll_all_ones.h(slice(1, None))
    res5 = 2 @ H(6) + 6
    res6 = 4 @ H(4) + 2

    matplotlib.pyplot.plot(
        *res1.distribution_xy(),
        marker="D",
        label="3d6",
    )
    matplotlib.pyplot.plot(
        *res2.distribution_xy(),
        marker="s",
        label="4d6 - discard lowest",
    )
    matplotlib.pyplot.plot(
        *res3.distribution_xy(),
        marker="^",
        label="4d6 - re-roll first 1, discard lowest",
    )
    matplotlib.pyplot.plot(
        *res4.distribution_xy(),
        marker="*",
        label="4d6 - re-roll all 1s (i.e., 4d5), discard lowest",
    )
    matplotlib.pyplot.plot(
        *res5.distribution_xy(),
        marker="x",
        label="2d6 + 6",
    )
    matplotlib.pyplot.plot(
        *res6.distribution_xy(),
        marker="o",
        label="4d4 + 2",
    )
    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title("Comparing various take-three-of-4d6 methods")

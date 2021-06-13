from __future__ import annotations, generator_stop

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    p_4d6 = 4 @ P(6)
    res1 = p_4d6.h(slice(1, None))
    d6_reroll_first_one = H(6).substitute(
        lambda h, outcome: H(6) if outcome == 1 else outcome
    )
    p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
    res2 = p_4d6_reroll_first_one.h(slice(1, None))
    p_4d6_reroll_all_ones = 4 @ P(H(range(2, 7)))
    res3 = p_4d6_reroll_all_ones.h(slice(1, None))

    matplotlib.pyplot.plot(
        *res1.distribution_xy(),
        marker=".",
        label="Discard lowest",
    )
    matplotlib.pyplot.plot(
        *res2.distribution_xy(),
        marker=".",
        label="Re-roll first 1; discard lowest",
    )
    matplotlib.pyplot.plot(
        *res3.distribution_xy(),
        marker=".",
        label="Re-roll all 1s; discard lowest",
    )
    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(r"Comparing various take-three-of-4d6 methods")

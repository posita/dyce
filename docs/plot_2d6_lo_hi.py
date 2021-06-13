from __future__ import annotations, generator_stop

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    p_2d6 = 2 @ P(H(6))
    outcomes, probabilities = p_2d6.h(0).distribution_xy()
    matplotlib.pyplot.bar(
        [v - 0.125 for v in outcomes],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Lowest",
    )

    outcomes, probabilities = p_2d6.h(-1).distribution_xy()
    matplotlib.pyplot.bar(
        [v + 0.125 for v in outcomes],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Highest",
    )

    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(r"Taking the lowest or highest die of 2d6")

from __future__ import annotations, generator_stop

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    p_2d6 = 2 @ P(H(6))
    faces, probabilities = p_2d6.h(0).data_xy()
    matplotlib.pyplot.bar(
        [f - 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Lowest die of 2d6",
    )

    faces, probabilities = p_2d6.h(-1).data_xy()
    matplotlib.pyplot.bar(
        [f + 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Highest die of 2d6",
    )

    matplotlib.pyplot.legend()

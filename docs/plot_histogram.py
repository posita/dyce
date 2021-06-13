from __future__ import annotations, generator_stop

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    outcomes, probabilities = (2 @ H(6)).distribution_xy()
    matplotlib.pyplot.bar([str(v) for v in outcomes], probabilities)
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(r"Distribution for 2d6")

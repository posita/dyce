from __future__ import annotations, generator_stop

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    res = (10 @ P(H(10).explode(max_depth=3))).h(slice(-3, None))

    matplotlib.pyplot.plot(*res.distribution_xy(), marker=".")
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title(r"Modeling taking the three highest of ten exploding d10s")

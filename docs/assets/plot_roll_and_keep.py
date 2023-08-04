# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from typing import Iterator

from anydyce.viz import plot_line

from dyce import H, P


def do_it(style: str) -> None:
    import matplotlib.pyplot

    def roll_and_keep(p: P, k: int):
        assert p.is_homogeneous()
        max_d = max(p[-1]) if p else 0

        for roll, count in p.rolls_with_counts():
            total = sum(roll[-k:]) + sum(1 for outcome in roll[:-k] if outcome == max_d)
            yield total, count

    d, k = 6, 3

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    marker_start = 0

    def _roll_and_keep_hs() -> Iterator[tuple[str, H]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k} add +1", H(roll_and_keep(p, k))

    plot_line(ax, tuple(_roll_and_keep_hs()), alpha=0.75)

    for i in range(marker_start, len(ax.lines)):
        ax.lines[i].set_marker(".")

    marker_start = len(ax.lines)

    def _normal() -> Iterator[tuple[str, H]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k}", p.h(slice(-k, None))

    plot_line(ax, tuple(_normal()), alpha=0.25)

    for i in range(marker_start, len(ax.lines)):
        ax.lines[i].set_marker("o")

    ax.legend(loc="upper left")
    ax.set_title("Roll-and-keep mechanic comparison", color=text_color)

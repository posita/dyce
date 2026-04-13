# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path

from _plot import main, name_from_path  # pyrefly: ignore[missing-import]

from dyce import H, P
from dyce.viz import plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    def roll_and_keep(p: P[int], k: int) -> H[int]:
        assert all(h == p[0] for h in p), "pool must be homogeneous"
        max_d = max(p[-1]) if p else 0
        return H.from_counts(
            (
                sum(roll[-k:]) + sum(1 for outcome in roll[:-k] if outcome == max_d),
                count,
            )
            for roll, count in p.rolls_with_counts()
        )

    d, k = 6, 3

    def roll_and_keep_hs() -> Iterator[tuple[str, H[int]]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k} add +1", roll_and_keep(p, k)

    def normal() -> Iterator[tuple[str, H[int]]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k}", p.h(slice(-k, None))

    pairs1 = tuple(normal())
    pairs2 = tuple(roll_and_keep_hs())

    text_color = "white" if args.style == "dark" else "black"
    labels1, hs1 = zip(*pairs1, strict=True)
    ax = plot_line(*hs1, labels=labels1, markers=".", alpha=0.75)

    labels2, hs2 = zip(*pairs2, strict=True)
    plot_line(*hs2, labels=labels2, markers="o", alpha=0.25, ax=ax)

    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.legend(loc="upper left")
    ax.set_title("Roll-and-keep mechanic comparison", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

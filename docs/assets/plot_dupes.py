# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from argparse import Namespace
from pathlib import Path

from _plot import main, name_from_path  # pyrefly: ignore[missing-import]

from dyce import H, P
from dyce.viz import plot_bar

_LOGGER = logging.getLogger(__name__)


def _count_dupes(pool: P) -> H[int]:
    return H.from_counts(
        (sum(1 for i in range(1, len(roll)) if roll[i] == roll[i - 1]), count)
        for roll, count in pool.rolls_with_counts()
    )


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    res_15d6 = _count_dupes(15 @ P(6))
    res_8d10 = _count_dupes(8 @ P(10))

    text_color = "white" if args.style == "dark" else "black"
    ax = plot_bar(res_15d6, res_8d10, labels=["15d6", "8d10"])
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.legend()
    ax.set_title("Chances of rolling $n$ duplicates", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

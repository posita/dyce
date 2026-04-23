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

from dyce import H, P, explode_n
from dyce.viz import plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    pairs = [
        (f"{depth} rerolls", (10 @ P(explode_n(H(10), n=depth))).h(slice(-3, None)))
        for depth in range(5, -1, -1)
    ]
    labels, hs = zip(*pairs, strict=True)

    text_color = "white" if args.style == "dark" else "black"
    ax = plot_line(*hs, labels=labels)
    for line in ax.lines:
        line.set_marker("")
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.legend()
    ax.set_title("Taking the three highest of ten exploding d10s", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

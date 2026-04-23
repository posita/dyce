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

from dyce import H
from dyce.viz import plot_bar

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    text_color = "white" if args.style == "dark" else "black"
    ax = plot_bar(
        2 @ H(6),
        H(12),
        labels=["2d6", "d12"],
    )
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.set_title("2d6 vs. d12", color=text_color)
    ax.legend(loc="upper right")


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

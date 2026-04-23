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
from matplotlib import pyplot as plt

from dyce import H
from dyce.viz import plot_burst

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    text_color = "white" if args.style == "dark" else "black"
    ax_d6 = plt.subplot2grid((1, 2), (0, 0))
    plot_burst(H(6), ax=ax_d6, text_color=text_color)
    ax_d6.set_title("d6", color=text_color)
    ax_2d6_vs_d12 = plt.subplot2grid((1, 2), (0, 1))
    plot_burst(
        2 @ H(6),
        H(12),
        ax=ax_2d6_vs_d12,
        text_color=text_color,
    )
    ax_2d6_vs_d12.set_title("2d6 vs. d12", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

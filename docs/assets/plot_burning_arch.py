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
from matplotlib import ticker

from dyce import H
from dyce.viz import plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    save_roll = H(20)
    burning_arch_damage = 10 @ H(6) + 10
    pass_save = save_roll.ge(10)
    damage_half_on_save = burning_arch_damage // (pass_save + 1)

    text_color = "white" if args.style == "dark" else "black"
    ax = plot_line(damage_half_on_save)
    ax.xaxis.set_major_locator(ticker.IndexLocator(base=2, offset=0))
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.set_title("Attack with saving throw for half damage", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

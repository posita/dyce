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

from dyce import H, HResult, P, expand
from dyce.viz import plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    normal_hit = H(12) + 5
    critical_hit = 3 @ H(12) + 5
    advantage = (2 @ P(20)).h(-1)

    def crit(result: HResult[int]) -> H[int] | int:
        if result.outcome == 20:
            return critical_hit
        elif result.outcome + 5 >= 14:
            return normal_hit
        else:
            return 0

    advantage_weighted = expand(crit, advantage)

    text_color = "white" if args.style == "dark" else "black"
    ax = plot_line(
        normal_hit,
        critical_hit,
        advantage_weighted,
        labels=["Normal hit", "Critical hit", "Advantage-weighted"],
    )
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.legend()
    ax.set_title("Advantage-weighted attack with critical hits", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

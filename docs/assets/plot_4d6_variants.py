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

from dyce import H, P, expand
from dyce.viz import plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    p_4d6 = 4 @ P(6)
    d6_reroll_first_one = expand(
        lambda result: result.h if result.outcome == 1 else result.outcome,
        H(6),
    )
    p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
    p_4d6_reroll_all_ones = 4 @ P(H(5) + 1)

    attr_results: dict[str, H] = {
        "3d6": 3 @ H(6),
        "4d6 - discard lowest": p_4d6.h(slice(1, None)),
        "4d6 - re-roll first 1, discard lowest": p_4d6_reroll_first_one.h(
            slice(1, None)
        ),
        "4d6 - re-roll all 1s (i.e., 4d(1d5 + 1)), discard lowest": p_4d6_reroll_all_ones.h(
            slice(1, None)
        ),
        "2d6 + 6": 2 @ H(6) + 6,
        "4d4 + 2": 4 @ H(4) + 2,
    }

    labels, hs = zip(*attr_results.items(), strict=True)
    text_color = "white" if args.style == "dark" else "black"
    ax = plot_line(*hs, labels=labels, markers="Ds^*xo")
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    ax.legend()
    ax.set_title("Comparing various take-three-of-4d6 methods", color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

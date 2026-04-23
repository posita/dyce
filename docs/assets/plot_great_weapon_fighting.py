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

from dyce import H, HResult, expand
from dyce.viz import plot_burst, plot_line

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    single_attack = 2 @ H(6) + 5

    def gwf(result: HResult[int]) -> H[int] | int:
        return result.h if result.outcome in (1, 2) else result.outcome

    great_weapon_fighting = 2 @ expand(gwf, H(6)) + 5

    text_color = "white" if args.style == "dark" else "black"
    label_sa = "Normal attack"
    label_gwf = "\u201cGreat Weapon Fighting\u201d"

    ax_plot = plt.subplot2grid((1, 2), (0, 0))
    plot_line(
        single_attack, great_weapon_fighting, labels=[label_sa, label_gwf], ax=ax_plot
    )
    ax_plot.lines[0].set_color("tab:green")
    ax_plot.lines[1].set_color("tab:blue")
    ax_plot.tick_params(axis="x", colors=text_color)
    ax_plot.tick_params(axis="y", colors=text_color)
    ax_plot.legend()

    ax_burst = plt.subplot2grid((1, 2), (0, 1))
    plot_burst(
        great_weapon_fighting,
        single_attack,
        cmap="RdYlBu_r",
        compare_cmap="RdYlGn_r",
        title=f"{label_sa}\nvs.\n{label_gwf}",
        text_color=text_color,
        ax=ax_burst,
    )


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

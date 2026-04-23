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

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    col_names = ["Loss", "Tie", "Win"]
    col_ticks = list(range(len(col_names)))
    num_scenarios = 3
    text_color = "white" if args.style == "dark" else "black"

    for i, them in enumerate(range(3, 3 + num_scenarios)):
        ax = plt.subplot(1, num_scenarios, i + 1)
        row_names: list[str] = []
        rows: list[tuple[float, ...]] = []
        num_rows = 3

        for us in range(them, them + num_rows):
            row_names.append(f"{us}d6 …")
            diff = (us @ H(6)) - (them @ H(6))
            prob_by_outcome = {o: float(p) for o, p in diff.probability_items()}
            p_loss = sum(v for k, v in prob_by_outcome.items() if k < 0)
            p_tie = prob_by_outcome.get(0, 0.0)
            p_win = sum(v for k, v in prob_by_outcome.items() if k > 0)
            rows.append((p_loss, p_tie, p_win))

        ax.imshow(rows)
        ax.set_title(f"… vs. {them}d6", color=text_color)
        ax.set_xticks(col_ticks)
        ax.set_xticklabels(col_names, color=text_color, rotation=90)
        ax.set_yticks(list(range(len(rows))))
        ax.set_yticklabels(row_names, color=text_color)

        for y in range(len(row_names)):
            for x in range(len(col_names)):
                ax.text(
                    x,
                    y,
                    f"{rows[y][x]:.0%}",
                    ha="center",
                    va="center",
                    color="w",
                )


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

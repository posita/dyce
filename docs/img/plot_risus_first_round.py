# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from typing import List, Tuple

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    col_names = ["Loss", "Tie", "Win"]
    col_ticks = list(range(len(col_names)))
    num_scenarios = 3
    fig, axes = matplotlib.pyplot.subplots(1, num_scenarios)

    for i, them in enumerate(range(3, 3 + num_scenarios)):
        ax = axes[i]
        row_names: List[str] = []
        rows: List[Tuple[float, ...]] = []
        num_rows = 3

        for us in range(them, them + num_rows):
            row_names.append(f"{us}d6 …")
            rows.append((us @ H(6)).vs(them @ H(6)).distribution_xy()[-1])
        _ = ax.imshow(rows)

        ax.set_title(f"… vs {them}d6")
        ax.set_xticks(col_ticks)
        ax.set_xticklabels(col_names, rotation=90)
        ax.set_yticks(list(range(len(rows))))
        ax.set_yticklabels(row_names)

        for y in range(len(row_names)):
            for x in range(len(col_names)):
                _ = ax.text(
                    x,
                    y,
                    f"{rows[y][x]:.0%}",
                    ha="center",
                    va="center",
                    color="w",
                )

    fig.tight_layout()

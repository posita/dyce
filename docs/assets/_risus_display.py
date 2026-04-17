# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from collections.abc import Iterator, Sequence

import matplotlib as mpl
from _risus_data import ThemTable, Versus  # pyrefly: ignore[missing-import]
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

__all__ = (
    "us_vs_them_heatmap_subplot",
    "us_vs_them_md_table",
)


def us_vs_them_md_table(
    title: str,
    data: Sequence[ThemTable],
) -> str:
    table_data: list[tuple[str, dict[str, float]]] = []

    for them_map in data:
        table_data.append(("", {}))  # blank row
        table_data.extend(
            (
                f"our {us_row.our_pool_size}d6 vs. their {them_map.their_pool_size}d6",
                {vs.name: float(prob) for vs, prob in us_row.data.items()},
            )
            for us_row in them_map.results
        )

    def _md_table_rows() -> Iterator[str]:
        yield (f"| {title} | " + " | ".join(vs.name for vs in Versus) + " |")
        yield ("|:---:|" + ":---:|" * len(Versus))
        for row_label, row in table_data:
            if row_label:
                yield (
                    f"| {row_label} | "
                    + " | ".join(f"{prob:0.2%}" for prob in row.values())
                    + " |"
                )
            else:
                yield ("|  |" + "  |" * len(Versus))  # blank row

    return "\n".join(_md_table_rows())


def us_vs_them_heatmap_subplot(
    data: Sequence[ThemTable],
    cmap_name: str = "viridis",
    plt_rows: int = 1,
    plt_row: int = 1,
    ax_color: str = "black",
) -> list[Axes]:
    axes: list[Axes] = []
    col_names = [e.name for e in Versus]
    col_ticks = list(range(len(Versus)))
    cmap = mpl.colormaps[cmap_name]
    lo_color = cmap(100.0)
    hi_color = cmap(0.0)

    for i, them_map in enumerate(data):
        ax = plt.subplot(plt_rows, len(data), (plt_row - 1) * len(data) + i + 1)
        # imshow wants just values, not dicts
        rows = [
            [float(prob) for prob in us_row.data.values()]
            for us_row in them_map.results
        ]
        row_names = [f"our\n{us_row.our_pool_size}d6 …" for us_row in them_map.results]
        row_ticks = list(range(len(rows)))
        ax.imshow(rows, vmin=0.0, vmax=1.0, cmap=cmap_name)
        ax.set_title(f"… vs. their {them_map.their_pool_size}d6", color=ax_color)
        ax.set_xticks(col_ticks)
        ax.set_xticklabels(col_names, color=ax_color)
        ax.set_yticks(row_ticks)
        ax.set_yticklabels(row_names, color=ax_color)
        for y, row in enumerate(rows):
            for x, val in enumerate(row):
                ax.text(
                    x,
                    y,
                    f"{val:.0%}",
                    ha="center",
                    va="center",
                    color=hi_color if val > 0.5 else lo_color,
                )
        axes.append(ax)

    return axes

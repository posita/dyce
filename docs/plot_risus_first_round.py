from typing import List, Tuple
import os
from dyce import H


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"

    col_names = ["Loss", "Tie", "Win"]
    col_ticks = list(range(len(col_names)))
    num_scenarios = 3
    fig, axes = matplotlib.pyplot.subplots(1, num_scenarios)

    for i, them in enumerate(range(3, 3 + num_scenarios)):
        ax = axes[i]
        row_names = []  # type: List[str]
        rows = []  # type: List[Tuple[float, ...]]
        num_rows = 3

        for us in range(them, them + num_rows):
            row_names.append("{}d6 …".format(us))
            rows.append((us @ H(6)).vs(them @ H(6)).data_xy(relative=True)[-1])
        _ = ax.imshow(rows)

        ax.set_title("… vs {}d6".format(them))
        ax.set_xticks(col_ticks)
        ax.set_xticklabels(col_names, rotation=90)
        ax.set_yticks(list(range(len(rows))))
        ax.set_yticklabels(row_names)

        for y in range(len(row_names)):
            for x in range(len(col_names)):
                _ = ax.text(
                    x,
                    y,
                    "{:.0%}".format(rows[y][x]),
                    ha="center",
                    va="center",
                    color="w",
                )

    fig.tight_layout()
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from dyce import H


def do_it(style: str) -> None:
    import matplotlib.pyplot

    col_names = ["Loss", "Tie", "Win"]
    col_ticks = list(range(len(col_names)))
    num_scenarios = 3
    text_color = "white" if style == "dark" else "black"

    for i, them in enumerate(range(3, 3 + num_scenarios)):
        ax = matplotlib.pyplot.subplot(1, num_scenarios, i + 1)
        row_names: list[str] = []
        rows: list[tuple[float, ...]] = []
        num_rows = 3

        for us in range(them, them + num_rows):
            row_names.append(f"{us}d6 …")
            results = (us @ H(6)).vs(them @ H(6))
            rows.append(results.distribution_xy()[-1])

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

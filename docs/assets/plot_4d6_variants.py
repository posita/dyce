# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from anydyce.viz import plot_line

from dyce import H, P
from dyce.evaluation import explode


def do_it(style: str) -> None:
    import matplotlib.pyplot

    p_4d6 = 4 @ P(6)
    d6_reroll_first_one = explode(H(6), lambda result: result.outcome == 1)
    p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
    p_4d6_reroll_all_ones = 4 @ P(H(5) + 1)

    markers = "Ds^*xo"
    attr_results: dict[str, H] = {
        "3d6": 3 @ H(6),  # marker="D"
        "4d6 - discard lowest": p_4d6.h(slice(1, None)),  # marker="s"
        "4d6 - re-roll first 1, discard lowest": p_4d6_reroll_first_one.h(
            slice(1, None)
        ),  # marker="^"
        "4d6 - re-roll all 1s (i.e., 4d(1d5 + 1)), discard lowest": p_4d6_reroll_all_ones.h(
            slice(1, None)
        ),  # marker="*"
        "2d6 + 6": 2 @ H(6) + 6,  # marker="x"
        "4d4 + 2": 4 @ H(4) + 2,  # marker="o"
    }

    ax = matplotlib.pyplot.axes()
    text_color = "white" if style == "dark" else "black"
    ax.tick_params(axis="x", colors=text_color)
    ax.tick_params(axis="y", colors=text_color)
    plot_line(
        ax,
        [(label, res) for label, res in attr_results.items()],
    )

    for line, marker in zip(ax.lines, markers):
        line.set_marker(marker)

    ax.legend()
    ax.set_title("Comparing various take-three-of-4d6 methods", color=text_color)

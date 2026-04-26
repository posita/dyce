# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_4d6_variants.py
    # --8<-- [start:core]
    from dyce import H, P, expand

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
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_4d6_variants.py
    # --8<-- [start:viz]
    from matplotlib import pyplot as plt

    from dyce.viz import plot_burst, plot_line

    labels, hs = zip(*attr_results.items(), strict=True)

    ax_lines = plt.subplot2grid((3, 3), (0, 0), colspan=3)
    plot_line(*hs, labels=labels, markers="Ds^*xo", ax=ax_lines)
    ax_lines.legend()
    ax_lines.set_title("Comparing various take-three-of-4d6 methods")

    for i, (label, h) in enumerate(attr_results.items()):
        ax_burst = plt.subplot2grid((3, 3), (1 + i // 3, i % 3))
        plot_burst(h, title=label, ax=ax_burst)
        ax_burst.set_title(ax_burst.get_title(), wrap=True)

    plt.gcf().set_size_inches(9.6, 9.6)
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    for ax in plt.gcf().get_axes():
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        for text in ax.texts:
            text.set_color(line_color)
        for patch in ax.patches:
            patch.set_edgecolor(line_color)
        ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

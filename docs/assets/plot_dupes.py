# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_dupes.py
    # --8<-- [start:core]
    from dyce import H, P

    def count_dupes(pool: P) -> H[int]:
        return H.from_counts(
            (sum(1 for i in range(1, len(roll)) if roll[i] == roll[i - 1]), count)
            for roll, count in pool.rolls_with_counts()
        )

    res_15d6 = count_dupes(15 @ P(6))
    res_8d10 = count_dupes(8 @ P(10))
    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_dupes.py
    # --8<-- [start:viz]
    from dyce.viz import plot_bar

    ax = plot_bar(res_15d6, res_8d10, labels=["15d6", "8d10"])
    ax.set_title("Chances of rolling $n$ duplicates")
    ax.legend()
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

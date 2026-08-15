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
    # NOTE: Changes to this section should be propagated to docs/assets/nb_roll_and_keep.py
    # --8<-- [start:core]
    from collections.abc import Iterator

    from dyce import H, P

    def roll_and_keep(p: P[int], k: int) -> H[int]:
        assert all(h == p[0] for h in p), "pool must be homogeneous"
        max_d = max(p[-1]) if p else 0
        return H.from_counts(
            (
                sum(roll[-k:]) + sum(1 for outcome in roll[:-k] if outcome == max_d),
                count,
            )
            for roll, count in p.rolls_with_counts()
        )

    d, k = 6, 3

    def roll_and_keep_hs() -> Iterator[tuple[str, H[int]]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k} add +1", roll_and_keep(p, k)

    def normal() -> Iterator[tuple[str, H[int]]]:
        for n in range(k + 1, k + 9):
            p = n @ P(d)
            yield f"{n}d{d} keep {k}", p.h(slice(-k, None))

    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_roll_and_keep.py
    # --8<-- [start:viz]
    from matplotlib import pyplot as plt

    from dyce.viz.matplotlib import plot_burst

    labels1, hs1 = zip(*tuple(normal()), strict=True)
    labels2, hs2 = zip(*tuple(roll_and_keep_hs()), strict=True)
    assert len(hs1) == len(hs2)
    cols = 2
    for i, (h1, h2, label) in enumerate(
        zip(
            hs1,
            hs2,
            (
                f"{label1} vs.\n{label2}"
                for label1, label2 in zip(labels1, labels2, strict=True)
            ),
            strict=True,
        )
    ):
        ax = plt.subplot2grid(
            (len(hs1) // cols + len(hs1) % cols, cols), (i // cols, i % cols)
        )
        plot_burst(h2, h1, compare_cmap="cividis", title=label, ax=ax)
        ax.set_title(ax.get_title(), wrap=True)
    plt.gcf().set_size_inches(9.6, 14.4)
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    for ax in plt.gcf().axes:
        ax.title.set_color(line_color)
        for text in ax.texts:
            text.set_color(line_color)  # wedge labels (both rings)
        for patch in ax.patches:
            patch.set_edgecolor(line_color)  # wedge edges (both rings)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

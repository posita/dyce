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
    from dyce.viz import plot_line

    labels1, hs1 = zip(*tuple(normal()), strict=True)
    ax = plot_line(*hs1, labels=labels1, markers=".", alpha=0.75)

    labels2, hs2 = zip(*tuple(roll_and_keep_hs()), strict=True)
    plot_line(*hs2, labels=labels2, markers="o", alpha=0.25, ax=ax)

    ax.set_title("Roll-and-keep mechanic comparison")
    ax.legend(loc="upper left")
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

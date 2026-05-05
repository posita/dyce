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
    # NOTE: Changes to this section should be propagated to docs/assets/nb_d10_explode.py
    # --8<-- [start:core]
    from math import ceil

    from dyce import H, P, explode_n

    explode_depth = 2

    def keep(p: P[int], k: int) -> H[int]:
        r"Negative k keeps lowest, otherwise keeps highest"
        return p.h(slice(-k, None) if k > 0 else slice(-k))

    def nkk(n: int, k: int) -> H[int]:
        # TODO(posita): <https://github.com/facebook/pyrefly/issues/3236>
        return keep(n @ P(explode_n(H(10), n=explode_depth)), k=k)  # pyrefly: ignore[no-matching-overload]

    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_d10_explode.py
    # --8<-- [start:viz]
    from matplotlib import pyplot as plt
    from matplotlib import ticker

    from dyce.viz import plot_line

    # Range: [start_k..end_k)
    k_start, k_end = 3, 6
    # Range: [start_n..end_n)
    n_start, n_end = 5, 11
    # For normalizing axes scale
    all_nkk: list[H[int]] = []

    for k in range(k_start, k_end):
        label_value_pairs = [(f"{n}k{k}", nkk(n, k)) for n in range(n_start, n_end)]
        labels, hs = zip(*label_value_pairs, strict=True)
        all_nkk.extend(hs)
        ax = plt.subplot2grid((k_end - k_start, 1), (k - k_start, 0))
        plot_line(*hs, labels=labels, ax=ax)
        for line in ax.lines:
            line.set_marker("")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.tick_params(axis="x", labelrotation=60)
        ax.set_title(f"Taking the {k} highest of $n$ exploding d10s")
        ax.legend()

    max_x = max(max(h) for h in all_nkk)
    max_y = max(prob for h in all_nkk for _, prob in h.probability_items())
    for ax in plt.gcf().get_axes():
        ax.set_xlim(left=0, right=max_x)
        ax.set_ylim(top=ceil(max_y * 100) / 100)
    plt.gcf().set_size_inches(6.4, 8.0)
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    for ax in plt.gcf().get_axes():
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

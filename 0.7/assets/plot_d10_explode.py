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


def fig_callback() -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_d10_explode.py
    # --8<-- [start:core]
    from dyce import H, P, explode_n

    explode_depth = 2

    def keep(p: P[int], k: int) -> H[int]:
        r"Negative k keeps lowest, otherwise keeps highest"
        return p.h(slice(-k, None) if k > 0 else slice(-k))

    def nkk(n: int, k: int) -> H[int]:
        return keep(n @ P(explode_n(H(10), n=explode_depth)), k=k)

    # --8<-- [end:core]

    # NOTE: Changes to this section should be propagated to docs/assets/nb_d10_explode.py
    # --8<-- [start:viz]
    from matplotlib import pyplot as plt
    from matplotlib import ticker

    from dyce.viz.matplotlib import plot_ridge

    k_start, k_end = 3, 6  # range: [start_k..end_k)
    n_start, n_end = 5, 11  # range: [start_n..end_n)
    rows_by_k = {
        k: [(f"{n}k{k}", nkk(n, k)) for n in range(n_start, n_end)]
        for k in range(k_start, k_end)
    }
    max_x = max(max(h) for rows in rows_by_k.values() for _, h in rows)
    max_y = max(
        float(prob)
        for rows in rows_by_k.values()
        for _, h in rows
        for _, prob in h.probability_items()
    )
    for k, rows in rows_by_k.items():
        labels, hs = zip(*rows, strict=True)
        ax = plt.subplot2grid((k_end - k_start, 1), (k - k_start, 0))
        plot_ridge(*hs, labels=labels, cmap="cool", peak=max_y, ax=ax)
        for line in ax.lines:
            line.set_marker("")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.tick_params(axis="x", labelrotation=60)
        ax.set_title(f"Taking the {k} highest of $n$ exploding d10s")
        ax.set_xlim(left=0, right=max_x)  # subplots should share a horizontal scale
    # subplots should share a vertical scale
    axes = plt.gcf().get_axes()
    y_lims = [ax.get_ylim() for ax in axes]
    for ax in axes:
        ax.set_ylim(min(lo for lo, _ in y_lims), max(hi for _, hi in y_lims))
    plt.gcf().set_size_inches(6.4, 8.0)
    # --8<-- [end:viz]


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

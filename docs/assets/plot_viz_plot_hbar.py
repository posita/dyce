# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback(line_color: str) -> None:
    from dyce import H
    from dyce.viz import plot_bar

    ax = plot_bar(
        2 @ H(6),
        H(12),
        horizontal=True,
        labels=["2d6", "d12"],
    )
    ax.set_title("2d6 vs. d12")
    ax.legend(loc="upper right")

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

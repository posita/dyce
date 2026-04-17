# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================


def fig_callback(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_histogram.py
    # --8<-- [start:viz]
    from dyce.d import h3d6
    from dyce.viz import plot_bar

    ax = plot_bar(h3d6)
    ax.set_title("Distribution for 3d6")
    # --8<-- [end:viz]

    # Style (dark/light) tweaks
    ax.tick_params(axis="x", colors=line_color)
    ax.tick_params(axis="y", colors=line_color)
    ax.title.set_color(line_color)


if __name__ == "__main__":
    from _plot import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

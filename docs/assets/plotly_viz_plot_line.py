# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dyce.viz.plotly import PlotSpec


def fig_callback() -> "PlotSpec":
    # --8<-- [start:viz]
    from dyce import H
    from dyce.viz.plotly import line_spec

    spec = line_spec(
        2 @ H(10),
        H(8) + H(12),
        labels=["2d10", "d8 + d12"],
        colors=["#1f77b4", "#d62728"],
    )
    spec.layout.update(
        {
            "title": {"text": "2d10 vs. d8 + d12"},
            "margin": {"l": 55, "r": 20, "t": 50, "b": 45},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        }
    )
    # --8<-- [end:viz]

    return spec


if __name__ == "__main__":
    from _plotly import main  # pyrefly: ignore[missing-import]

    main(fig_callback)

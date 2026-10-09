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
    from dyce.d import p3d6
    from dyce.viz.plotly import ridge_spec

    spec = ridge_spec(
        p3d6.at(0, 1),
        p3d6.at(0, -1),
        p3d6.at(slice(-2, None)),
        labels=("least two", "least and greatest", "greatest two"),
        colors=["#348abd", "#a60628", "#7a68a6"],
    )
    spec.layout.update(
        {
            "title": {"text": "Distributions for various selections from 3d6"},
            "margin": {"l": 55, "r": 20, "t": 50, "b": 45},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        }
    )
    # --8<-- [end:viz]

    return spec


if __name__ == "__main__":
    from _plotly import main

    main(fig_callback)

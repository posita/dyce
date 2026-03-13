# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from typing import TYPE_CHECKING

from dyce.r import R

if TYPE_CHECKING:
    from .graph import COLORS, digraph, graphviz_walk
else:
    from graph import COLORS, digraph, graphviz_walk


def do_it(style: str) -> object:
    g = digraph(style)
    colors_by_index = tuple(name for name in COLORS[style] if name != "line")
    r_filter = R.filter_from_sources_iterable(
        lambda outcome: bool(outcome.is_odd().value),
        sources=(
            R.from_value(
                i,
                annotation={
                    "node": {
                        "color": COLORS[style][colors_by_index[i]],
                        "fontcolor": COLORS[style][colors_by_index[i]],
                        "style": "dashed",
                    },
                    "edge": {
                        "color": COLORS[style][colors_by_index[i]],
                        "fontcolor": COLORS[style][colors_by_index[i]],
                        "style": "dashed",
                    },
                },
            )
            for i in range(6)
        ),
    )
    graphviz_walk(g, r_filter.roll())

    return g

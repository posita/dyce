# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import random

from graph import COLORS, Dot, digraph, graphviz_walk

from dyce import H, rng
from dyce.r import ValueRoller


def do_it(style: str) -> Dot:
    # ---- BEGIN MONKEY PATCH ----
    # For deterministic outcomes
    rng.RNG = random.Random(1633438430)
    # ----- END MONKEY PATCH -----

    g = digraph(style)
    d12 = H(12)
    r_d12 = ValueRoller(
        d12,
        annotation={
            "node": {
                "color": COLORS[style]["blue"],
                "fontcolor": COLORS[style]["blue"],
                "style": "dashed",
            },
            "edge": {
                "color": COLORS[style]["blue"],
                "fontcolor": COLORS[style]["blue"],
                "style": "dashed",
            },
        },
    )
    r_4 = ValueRoller(
        4,
        annotation={
            "node": {
                "color": COLORS[style]["red"],
                "fontcolor": COLORS[style]["red"],
                "style": "dashed",
            },
            "edge": {
                "color": COLORS[style]["red"],
                "fontcolor": COLORS[style]["red"],
                "style": "dashed",
            },
        },
    )
    r_d12_add_4 = r_d12 + r_4
    graphviz_walk(g, r_d12_add_4.roll())

    return g

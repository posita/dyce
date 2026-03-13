# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import random
from typing import TYPE_CHECKING

from dyce import H, rng
from dyce.r import CoalesceMode, R, SubstitutionRoller

if TYPE_CHECKING:
    from .graph import COLORS, digraph, graphviz_walk
else:
    from graph import COLORS, digraph, graphviz_walk


def do_it(style: str) -> object:
    # ---- BEGIN MONKEY PATCH ----
    # For deterministic outcomes
    rng.RNG = random.Random(1639492287)
    # ----- END MONKEY PATCH -----

    g = digraph(style)
    r_d6 = R.from_value(
        H(6),
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
    r_append = SubstitutionRoller(
        lambda outcome: r_d6.roll() if outcome.value == 1 else outcome,
        r_d6,
        CoalesceMode.APPEND,
        max_depth=2,
    )
    graphviz_walk(g, r_append.roll())

    return g

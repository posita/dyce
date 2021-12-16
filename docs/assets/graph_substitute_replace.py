# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import random

from graph import Dot, digraph, graphviz_walk

from dyce import H, rng
from dyce.r import R, SubstitutionRoller


def do_it(style: str) -> Dot:
    # ---- BEGIN MONKEY PATCH ----
    # For deterministic outcomes
    rng.RNG = random.Random(1639492287)
    # ----- END MONKEY PATCH -----

    g = digraph(style)
    r_d6 = R.from_value(H(6))
    replace_r = SubstitutionRoller(
        lambda outcome: r_d6.roll() if outcome.value == 1 else outcome,
        r_d6,
        max_depth=2,
    )
    graphviz_walk(g, replace_r.roll())

    return g

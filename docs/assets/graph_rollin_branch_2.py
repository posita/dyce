# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import random
from typing import Iterable, Union

from graph import Dot, digraph, graphviz_walk

from dyce import H, rng
from dyce.r import BranchOperationRoller, R, RollOutcome


def do_it(style: str) -> Dot:
    # ---- BEGIN MONKEY PATCH ----
    # For deterministic outcomes
    rng.RNG = random.Random(1635137918)
    # ----- END MONKEY PATCH -----

    g = digraph(style)
    r_d6 = R.from_value(H(6))

    def explode_sixes(
        r: BranchOperationRoller,
        roll_outcomes: Iterable[RollOutcome],
    ) -> Iterable[Union["RollOutcome", "R"]]:
        for roll_outcome in roll_outcomes:
            yield roll_outcome

            if roll_outcome.value == 6:
                yield roll_outcome.r

    r_d6_exploding = BranchOperationRoller(
        branch_op=explode_sixes,
        sources=(r_d6,),
        max_depth=2,
    )
    r_d6_exploding_3 = 3 @ r_d6_exploding

    roll = r_d6_exploding_3.roll()
    graphviz_walk(g, roll)

    return g

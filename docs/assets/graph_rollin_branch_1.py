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
    rng.RNG = random.Random(1633839750)
    # ----- END MONKEY PATCH -----

    g = digraph(style)
    r_d6 = R.from_value(H(6))

    def reroll_ones(
        r: BranchOperationRoller,
        roll_outcomes: Iterable[RollOutcome],
    ) -> Iterable[Union["RollOutcome", "R"]]:
        for roll_outcome in roll_outcomes:
            if roll_outcome.value == 1:
                yield roll_outcome.euthanize()
                yield roll_outcome.r
            else:
                yield roll_outcome

    r = BranchOperationRoller(
        branch_op=reroll_ones,
        sources=(r_d6, r_d6, r_d6),
        max_depth=2,
    )

    roll = r.roll()
    graphviz_walk(g, roll)

    return g

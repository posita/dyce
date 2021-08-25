# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from typing import cast

from graph import COLORS, Dot, digraph, graphviz_walk

from dyce import H
from dyce.r import ValueRoller
from tests.patches import patch_roll


def do_it(style: str) -> Dot:
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

    # ---- BEGIN MONKEY PATCH ----
    # For deterministic outcomes
    d12 = patch_roll(d12, 7)
    cast(ValueRoller, r_d12_add_4.sources[0])._value = d12
    # ----- END MONKEY PATCH -----

    graphviz_walk(g, r_d12_add_4.roll())

    return g

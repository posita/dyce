# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from graph import COLORS, Dot, digraph, graphviz_walk

from dyce import H
from dyce.r import PoolRoller, ValueRoller
from tests.patches import patch_roll


def do_it(style: str) -> Dot:
    g = digraph(style)
    d10 = H(10) - 1
    patch_roll(d10, 9)
    d00 = 10 * d10
    patch_roll(d00, 60)
    r_d00 = ValueRoller(
        d00,
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
    r_d10 = ValueRoller(
        d10,
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
    r_d100 = PoolRoller(sources=(r_d00, r_d10))
    graphviz_walk(g, r_d100.roll())

    return g

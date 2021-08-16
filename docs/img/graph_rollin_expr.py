# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from graph import COLORS, digraph

from dyce import H
from dyce.r import ValueRoller
from dyce.viz import walk_r
from tests.patches import patch_roll


def do_it(style: str):
    g = digraph(style)
    d12 = H(12)
    patch_roll(d12, 7)
    r_d12 = ValueRoller(
        d12,
        annotation={
            "node": {
                "color": COLORS[style][1],
                "fontcolor": COLORS[style][1],
                "style": "dashed",
            },
            "edge": {
                "color": COLORS[style][1],
                "fontcolor": COLORS[style][1],
                "style": "dashed",
            },
        },
    )
    r_4 = ValueRoller(
        4,
        annotation={
            "node": {
                "color": COLORS[style][2],
                "fontcolor": COLORS[style][2],
                "style": "dashed",
            },
            "edge": {
                "color": COLORS[style][2],
                "fontcolor": COLORS[style][2],
                "style": "dashed",
            },
        },
    )
    r_d12_add_4 = r_d12 + r_4
    walk_r(g, r_d12_add_4.roll())

    return g

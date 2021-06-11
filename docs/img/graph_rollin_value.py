# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from graph import digraph

from dyce.r import ValueRoller
from dyce.viz import walk_r


def do_it(style: str):
    g = digraph(style)
    r_1 = ValueRoller(1)
    walk_r(g, r_1.roll())

    return g
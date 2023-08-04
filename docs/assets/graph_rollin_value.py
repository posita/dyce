# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from graph import Dot, digraph, graphviz_walk

from dyce.r import ValueRoller


def do_it(style: str) -> Dot:
    g = digraph(style)
    r_1 = ValueRoller(1)
    graphviz_walk(g, r_1.roll())

    return g

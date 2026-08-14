# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

import operator
from enum import StrEnum, auto
from itertools import accumulate
from typing import TypeVar

from .h import H

__all__ = ("GraphType",)

_T = TypeVar("_T")


class GraphType(StrEnum):
    r"""
    Controls which variant of the distribution is plotted.

    - *NORMAL*: raw probability for each outcome
    - *AT_MOST*: cumulative probability `#!math P(X \le k)`
    - *AT_LEAST*: survival probability `#!math P(X \ge k)`
    """

    NORMAL = auto()
    AT_MOST = auto()
    AT_LEAST = auto()


def values_for_graph_type(
    h: H[_T],
    graph_type: GraphType,
) -> tuple[tuple[_T, ...], tuple[float, ...]]:
    if not h:
        return (), ()

    outcomes: tuple[_T, ...] = tuple(h)
    probabilities: tuple[float, ...] = tuple(
        float(probability) for _, probability in h.probability_items()
    )
    match graph_type:
        case GraphType.NORMAL:
            pass
        case GraphType.AT_LEAST:
            probabilities = tuple(accumulate(probabilities, operator.sub, initial=1.0))[
                :-1
            ]
        case GraphType.AT_MOST:
            probabilities = tuple(accumulate(probabilities, operator.add, initial=0.0))[
                1:
            ]
        case _:  # pragma: no cover
            raise ValueError(f"unrecognized graph type ({graph_type})")

    return outcomes, probabilities

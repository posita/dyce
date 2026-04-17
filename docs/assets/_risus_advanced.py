# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from enum import IntEnum, auto
from typing import TypeVar

from _risus_data import Versus  # pyrefly: ignore[missing-import]

from dyce import H, HResult, P, expand, explode_n

__all__ = ("evens_up_vs",)

T = TypeVar("T")


class EvensUp(IntEnum):
    MISS = 0
    HIT = auto()
    HIT_EXPLODE = auto()


def deadly_combat_vs(our_pool_size: int, their_pool_size: int) -> H[Versus]:
    our_best = (our_pool_size @ P(6)).h(-1)
    their_best = (their_pool_size @ P(6)).h(-1)
    h = our_best.apply(Versus.raw_vs, their_best)
    return expand(
        resolve_goliath,
        h,
        our_pool_size=our_pool_size,
        their_pool_size=their_pool_size,
    )


def evens_up_vs(
    our_pool_size: int, their_pool_size: int, *, goliath: bool = False
) -> H[Versus]:
    d_evens_up_raw = H(
        {
            EvensUp.MISS: 1,  # 1, 3, 5
            EvensUp.HIT: 2,  # 2, 4
            EvensUp.HIT_EXPLODE: 1,  # 6
        }
    )
    d_evens_up_exploded = explode_n(d_evens_up_raw, n=3)

    def _decode_hits(h_result: HResult[int]) -> int:
        return (
            h_result.outcome + 1
        ) // 2  # equivalent to h_result.outcome // 2 + h_result.outcome % 2

    d_evens_up = expand(_decode_hits, d_evens_up_exploded)
    h = (our_pool_size @ d_evens_up).apply(Versus.raw_vs, their_pool_size @ d_evens_up)

    return (
        expand(
            resolve_goliath,
            h,
            our_pool_size=our_pool_size,
            their_pool_size=their_pool_size,
        )
        if goliath
        else h
    )


def resolve_goliath(
    h_result: HResult[Versus], *, our_pool_size: int, their_pool_size: int
) -> Versus:
    r"""
    Goliath Rule: A tie goes to the party with fewer dice in this round.

    <!-- BEGIN MONKEY PATCH --
    >>> from _risus_advanced import (  # type: ignore[import-not-found] # ty: ignore[unresolved-import]
    ...     resolve_goliath,
    ... )
    >>> from _risus_data import Versus  # type: ignore[import-not-found] # ty: ignore[unresolved-import]

       -- END MONKEY PATCH -->

        >>> from dyce import H, HResult
        >>> resolve_goliath(
        ...     HResult(h=H(Versus), outcome=Versus.DRAW),
        ...     our_pool_size=1,
        ...     their_pool_size=2,
        ... ) is Versus.WIN
        True
        >>> resolve_goliath(
        ...     HResult(h=H(Versus), outcome=Versus.DRAW),
        ...     our_pool_size=2,
        ...     their_pool_size=1,
        ... ) is Versus.LOSE
        True
        >>> resolve_goliath(
        ...     HResult(h=H(Versus), outcome=Versus.DRAW),
        ...     our_pool_size=2,
        ...     their_pool_size=2,
        ... ) is Versus.DRAW
        True
    """
    return (
        Versus(
            int(our_pool_size < their_pool_size) - int(our_pool_size > their_pool_size)
        )
        if h_result.outcome == Versus.DRAW
        else h_result.outcome
    )

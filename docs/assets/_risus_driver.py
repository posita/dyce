# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from fractions import Fraction
from functools import cache
from typing import cast

from _risus_data import Versus, VersusFuncT  # pyrefly: ignore[missing-import]

from dyce import H, HResult, expand

__all__ = ("risus_combat_driver",)


def risus_combat_driver(
    our_pool_size: int,  # number of dice we still have
    their_pool_size: int,  # number of dice they still have
    us_vs_them_func: VersusFuncT,
) -> H[Versus]:
    if our_pool_size < 0 or their_pool_size < 0:
        raise ValueError(
            f"cannot have negative numbers (us: {our_pool_size}, them: {their_pool_size})"
        )
    elif our_pool_size == 0 and their_pool_size == 0:
        return H(
            {Versus.DRAW: 1}
        )  # should not happen unless combat(0, 0) is called from the start

    @cache
    def _resolve(our_pool_size: int, their_pool_size: int) -> H[Versus]:
        if our_pool_size == 0:
            return H({Versus.LOSE: 1})  # we are out of dice, they win
        if their_pool_size == 0:
            return H({Versus.WIN: 1})  # they are out of dice, we win
        this_round = us_vs_them_func(our_pool_size, their_pool_size)

        def _next_round(this_round: HResult[Versus]) -> H[Versus]:
            match this_round.outcome:
                case Versus.LOSE:
                    return _resolve(
                        our_pool_size - 1, their_pool_size
                    )  # we lost this round, and one die
                case Versus.WIN:
                    return _resolve(
                        our_pool_size, their_pool_size - 1
                    )  # they lost this round, and one die
                case Versus.DRAW:
                    return H({})  # ignore (immediately re-roll) all ties
                case _:
                    raise TypeError(
                        f"unrecognized this_round.outcome {this_round.outcome}"
                    )

        return cast(
            "H[Versus]",
            expand(_next_round, this_round, precision=Fraction(1, 0x7FFFFFFF)),
        )

    return _resolve(our_pool_size, their_pool_size)

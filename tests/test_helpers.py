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

from collections import Counter

from dyce import H, RollT

from ._helpers import (
    enumerate_weighted_unsorted_rolls_brute_force,
    enumerate_weighted_unsorted_rolls_multinomial_coefficient,
    sort_and_select_from_rolls,
)

__all__ = ()


def test_first_principles() -> None:
    for hs in (
        (H(6),) * 3,
        (H((2, 3, 3, 4, 4, 5)),) * 3,
        (H(4),) * 6,
        (H({i: i for i in range(1, 11)}),) * 3,
        (H({i: 11 - i for i in range(1, 11)}),) * 3,
        (H((-1, 0, 1)),) * 3,
        (H({1: 5, 6: 1}),) * 2 + (H({-3: 5, 2: 1, 7: 100}),) * 3,
    ):
        for keys in (
            (),
            (0,),
            (1,),
            (-1,),
            (0, 2),
        ):
            brute_force: Counter[RollT[int]] = Counter()
            multinomial: Counter[RollT[int]] = Counter()
            for roll, count in sort_and_select_from_rolls(
                enumerate_weighted_unsorted_rolls_brute_force(hs), *keys
            ):
                brute_force[roll] += count
            for (
                roll,
                count,
            ) in sort_and_select_from_rolls(
                enumerate_weighted_unsorted_rolls_multinomial_coefficient(hs), *keys
            ):
                multinomial[roll] += count
            assert brute_force == multinomial

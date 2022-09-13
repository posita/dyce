# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from collections import Counter
from enum import IntEnum, auto

from dyce import H, P
from dyce.evaluation import HResult, PResult, expandable, explode, foreach
from dyce.h import HOrOutcomeT

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_expandable_sentinel_default() -> None:
    default_sentinel = H({0: 1})
    d6 = H(6)

    @expandable
    def func(result: HResult) -> HOrOutcomeT:
        return result.outcome * 2 + func(result.h)

    assert func(d6, limit=0) == default_sentinel
    assert func(d6, limit=1) == d6 * 2 + default_sentinel
    assert func(d6, limit=2) == d6 * 2 + d6 * 2 + default_sentinel


def test_expandable_sentinel_h() -> None:
    sentinel = H({-2: 1})
    d6 = H(6)

    @expandable(sentinel=sentinel)
    def func(result: HResult) -> HOrOutcomeT:
        return result.outcome * func(result.h)

    assert func(d6, limit=0) == sentinel
    assert func(d6, limit=1) == d6 * sentinel
    assert func(d6, limit=2) == d6 * d6 * sentinel


def test_expandable_sentinel_with_recursion_error() -> None:
    d1 = H(1)

    @expandable(sentinel=H({0: 1}))
    def func(result: HResult) -> HOrOutcomeT:
        return func(result.h) + 1

    # Sentinel raises a RecursionError
    assert func(d1, limit=1) == H({1: 1})

    # 50 is meant to capture the depth beyond which func hits its RecursionError. This
    # is probably more like 200-500, depending on the environment.
    assert func(d1, limit=-1).gt(H({50: 1})) == H({True: 1})


def test_expandable_multiple_args_kw() -> None:
    d6 = H(6)
    d8 = H(8)
    d10 = H(10)
    p_2d8 = 2 @ P(d8)

    @expandable
    def func(d6: HResult, p_2d8: PResult, d10: HResult) -> HOrOutcomeT:
        assert d6.outcome in d6

        for d8_outcome in p_2d8.roll:
            assert d8_outcome in d8

        assert d10.outcome in d10

        return d6.outcome + sum(p_2d8.roll) + d10.outcome

    res = d6 + p_2d8 + d10
    assert func(d6, p_2d8, d10) == res
    assert func(d6, p_2d8, d10=d10) == res
    assert func(d6, p_2d8=p_2d8, d10=d10) == res
    assert func(d6=d6, p_2d8=p_2d8, d10=d10) == res


def test_expandable_accommodates_h_with_zero_total() -> None:
    class Result(IntEnum):
        ONES = auto()
        FIVES_OR_SIXES = auto()

    def func(p_result: PResult) -> H:
        c = Counter(p_result.roll)

        return H({Result.ONES: c[1], Result.FIVES_OR_SIXES: c[5] + c[6]})

    assert foreach(func, p_result=4 @ P(6)) == H(
        {Result.ONES: 1, Result.FIVES_OR_SIXES: 2}
    )


def test_explode_single_sided_die_integral_limit() -> None:
    def is_even_predicate(h_result: HResult):
        return h_result.outcome % 2 == 0

    assert explode(H({3: 1}), is_even_predicate, limit=5) == H({3: 1})
    assert explode(H({2: 1}), is_even_predicate, limit=5) == H({12: 1})
    assert explode(H({0: 1}), is_even_predicate, limit=5) == H({0: 1})
    assert explode(H({-2: 1}), is_even_predicate, limit=5) == H({-12: 1})
    assert explode(H({-3: 1}), is_even_predicate, limit=5) == H({-3: 1})

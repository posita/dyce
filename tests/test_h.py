# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop
from typing import Union

import itertools
import math
import operator
import os
import statistics

from dyce import H
from dyce.h import _within

__all__ = ()


# ---- Classes -------------------------------------------------------------------------


class TestH:
    def test_init_empty(self) -> None:
        assert H(()) == {}
        assert H(0) == {}
        assert H((i, 0) for i in range(1, 7)) == {}

    def test_init(self) -> None:
        assert H((0, 0, 1, 0, 1)) == {0: 3, 1: 2}
        assert H((1, 2, 3, 1, 2, 1)) == {1: 3, 2: 2, 3: 1}
        assert H(((1, 2), (3, 1), (2, 1), (1, 1))) == {1: 3, 2: 1, 3: 1}
        assert H(-2) == H(range(-1, -3, -1))
        assert H(6) == H(range(1, 7))

    def test_repr(self) -> None:
        assert repr(H(())) == "H({})"
        assert repr(H(0)) == "H({})"
        assert repr(H(-6)) == "H(-6)"
        assert repr(H(6)) == "H(6)"
        assert repr(H((1, 2, 3, 0, 1, 2, 1))) == "H({0: 1, 1: 3, 2: 2, 3: 1})"

    def test_op_eq(self) -> None:
        base = H(range(10))
        assert base == base.accumulate(base)
        assert base == base.accumulate(base).accumulate(base)
        assert base.accumulate(base) == base.accumulate(base).accumulate(base)
        assert base != base.accumulate((0,))

    def test_len_and_counts(self) -> None:
        d0 = H({})
        d6_d8 = H(6) + H(8)
        assert len(d0) == 0
        assert sum(d0.counts()) == 0
        assert len(d6_d8) == 13  # num distinct values
        assert sum(d6_d8.counts()) == 48  # combinations
        assert len((d6_d8 + d6_d8)) == 25
        assert sum((d6_d8 + d6_d8).counts()) == 2304

    def test_getitem(self) -> None:
        d6_2 = 2 @ H(6)
        assert d6_2[2] == 1
        assert d6_2[7] == 6
        assert d6_2[12] == 1

    def test_op_add_h(self) -> None:
        d2 = H(range(1, 3))
        d3 = H(range(1, 4))
        assert d2 + d3 == {2: 1, 3: 2, 4: 2, 5: 1}
        assert d3 + d2 == {2: 1, 3: 2, 4: 2, 5: 1}
        assert d2 + d3 == d3 + d2

    def test_op_add_int(self) -> None:
        h1 = H(range(10, 20))
        h2 = H(range(11, 21))
        assert h2 == h1 + 1
        assert 1 + h1 == h2

    def test_op_sub_h(self) -> None:
        d2 = H(range(1, 3))
        d3 = H(range(1, 4))
        assert d2 - d3 == {-2: 1, -1: 2, 0: 2, 1: 1}
        assert d3 - d2 == {-1: 1, 0: 2, 1: 2, 2: 1}

    def test_op_sub_int(self) -> None:
        h1 = H(range(10, 20))
        h2 = H(range(9, 19))
        h3 = H(range(-8, -18, -1))
        assert h2 == h1 - 1
        assert 1 - h2 == h3

    def test_op_matmul(self) -> None:
        d6 = H(range(1, 7))
        d6_2 = d6 + d6
        d6_3 = d6_2 + d6
        assert 0 @ d6 == H({})
        assert H({}) == d6 @ 0
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2
        assert d6_3 == 3 @ d6
        assert 4 @ d6 == d6 @ 2 @ 2

    def test_map(self) -> None:
        d6 = H(range(1, 7))
        d8 = H(range(1, 9))
        within_filter = _within(-1, 1)
        d8_v_d6 = d8.map(within_filter, d6)
        assert d8_v_d6 == {-1: 10, 0: 17, 1: 21}

        within_filter = _within(7, 9)
        d6_2_v_7_9 = (2 @ d6).map(within_filter, 0)
        assert d6_2_v_7_9 == {-1: 15, 0: 15, 1: 6}

    def test_cmp_eq(self) -> None:
        h = H(range(-1, 2))
        assert h.eq(0) == H((0, 1, 0))
        assert h.eq(h) == H((1, 0, 0, 0, 1, 0, 0, 0, 1))

    def test_cmp_ne(self) -> None:
        h = H(range(-1, 2))
        assert h.ne(0) == H((1, 0, 1))
        assert h.ne(h) == H((0, 1, 1, 1, 0, 1, 1, 1, 0))

    def test_cmp_lt(self) -> None:
        h = H(range(-1, 2))
        assert h.lt(0) == H((1, 0, 0))
        assert h.lt(h) == H((0, 1, 1, 0, 0, 1, 0, 0, 0))

    def test_cmp_le(self) -> None:
        h = H(range(-1, 2))
        assert h.le(0) == H((1, 1, 0))
        assert h.le(h) == H((1, 1, 1, 0, 1, 1, 0, 0, 1))

    def test_cmp_gt(self) -> None:
        h = H(range(-1, 2))
        assert h.gt(0) == H((0, 0, 1))
        assert h.gt(h) == H((0, 0, 0, 1, 0, 0, 1, 1, 0))

    def test_cmp_ge(self) -> None:
        h = H(range(-1, 2))
        assert h.ge(0) == H((0, 1, 1))
        assert h.ge(h) == H((1, 0, 0, 1, 1, 0, 1, 1, 1))

    def test_accumulate(self) -> None:
        h = H(itertools.chain(range(0, 6), range(3, 9)))
        assert H(range(0, 6)).accumulate(H(range(3, 9))) == h

    def test_accumulate_does_not_invoke_lowest_terms(self) -> None:
        base = H(range(10))
        assert dict(base) != dict(base.accumulate(base))

    def test_lowest_terms_identity(self) -> None:
        lowest_terms = H({i: i for i in range(10)})
        assert dict(lowest_terms) == dict(lowest_terms.lowest_terms())

    def test_substitute_double_odd_values(self) -> None:
        def double_odd_values(
            h: H,  # pylint: disable=unused-argument
            face: int,
        ) -> Union[H, int]:
            return face * 2 if face % 2 != 0 else face

        d8 = H(8)
        assert d8.substitute(double_odd_values) == H(
            {14: 1, 10: 1, 8: 1, 6: 2, 4: 1, 2: 2}
        )
        assert d8.substitute(double_odd_values, max_depth=2) == H(
            {14: 1, 10: 1, 8: 1, 6: 2, 4: 1, 2: 2}
        )

    def test_substitute_never_expand(self) -> None:
        def never_expand(
            d: H,  # pylint: disable=unused-argument
            face: int,
        ) -> Union[H, int]:
            return face

        d20 = H(20)
        assert d20.substitute(never_expand) == d20
        assert d20.substitute(never_expand, operator.add, 20) == d20

    def test_substitute_reroll_d4_threes(self) -> None:
        def reroll_d4_threes(h: H, face: int) -> Union[H, int]:
            return h if max(h) == 4 and face == 3 else face

        h = H(4)
        assert h.substitute(reroll_d4_threes) == H({4: 5, 3: 1, 2: 5, 1: 5})
        assert h.substitute(reroll_d4_threes, operator.add) == H(
            {7: 1, 6: 1, 5: 1, 4: 5, 2: 4, 1: 4}
        )
        assert h.substitute(reroll_d4_threes, operator.mul, max_depth=2) == H(
            {36: 1, 27: 1, 18: 1, 12: 4, 9: 1, 6: 4, 4: 16, 3: 4, 2: 16, 1: 16}
        )

    def test_format(self) -> None:
        assert H((1, 2, 3, 1, 2, 1)).format(width=115) == os.linesep.join(
            (
                "avg |    1.67",
                "std |    0.75",
                "var |    0.56",
                "  1 |  50.00% |##################################################",
                "  2 |  33.33% |#################################",
                "  3 |  16.67% |################",
            )
        )
        assert (
            H((1, 2, 3, 1, 2, 1)).format(width=0)
            == "{avg: 1.67, 1: 50.00%, 2: 33.33%, 3: 16.67%}"
        )

    def test_mean(self) -> None:
        h = H((i, i) for i in range(10))
        assert math.isclose(
            h.mean(),
            statistics.mean(
                itertools.chain(*(itertools.repeat(f, c) for f, c in h.items()))
            ),
        )

    def test_stdev(self) -> None:
        h = H((i, i) for i in range(10))
        assert math.isclose(
            h.stdev(),
            statistics.pstdev(
                itertools.chain(*(itertools.repeat(f, c) for f, c in h.items()))
            ),
        )

    def test_variance(self) -> None:
        h = H((i, i) for i in range(10))
        assert math.isclose(
            h.variance(),
            statistics.pvariance(
                itertools.chain(*(itertools.repeat(f, c) for f, c in h.items()))
            ),
        )


def test_within() -> None:
    within_filter = _within(0, 2)
    assert getattr(within_filter, "lo") == 0
    assert getattr(within_filter, "hi") == 2
    assert within_filter(5, 2) > 0
    assert within_filter(5, 3) == 0
    assert within_filter(5, 4) == 0
    assert within_filter(5, 5) == 0
    assert within_filter(5, 6) < 0

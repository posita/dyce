#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` files for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before viewing or using
this software in any capacity.
"""
# ======================================================================================

from __future__ import generator_stop


# ---- Imports -------------------------------------------------------------------------


import itertools
import logging
import os

from dyce.lib import D, H, within


# ---- Data ----------------------------------------------------------------------------


__all__ = ()

_LOGGER = logging.getLogger(__name__)


# ---- Classes -------------------------------------------------------------------------


class TestH:
    def test_init(self) -> None:
        assert H(()) == {}
        assert H((0, 0, 1, 0, 1)) == {0: 3, 1: 2}
        assert H((1, 2, 3, 1, 2, 1)) == {1: 3, 2: 2, 3: 1}
        assert H(((1, 2), (3, 1), (2, 1), (1, 1))) == {1: 3, 2: 1, 3: 1}
        assert H(-2) == H(range(-1, -3, -1))
        assert H(0) == H((0,))
        assert H(6) == H(range(1, 7))

    def test_repr(self) -> None:
        assert repr(H(-6)) == "H(-6)"
        assert repr(H(0)) == "H(0)"
        assert repr(H(6)) == "H(6)"
        assert repr(H((1, 2, 3, 0, 1, 2, 1))) == "H({0: 1, 1: 3, 2: 2, 3: 1})"

    def test_op_add_int(self) -> None:
        h1 = H(range(10, 20))
        h2 = H(range(11, 21))
        assert h2 == h1 + 1
        assert 1 + h1 == h2

    def test_op_add_h(self) -> None:
        d2 = H(range(1, 3))
        d3 = H(range(1, 4))
        assert d2 + d3 == {2: 1, 3: 2, 4: 2, 5: 1}
        assert d3 + d2 == {2: 1, 3: 2, 4: 2, 5: 1}
        assert d2 + d3 == d3 + d2

        dist = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
        d6 = H(range(1, 7))
        d6_2 = d6 + d6
        assert d6_2 == H(dist)

    def test_op_sub_int(self) -> None:
        h1 = H(range(10, 20))
        h2 = H(range(9, 19))
        h3 = H(range(-8, -18, -1))
        assert h2 == h1 - 1
        assert 1 - h2 == h3

    def test_op_sub_h(self) -> None:
        d2 = H(range(1, 3))
        d3 = H(range(1, 4))
        assert d2 - d3 == {-2: 1, -1: 2, 0: 2, 1: 1}
        assert d3 - d2 == {-1: 1, 0: 2, 1: 2, 2: 1}

    def test_op_matmul(self) -> None:
        d6 = H(range(1, 7))
        d6_2 = d6 + d6
        d6_3 = d6_2 + d6
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2
        assert d6_3 == 3 @ d6
        assert 4 @ d6 == d6 @ 2 @ 2

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

    def test_apply(self) -> None:
        d6 = H(range(1, 7))
        d8 = H(range(1, 9))
        within_filter = within(-1, 1)
        h_d8_v_d6 = d8.apply(within_filter, d6)
        assert h_d8_v_d6 == {-1: 10, 0: 17, 1: 21}

        within_filter = within(7, 9)
        d6_2_v_7_9 = (2 @ d6).apply(within_filter, 0)
        assert d6_2_v_7_9 == {-1: 15, 0: 15, 1: 6}

    def test_filter(self) -> None:
        d6 = H(range(1, 7))
        d8 = H(range(1, 9))
        within_filter = within(-1, 1)

        def _within_filter(a: int, b: int) -> bool:
            return bool(within_filter(a, b))

        h_d8_v_d6 = d8.filter(_within_filter, d6, t_val=1, f_val=0)
        assert h_d8_v_d6 == {0: 17, 1: 31}

    def test_concat(self) -> None:
        h = H(itertools.chain(range(0, 6), range(3, 9)))
        assert H(range(0, 6)).concat(H(range(3, 9))) == h

    def test_format(self) -> None:
        assert H((1, 2, 3, 1, 2, 1)).format() == os.linesep.join(
            (
                "  1 |  50.00% |##################################################",
                "  2 |  33.33% |#################################",
                "  3 |  16.67% |################",
            )
        )

    def test_equivalence(self) -> None:
        d6 = D(6)
        d6n = D(-6)
        assert -d6 == d6n
        assert d6 - d6 == d6 + d6n
        assert -d6 + d6 == d6n + d6
        assert -d6 - d6 == d6n - d6
        assert d6 + d6 == d6 - d6n
        assert D(d6, -d6).h() == d6 + d6n
        assert 2 @ d6 - d6 == d6 + d6 + d6n
        assert -(2 @ d6) == d6n + d6n


class TestD:
    def test_init(self) -> None:
        d2n = D(-2)
        h_d2n = H(range(-1, -3, -1))
        assert d2n.h() == h_d2n

        d0 = D(0)
        h_d0 = H((0,))
        assert d0.h() == h_d0

        d6 = D(6)
        h_d6 = H(range(1, 7))
        assert d6.h() == h_d6

        h = H(range(0, -10, -1))
        assert D(h).h() == h

        d6_2 = D(h_d6, h_d6)
        assert d6_2.h() == H(sum(v) for v in itertools.product(h_d6, h_d6))
        assert D(d6, d6) == d6_2
        assert D(d6, h_d6) == d6_2
        assert D(h_d6, d6) == d6_2

        assert D(H({})) == D()  # exclude empty histograms

    def test_repr(self) -> None:
        assert repr(D()) == "D()"
        assert repr(D(-6)) == "D(-6)"
        assert repr(D(0)) == "D(0)"
        assert repr(D(6)) == "D(6)"
        assert (
            repr(D(D(6), D(8), D(H({0: 1, 1: 3, 2: 2, 3: 1}))))
            == "D(6, 8, H({0: 1, 1: 3, 2: 2, 3: 1}))"
        )

    def test_op_eq(self) -> None:
        die1 = D(H(range(6, 0, -1)))
        die2 = D(6)
        die3 = D(die2)
        assert die2 == die1
        assert die3 == die2

    def test_op_ne(self) -> None:
        die1 = D(H(range(-1, -7, -1)))
        die2 = D(6)
        assert die1 != die2

    def test_len(self) -> None:
        de1 = D()
        de2 = D(H({}))
        d0 = D(0)
        d6 = D(6)
        d8 = D(8)
        assert len(de1) == 0
        assert len(de2) == 0
        assert len(de1.h()) == 0
        assert len(de2.h()) == 0
        assert len(d0) == 1
        assert len(d0.h()) == 1
        assert len(d6) == 1
        assert len(d6.h()) == 6
        assert len(d8) == 1
        assert len(d8.h()) == 8
        assert len(D(d6, d8)) == 2
        assert len(D(d6, d8).h()) == 13  # num distinct values
        assert sum(D(d6, d8).h().counts()) == 48  # combinations
        assert len(D(d6, d8, d6, d8)) == 4
        assert sum(D(d6, d8, d6, d8).h().counts()) == 2304

    def test_getitem(self) -> None:
        d2 = D(2)
        d3 = D(3)
        d4 = D(4)
        d2d3d4 = D(d2, d3, d4)
        assert d2d3d4[0] == d2.h()
        assert d2d3d4[1] == d3.h()
        assert d2d3d4[2] == d4.h()
        assert d2d3d4[:] == d2d3d4.h()
        assert d2d3d4[:1] == H({1: 1, 2: 7, 3: 10, 4: 6})
        assert d2d3d4[:2] == H({2: 1, 3: 3, 4: 6, 5: 7, 6: 5, 7: 2})
        assert d2d3d4[-2:] == H({2: 7, 3: 9, 4: 6, 5: 2})
        assert d2d3d4[-1:] == H({1: 18, 2: 6})

    def test_op_add_int(self) -> None:
        d6 = D(6)
        d6_plus = D(H(range(2, 8)))
        d8 = D(8)
        d8_plus = D(H(range(2, 10)))
        assert 1 + d6 == d6_plus
        assert d8_plus == d8 + 1

    def test_op_add_die(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 + d3 == H((2, 3, 4, 3, 4, 5))
        assert d3 + d2 == H((2, 3, 3, 4, 4, 5))
        assert d2 + d3 == d3 + d2
        d2d3 = D(d2, d3)
        assert d2 + d3 == d2d3.h()

    def test_op_sub_int(self) -> None:
        d6 = D(6)
        minus_d6 = D(H(range(0, -6, -1)))
        d8 = D(8)
        d8_minus = D(H(range(0, 8)))
        assert 1 - d6 == minus_d6
        assert d8_minus == d8 - 1

    def test_op_sub_die(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 - d3 == H((0, -1, -2, 1, 0, -1))
        assert d3 - d2 == H((0, -1, 1, 0, 2, 1))

    def test_op_mul_int(self) -> None:
        die1 = D(H(range(10, 20)))
        die2 = D(H(range(100, 200, 10)))
        assert die2 == die1 * 10
        assert 10 * die1 == die2

    def test_op_mul_h(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 * d3 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert d3 * d2 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert d2 * d3 == d3 * d2

    def test_op_matmul(self) -> None:
        d6 = D(6)
        d6_2 = D(d6, d6)
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2

    def test_op_floordiv_int(self) -> None:
        die1 = D(H(range(10, 110, 10)))
        die2 = D(H(range(1, 11)))
        die3 = D(H((10, 5, 3, 2, 2, 1, 1, 1, 1, 1)))
        assert die2 == die1 // 10
        assert 100 // die1 == die3

    def test_op_floordiv_h(self) -> None:
        die1 = D(H((1, 4)))
        die2 = D(H((1, 2)))
        assert die1 // die2 == H((1, 0, 4, 2))
        assert die2 // die1 == H((1, 0, 2, 0))

    def test_op_mod_int(self) -> None:
        d10 = D(10)
        assert d10 % 5 == H((1, 2, 3, 4, 0, 1, 2, 3, 4, 0))
        assert 5 % d10 == H((0, 1, 2, 1, 0, 5, 5, 5, 5, 5))

    def test_op_mod_h(self) -> None:
        die1 = H((1, 5))
        die2 = H((1, 3))
        assert die1 % die2 == H((0, 1, 0, 2))
        assert die2 % die1 == H((0, 1, 0, 3))

    def test_op_pow_int(self) -> None:
        d5 = D(5)
        assert d5 ** 2 == H((1, 4, 9, 16, 25))
        assert 2 ** d5 == H((2, 4, 8, 16, 32))
        assert d5 ** -1 == H((1, 0, 0, 0, 0))
        assert (-1) ** d5 == H((-1, 1, -1, 1, -1))

    def test_op_pow_h(self) -> None:
        die1 = D(H((2, 5)))
        die2 = D(H((3, 4)))
        assert die1 ** die2 == H((8, 16, 125, 625))
        assert die2 ** die1 == H((9, 243, 16, 1024))

    def test_op_bool(self) -> None:
        assert 0 & D(H((1, 0, 1))) == H((0, 0, 0))
        assert 0 | D(H((1, 0, 1))) == H((1, 0, 1))
        assert 0 ^ D(H((1, 0, 1))) == H((1, 0, 1))
        assert D(H((1, 0, 1))) & 0 == H((0, 0, 0))
        assert D(H((1, 0, 1))) | 0 == H((1, 0, 1))
        assert D(H((1, 0, 1))) ^ 0 == H((1, 0, 1))
        assert 1 & D(H((1, 0, 1))) == H((1, 0, 1))
        assert 1 | D(H((1, 0, 1))) == H((1, 1, 1))
        assert 1 ^ D(H((1, 0, 1))) == H((0, 1, 0))
        assert D(H((1, 0, 1))) & 1 == H((1, 0, 1))
        assert D(H((1, 0, 1))) | 1 == H((1, 1, 1))
        assert D(H((1, 0, 1))) ^ 1 == H((0, 1, 0))

    def test_op_unary(self) -> None:
        die = D(H(-v if v % 2 else v for v in range(10, 20)))
        assert isinstance(+die, type(die))
        assert (+die) == D(H((10, -11, 12, -13, 14, -15, 16, -17, 18, -19)))
        assert isinstance(-die, type(die))
        assert (-die) == D(H((-10, 11, -12, 13, -14, 15, -16, 17, -18, 19)))
        assert isinstance(abs(die), type(die))
        assert abs(die) == D(H((10, 11, 12, 13, 14, 15, 16, 17, 18, 19)))

    def test_h(self) -> None:
        r_d6 = range(1, 7)
        r_d8 = range(1, 7)
        h_d6d8 = H(sum(v) for v in itertools.product(r_d6, r_d8) if v)
        d6 = D(6)
        d8 = D(6)
        d6d8 = D(d6, d8)
        assert d6d8.h() == h_d6d8
        assert D().h() == H({})


def test_within() -> None:
    within_filter = within(0, 2)
    assert getattr(within_filter, "lo") == 0
    assert getattr(within_filter, "hi") == 2
    assert within_filter(5, 2) > 0
    assert within_filter(5, 3) == 0
    assert within_filter(5, 4) == 0
    assert within_filter(5, 5) == 0
    assert within_filter(5, 6) < 0

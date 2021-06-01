# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop
from typing import Sequence

import functools
import itertools
import operator
import pytest

from dyce import H, P

__all__ = ()


# ---- Classes -------------------------------------------------------------------------


class TestP:
    def test_init_empty(self) -> None:
        assert P(0) == P()

    def test_init_neg(self) -> None:
        p_d2n = P(-2)
        d2n = H(range(-1, -3, -1))
        assert p_d2n.h() == d2n

    def test_init_pos(self) -> None:
        p_d6 = P(6)
        d6 = H(range(1, 7))
        assert p_d6.h() == d6

    def test_init_one_histogram(self) -> None:
        h = H(range(0, -10, -1))
        assert P(h).h() == h

    def test_init_multiple_histograms(self) -> None:
        d6 = H(6)
        p_d6 = P(6)
        p_2d6 = P(d6, d6)
        assert p_2d6.h() == H(sum(v) for v in itertools.product(d6, d6))
        assert P(p_d6, p_d6) == p_2d6
        assert P(p_d6, d6) == p_2d6
        assert P(d6, p_d6) == p_2d6

    def test_init_exclude_empty_histograms(self) -> None:
        assert P(H({})) == P()
        assert P(2, H({}), 2, H({})) == P(2, 2)

    def test_repr(self) -> None:
        assert repr(P()) == "P()"
        assert repr(P(0)) == "P()"
        assert repr(P(-6)) == "P(-6)"
        assert repr(P(6)) == "P(6)"
        assert (
            repr(P(P(6), P(8), P(H({3: 1, 2: 2, 1: 3, 0: 1}))))
            == "P(H({0: 1, 1: 3, 2: 2, 3: 1}), 6, 8)"
        )

    def test_equivalence(self) -> None:
        p_d6 = P(6)
        p_d6n = P(-6)
        assert -p_d6 == p_d6n
        assert p_d6 - p_d6 == p_d6 + p_d6n
        assert -p_d6 + p_d6 == p_d6n + p_d6
        assert -p_d6 - p_d6 == p_d6n - p_d6
        assert p_d6 + p_d6 == p_d6 - p_d6n
        assert P(p_d6, -p_d6).h() == p_d6 + p_d6n
        assert 2 @ p_d6 - p_d6 == p_d6 + p_d6 + p_d6n
        assert -(2 @ p_d6) == p_d6n + p_d6n

    def test_op_eq(self) -> None:
        p_d6 = P(6)
        p_d6_2 = P(H(range(6, 0, -1)))
        p_d6_3 = P(p_d6_2)
        assert p_d6_2 == p_d6
        assert p_d6_3 == p_d6_2

    def test_op_eq_ignores_order(self) -> None:
        d4 = H(4)
        d6 = H(6)
        assert P(d4, d6) == P(d6, d4)

    def test_op_eq_invokes_lowest_terms(self) -> None:
        d4 = H(4)
        d6 = H(6)
        assert P(d4, d6) == P(d4.accumulate(d4), d6.accumulate(d6))

    def test_op_ne(self) -> None:
        p_d6 = P(6)
        p_d6n = P(H(range(-1, -7, -1)))
        assert p_d6n != p_d6

    def test_len(self) -> None:
        p_d0_1 = P()
        p_d0_2 = P(H({}))
        p_d6 = P(6)
        p_d8 = P(8)
        assert len(p_d0_1) == 0
        assert len(p_d0_2) == 0
        assert len(p_d6) == 1
        assert len(p_d8) == 1
        assert len(P(p_d6, p_d8)) == 2
        assert len(P(p_d6, p_d8, p_d6, p_d8)) == 4

    def test_getitem(self) -> None:
        d4n = H(-4)
        d8 = H(8)
        p_d4n_d8 = 3 @ P(d4n, d8)
        assert p_d4n_d8[0] == d4n
        assert p_d4n_d8[2] == d4n
        assert p_d4n_d8[-3] == d8
        assert p_d4n_d8[-1] == d8

    def test_op_add_h(self) -> None:
        p_d2 = P(2)
        p_d3 = P(3)
        assert p_d2 + p_d3 == H((2, 3, 4, 3, 4, 5))
        assert p_d3 + p_d2 == H((2, 3, 3, 4, 4, 5))
        assert p_d2 + p_d3 == p_d3 + p_d2
        p_d2_d3 = P(p_d2, p_d3)
        assert p_d2 + p_d3 == p_d2_d3.h()

    def test_op_add_int(self) -> None:
        p_d6 = P(6)
        p_d6_plus = P(H(range(2, 8)))
        p_d8 = P(8)
        p_d8_plus = P(H(range(2, 10)))
        assert 1 + p_d6 == p_d6_plus
        assert p_d8_plus == p_d8 + 1

    def test_op_sub_h(self) -> None:
        p_d2 = P(2)
        p_d3 = P(3)
        assert p_d2 - p_d3 == H((0, -1, -2, 1, 0, -1))
        assert p_d3 - p_d2 == H((0, -1, 1, 0, 2, 1))

    def test_op_sub_int(self) -> None:
        p_d6 = P(6)
        p_minus_d6 = P(H(range(0, -6, -1)))
        p_d8 = P(8)
        p_d8_minus = P(H(range(0, 8)))
        assert 1 - p_d6 == p_minus_d6
        assert p_d8_minus == p_d8 - 1

    def test_op_mul_h(self) -> None:
        p_d2 = P(2)
        p_d3 = P(3)
        assert p_d2 * p_d3 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert p_d3 * p_d2 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert p_d2 * p_d3 == p_d3 * p_d2

    def test_op_mul_int(self) -> None:
        p1 = P(H(range(10, 20)))
        p2 = P(H(range(100, 200, 10)))
        assert p2 == p1 * 10
        assert 10 * p1 == p2

    def test_op_matmul(self) -> None:
        d6 = P(6)
        d6_2 = P(d6, d6)
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2

    def test_op_floordiv_h(self) -> None:
        p1 = P(H((1, 4)))
        p2 = P(H((1, 2)))
        assert p1 // p2 == H((1, 0, 4, 2))
        assert p2 // p1 == H((1, 0, 2, 0))

    def test_op_floordiv_int(self) -> None:
        p_d10 = P(10)
        p1 = P(H(range(10, 110, 10)))
        p2 = P(H((10, 5, 3, 2, 2, 1, 1, 1, 1, 1)))
        assert p_d10 == p1 // 10
        assert 100 // p1 == p2

    def test_op_mod_h(self) -> None:
        p_d4 = H((1, 5))
        p_d2 = H((1, 3))
        assert p_d4 % p_d2 == H((0, 1, 0, 2))
        assert p_d2 % p_d4 == H((0, 1, 0, 3))

    def test_op_mod_int(self) -> None:
        p_d10 = P(10)
        assert p_d10 % 5 == H((1, 2, 3, 4, 0, 1, 2, 3, 4, 0))
        assert 5 % p_d10 == H((0, 1, 2, 1, 0, 5, 5, 5, 5, 5))

    def test_op_pow_h(self) -> None:
        p1 = P(H((2, 5)))
        p2 = P(H((3, 4)))
        assert p1 ** p2 == H((8, 16, 125, 625))
        assert p2 ** p1 == H((9, 243, 16, 1024))

    def test_op_pow_int(self) -> None:
        p_d5 = P(5)
        assert p_d5 ** 2 == H((1, 4, 9, 16, 25))
        assert 2 ** p_d5 == H((2, 4, 8, 16, 32))
        assert p_d5 ** -1 == H((1, 0, 0, 0, 0))
        assert (-1) ** p_d5 == H((-1, 1, -1, 1, -1))

    def test_op_bitwise(self) -> None:
        assert 0 & P(H((1, 0, 1))) == H((0, 0, 0))
        assert 0 | P(H((1, 0, 1))) == H((1, 0, 1))
        assert 0 ^ P(H((1, 0, 1))) == H((1, 0, 1))
        assert P(H((1, 0, 1))) & 0 == H((0, 0, 0))
        assert P(H((1, 0, 1))) | 0 == H((1, 0, 1))
        assert P(H((1, 0, 1))) ^ 0 == H((1, 0, 1))
        assert 1 & P(H((1, 0, 1))) == H((1, 0, 1))
        assert 1 | P(H((1, 0, 1))) == H((1, 1, 1))
        assert 1 ^ P(H((1, 0, 1))) == H((0, 1, 0))
        assert P(H((1, 0, 1))) & 1 == H((1, 0, 1))
        assert P(H((1, 0, 1))) | 1 == H((1, 1, 1))
        assert P(H((1, 0, 1))) ^ 1 == H((0, 1, 0))

    def test_op_unary(self) -> None:
        p = P(H(-v if v % 2 else v for v in range(10, 20)))
        assert isinstance(+p, type(p))
        assert (+p) == P(H((10, -11, 12, -13, 14, -15, 16, -17, 18, -19)))
        assert isinstance(-p, type(p))
        assert (-p) == P(H((-10, 11, -12, 13, -14, 15, -16, 17, -18, 19)))
        assert isinstance(abs(p), type(p))
        assert abs(p) == P(H((10, 11, 12, 13, 14, 15, 16, 17, 18, 19)))

    def test_h_flatten(self) -> None:
        r_d6 = range(1, 7)
        r_d8 = range(1, 9)
        d6_d8 = H(sum(v) for v in itertools.product(r_d6, r_d8) if v)
        p_d6 = P(6)
        p_d8 = P(8)
        p_d6_d8 = P(p_d6, p_d8)
        assert p_d6_d8.h() == d6_d8
        assert P().h() == H({})

    def test_h_take_identity(self) -> None:
        p_d0 = P()
        assert p_d0.h(slice(None)) == p_d0.h()
        p_5d20 = 5 @ P(20)
        assert p_5d20.h(slice(None)) == p_5d20.h()

    def test_h_take_heterogeneous_dice(self) -> None:
        p_d3 = P(3)
        p_d3n = -p_d3
        p_d4 = P(4)
        p_d4n = -p_d4
        p_4d3_4d4 = 2 @ P(p_d3, p_d3n, p_d4n, p_d4)

        with pytest.raises(IndexError):
            _ = p_4d3_4d4.h(len(p_4d3_4d4))

        assert p_4d3_4d4.h(slice(0, 0)) == {}
        assert p_4d3_4d4.h(slice(None)) == p_4d3_4d4.h()
        assert p_4d3_4d4.h(*range(len(p_4d3_4d4))) == p_4d3_4d4.h()
        assert p_4d3_4d4.h(slice(1)) == p_4d3_4d4.h(0)
        assert p_4d3_4d4.h(slice(-1, None)) == p_4d3_4d4.h(-1)
        assert p_4d3_4d4.h(0, 2) == p_4d3_4d4.h(slice(None, 3, 2))
        assert p_4d3_4d4.h(0, slice(2, None, 2)) == p_4d3_4d4.h(slice(None, None, 2))
        assert p_4d3_4d4.h(0, 2, 4, 6) == p_4d3_4d4.h(slice(None, None, 2))
        assert p_4d3_4d4.h(*range(0, len(p_4d3_4d4), 2)) == p_4d3_4d4.h(
            slice(None, None, 2)
        )
        assert p_4d3_4d4.h(
            *(i for i in range(len(p_4d3_4d4)) if i & 0x1)
        ) == p_4d3_4d4.h(slice(1, None, 2))

    def test_h_take_homogeneous_dice(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df

        with pytest.raises(IndexError):
            _ = p_4df.h(len(p_4df))

        assert p_4df.h(slice(0, 0)) == {}
        assert p_4df.h(slice(None)) == p_4df.h()

    def test_rolls_with_counts_empty(self) -> None:
        assert tuple(P().rolls_with_counts()) == ()

    def test_rolls_with_counts_heterogeneous(self) -> None:
        assert tuple(P(2, 3).rolls_with_counts()) == (
            ((1, 1), 1),
            ((1, 2), 1),
            ((1, 3), 1),
            ((1, 2), 1),  # originated as ((2, 1), 1), but faces get sorted
            ((2, 2), 1),
            ((2, 3), 1),
        )

    def test_rolls_with_counts_homogeneous(self) -> None:
        assert tuple(P(2, 2).rolls_with_counts()) == (
            ((1, 1), 1),
            ((1, 2), 2),
            ((2, 2), 1),
        )

    def test_validate_implementation_combinations_heterogeneous_dice(self) -> None:
        p_d3 = P(3)
        p_d3n = -p_d3
        p_d4 = P(4)
        p_d4n = -p_d4
        p_4d3_4d4 = 2 @ P(p_d3, p_d3n, p_d4n, p_d4)
        assert p_4d3_4d4.h(slice(0, 0)) == H(
            _inefficient_combinations_with_counts(tuple(p_4d3_4d4), slice(0, 0))
        )
        assert p_4d3_4d4.h(slice(-1, None)) == H(
            _inefficient_combinations_with_counts(tuple(p_4d3_4d4), slice(-1, None))
        )
        assert p_4d3_4d4.h(slice(-2, None)) == H(
            _inefficient_combinations_with_counts(tuple(p_4d3_4d4), slice(-2, None))
        )
        assert p_4d3_4d4.h(slice(2)) == H(
            _inefficient_combinations_with_counts(tuple(p_4d3_4d4), slice(None, 2))
        )
        assert p_4d3_4d4.h(slice(1)) == H(
            _inefficient_combinations_with_counts(tuple(p_4d3_4d4), slice(None, 1))
        )

    def test_validate_implementation_combinations_homogeneous_dice(self) -> None:
        # Use the inefficient mechanism to validate our hard-to-understand implementation
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        assert p_4df.h(slice(0, 0)) == H(
            _inefficient_combinations_with_counts(tuple(p_4df), slice(0, 0))
        )
        assert p_4df.h(slice(2, 3)) == H(
            _inefficient_combinations_with_counts(tuple(p_4df), slice(2, 3))
        )
        assert p_4df.h(slice(1, 2)) == H(
            _inefficient_combinations_with_counts(tuple(p_4df), slice(1, 2))
        )
        assert p_4df.h(slice(0, 1)) == H(
            _inefficient_combinations_with_counts(tuple(p_4df), slice(0, 1))
        )


def _inefficient_combinations_with_counts(hs: Sequence[H], key: slice):
    # Generate combinations naively, via Cartesian product, which is much less
    # efficient, but also much easier to read and reason about
    if len(operator.getitem(hs, key)) > 0:
        for rolls in itertools.product(*(h.items() for h in hs)):
            faces, counts = tuple(zip(*rolls))
            sliced_faces = operator.getitem(sorted(faces), key)
            yield sum(sliced_faces), functools.reduce(operator.mul, counts)
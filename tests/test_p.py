# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations, generator_stop

import functools
import itertools
import operator
from typing import Sequence, Tuple

import pytest

from dyce import H, P
from dyce.h import _FaceT
from dyce.p import _analyze_selection, _select_from_end

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
        assert P(p_d6, -p_d6) == p_d6 + p_d6n
        assert P(p_d6n, -p_d6n) == p_d6n + p_d6
        assert 2 @ p_d6 - p_d6 == p_d6 + p_d6 + p_d6n
        assert -(2 @ p_d6) == p_d6n + p_d6n

    def test_op_eq(self) -> None:
        p_d6 = P(6)
        p_d6_2 = P(H(range(6, 0, -1)))
        p_d6_3 = P(p_d6_2)
        assert p_d6_2 == p_d6
        assert p_d6_3 == p_d6_2

        p_d4n = P(-4)
        p_d6 = P(6)
        p_d4n_d6 = P(p_d4n, p_d6)
        p_d6_d4n = P(p_d6, p_d4n)
        assert p_d4n_d6 == p_d6_d4n
        assert p_d4n_d6.h() == p_d6_d4n
        assert p_d4n_d6 == p_d6_d4n.h()
        assert p_d4n_d6.h() == p_d6_d4n.h()
        assert P(p_d6, -4) == p_d4n_d6
        assert P(p_d4n, 6) == p_d4n_d6

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

    def test_getitem_int(self) -> None:
        d4n = H(-4)
        d8 = H(8)
        p_3d4n_3d8 = 3 @ P(d4n, d8)
        assert p_3d4n_3d8[0] == d4n
        assert p_3d4n_3d8[2] == d4n
        assert p_3d4n_3d8[-3] == d8
        assert p_3d4n_3d8[-1] == d8

        with pytest.raises(IndexError):
            _ = p_3d4n_3d8[6]

    def test_getitem_slice(self) -> None:
        d4n = H(-4)
        d8 = H(8)
        p_3d4n_3d8 = 3 @ P(d4n, d8)
        assert p_3d4n_3d8[:] == p_3d4n_3d8
        assert p_3d4n_3d8[:0] == P()
        assert p_3d4n_3d8[6:] == P()
        assert p_3d4n_3d8[2:4] == P(d4n, d8)

    def test_getitem_wrong_type(self) -> None:
        p_d6 = P(6)

        with pytest.raises(TypeError):
            _ = p_d6[""]  # type: ignore

    def test_op_add_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_add_d3n = d2 + d3n
        d3n_add_d2 = d3n + d2
        assert p_d2 + p_d3n == d2_add_d3n
        assert p_d2 + d3n == d2_add_d3n
        assert d2 + p_d3n == d2_add_d3n
        assert p_d3n + p_d2 == d3n_add_d2
        assert p_d3n + d2 == d3n_add_d2
        assert d3n + p_d2 == d3n_add_d2
        assert d2_add_d3n == d3n_add_d2
        assert p_d2 + p_d3n == p_d3n + p_d2

        assert p_d2 + P() == p_d2
        assert P() + p_d2 == p_d2
        assert P() + P() == P()

        p_d2_d3n = P(p_d2, p_d3n)
        assert p_d2 + p_d3n == p_d2_d3n
        assert p_d2_d3n == p_d2 + p_d3n

    def test_op_add_num(self) -> None:
        p_d6 = P(6)
        p_d6_plus = P(H(range(2, 8)))
        p_d8 = P(8)
        p_d8_plus = P(H(range(2, 10)))
        assert 1 + p_d6 == p_d6_plus
        assert p_d8_plus == p_d8 + 1

    def test_op_sub_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_sub_d3n = d2 - d3n
        d3n_sub_d2 = d3n - d2
        assert p_d2 - p_d3n == d2_sub_d3n
        assert p_d2 - d3n == d2_sub_d3n
        assert d2 - p_d3n == d2_sub_d3n
        assert p_d3n - p_d2 == d3n_sub_d2
        assert p_d3n - d2 == d3n_sub_d2
        assert d3n - p_d2 == d3n_sub_d2
        assert p_d2 - p_d3n != p_d3n - p_d2

        assert p_d2 - P() == p_d2
        assert P() - p_d2 == -p_d2
        assert P() - P() == P()

    def test_op_sub_num(self) -> None:
        p_d6 = P(6)
        p_minus_d6 = P(H(range(0, -6, -1)))
        p_d8 = P(8)
        p_d8_minus = P(H(range(0, 8)))
        assert 1 - p_d6 == p_minus_d6
        assert p_d8_minus == p_d8 - 1

    def test_op_mul_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_mul_d3n = d2 * d3n
        d3n_mul_d2 = d3n * d2
        assert p_d2 * p_d3n == d2_mul_d3n
        assert p_d2 * d3n == d2_mul_d3n
        assert d2 * p_d3n == d2_mul_d3n
        assert p_d3n * p_d2 == d3n_mul_d2
        assert p_d3n * d2 == d3n_mul_d2
        assert d3n * p_d2 == d3n_mul_d2
        assert d2_mul_d3n == d3n_mul_d2
        assert p_d2 * p_d3n == p_d3n * p_d2

        assert p_d2 * P() == P()
        assert P() * p_d2 == P()
        assert P() * P() == P()

    def test_op_mul_num(self) -> None:
        p1 = P(H(range(10, 20)))
        p2 = P(H(range(100, 200, 10)))
        assert p2 == p1 * 10
        assert 10 * p1 == p2

    def test_op_matmul(self) -> None:
        d6 = P(6)
        d6_2 = P(d6, d6)
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2

    def test_op_truediv_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_truediv_d3n = d2 / d3n
        d3n_truediv_d2 = d3n / d2
        assert p_d2 / p_d3n == d2_truediv_d3n
        assert p_d2 / d3n == d2_truediv_d3n
        assert d2 / p_d3n == d2_truediv_d3n
        assert p_d3n / p_d2 == d3n_truediv_d2
        assert p_d3n / d2 == d3n_truediv_d2
        assert d3n / p_d2 == d3n_truediv_d2
        assert p_d2 / p_d3n != p_d3n / p_d2

    def test_op_truediv_num(self) -> None:
        p_d10 = P(10)
        p1 = P(H(range(100, 0, -10)))
        assert p_d10 == p1 / 10
        assert (2 * 2 * 2 * 3 * 3 * 5 * 7) / p_d10 == H(
            {
                252.0: 1,
                280.0: 1,
                315.0: 1,
                360.0: 1,
                420.0: 1,
                504.0: 1,
                630.0: 1,
                840.0: 1,
                1260.0: 1,
                2520.0: 1,
            }
        )

    def test_op_floordiv_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_floordiv_d3n = d2 // d3n
        d3n_floordiv_d2 = d3n // d2
        assert p_d2 // p_d3n == d2_floordiv_d3n
        assert p_d2 // d3n == d2_floordiv_d3n
        assert d2 // p_d3n == d2_floordiv_d3n
        assert p_d3n // p_d2 == d3n_floordiv_d2
        assert p_d3n // d2 == d3n_floordiv_d2
        assert d3n // p_d2 == d3n_floordiv_d2
        assert p_d2 // p_d3n != p_d3n // p_d2

        assert p_d2 // P() == P()
        assert P() // p_d2 == P()
        assert P() // P() == P()

    def test_op_floordiv_num(self) -> None:
        p_d10 = P(10)
        p1 = P(H(range(10, 110, 10)))
        p2 = P(H((10, 5, 3, 2, 2, 1, 1, 1, 1, 1)))
        assert p_d10 == p1 // 10
        assert 100 // p1 == p2

    def test_op_mod_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_mod_d3n = d2 % d3n
        d3n_mod_d2 = d3n % d2
        assert p_d2 % p_d3n == d2_mod_d3n
        assert p_d2 % d3n == d2_mod_d3n
        assert d2 % p_d3n == d2_mod_d3n
        assert p_d3n % p_d2 == d3n_mod_d2
        assert p_d3n % d2 == d3n_mod_d2
        assert d3n % p_d2 == d3n_mod_d2
        assert p_d2 % p_d3n != p_d3n % p_d2

        assert p_d2 % P() == P()
        assert P() % p_d2 == P()
        assert P() % P() == P()

    def test_op_mod_num(self) -> None:
        p_d10 = P(10)
        assert p_d10 % 5 == H((1, 2, 3, 4, 0, 1, 2, 3, 4, 0))
        assert 5 % p_d10 == H((0, 1, 2, 1, 0, 5, 5, 5, 5, 5))

    def test_op_pow_h(self) -> None:
        d2 = H(2)
        d3 = H(3)
        p_d2 = P(d2)
        p_d3 = P(d3)
        d2_pow_d3 = d2 ** d3
        d3_pow_d2 = d3 ** d2
        assert p_d2 ** p_d3 == d2_pow_d3
        assert p_d2 ** d3 == d2_pow_d3
        assert d2 ** p_d3 == d2_pow_d3
        assert p_d3 ** p_d2 == d3_pow_d2
        assert p_d3 ** d2 == d3_pow_d2
        assert d3 ** p_d2 == d3_pow_d2
        assert p_d2 ** p_d3 != p_d3 ** p_d2

        assert p_d2 ** P() == P()
        assert P() ** p_d2 == P()
        assert P() ** P() == P()

    def test_op_pow_num(self) -> None:
        p_d5 = P(5)
        assert p_d5 ** 2 == H((1, 4, 9, 16, 25))
        assert 2 ** p_d5 == H((2, 4, 8, 16, 32))
        assert p_d5 ** -1 == H((1, 1 / 2, 1 / 3, 1 / 4, 1 / 5))
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
        assert p_4df.h(slice(2)) == H(
            (sum(roll[slice(2)]), count) for roll, count in p_4df.rolls_with_counts()
        )
        assert p_4df.h(slice(-2, None)) == H(
            (sum(roll[slice(-2, None)]), count)
            for roll, count in p_4df.rolls_with_counts()
        )
        assert p_4df.h(0, 1, 1, 0) == H(
            (sum(roll[i] for i in (1, 0, 0, 1)), count)
            for roll, count in p_4df.rolls_with_counts()
        )
        assert p_4df.h(-2, -1, -1, -2) == H(
            (sum(roll[i] for i in (-1, -2, -2, -1)), count)
            for roll, count in p_4df.rolls_with_counts()
        )

    def test_h_take_n_twice_from_n_homogeneous_dice(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        assert p_4df.h(slice(None), slice(None)) == H(
            (sum(f * 2 for f in roll), count)
            for roll, count in p_4df.rolls_with_counts()
        )

    def test_homogeneous(self) -> None:
        assert P().homogeneous
        assert P(2).homogeneous
        assert P(2, 2).homogeneous
        assert not P(2, -3).homogeneous

    def test_appearances_in_rolls(self) -> None:
        def _sum_method(p: P, face: _FaceT) -> H:
            return H(
                (sum(1 for f in roll if f == face), count)
                for roll, count in p.rolls_with_counts()
            )

        p_empty = P()
        assert p_empty.appearances_in_rolls(0) == _sum_method(p_empty, 0)
        assert p_empty.appearances_in_rolls(0) == H({}).eq(0)

        p_4d6 = 4 @ P(6)
        assert p_4d6.appearances_in_rolls(2) == _sum_method(p_4d6, 2)
        assert p_4d6.appearances_in_rolls(2) == 4 @ H(6).eq(2)
        assert p_4d6.appearances_in_rolls(7) == _sum_method(p_4d6, 7)
        assert p_4d6.appearances_in_rolls(7) == 4 @ H(6).eq(7)

        p_mixed = P(4, 4, 6, 6, 6, H({}))
        assert p_mixed.appearances_in_rolls(3) == _sum_method(p_mixed, 3)
        assert p_mixed.appearances_in_rolls(3) == (
            2 @ H(4).eq(3) + 3 @ H(6).eq(3) + H({}).eq(3)
        )
        assert p_mixed.appearances_in_rolls(5) == _sum_method(p_mixed, 5)
        assert p_mixed.appearances_in_rolls(5) == (
            2 @ H(4).eq(5) + 3 @ H(6).eq(5) + H({}).eq(5)
        )
        assert p_mixed.appearances_in_rolls(7) == _sum_method(p_mixed, 7)
        assert p_mixed.appearances_in_rolls(7) == (
            2 @ H(4).eq(7) + 3 @ H(6).eq(7) + H({}).eq(7)
        )

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
            _brute_force_combinations_with_counts(tuple(p_4d3_4d4), slice(0, 0))
        )
        assert p_4d3_4d4.h(slice(-1, None)) == H(
            _brute_force_combinations_with_counts(tuple(p_4d3_4d4), slice(-1, None))
        )
        assert p_4d3_4d4.h(slice(-2, None)) == H(
            _brute_force_combinations_with_counts(tuple(p_4d3_4d4), slice(-2, None))
        )
        assert p_4d3_4d4.h(slice(2)) == H(
            _brute_force_combinations_with_counts(tuple(p_4d3_4d4), slice(None, 2))
        )
        assert p_4d3_4d4.h(slice(1)) == H(
            _brute_force_combinations_with_counts(tuple(p_4d3_4d4), slice(None, 1))
        )

    def test_validate_implementation_combinations_homogeneous_dice(self) -> None:
        # Use the brute-force mechanism to validate our harder-to-understand
        # implementation
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        assert p_4df.h(slice(0, 0)) == H(
            _brute_force_combinations_with_counts(tuple(p_4df), slice(0, 0))
        )
        assert p_4df.h(slice(2, 3)) == H(
            _brute_force_combinations_with_counts(tuple(p_4df), slice(2, 3))
        )
        assert p_4df.h(slice(1, 2)) == H(
            _brute_force_combinations_with_counts(tuple(p_4df), slice(1, 2))
        )
        assert p_4df.h(slice(0, 1)) == H(
            _brute_force_combinations_with_counts(tuple(p_4df), slice(0, 1))
        )


def test_analyze_selection() -> None:
    which: Tuple[int, ...]

    which = (0,)
    assert _analyze_selection(6, which) == (1, 1)
    which = (0, 2, 1)
    assert _analyze_selection(6, which) == (3, 1)
    which = (0, 2, 1, 2, 1, 0)
    assert _analyze_selection(6, which) == (3, 2)
    which = (0, 1, 0, 0, 1)
    assert _analyze_selection(6, which) == (None, None)

    which = (5,)
    assert _analyze_selection(6, which) == (-1, 1)
    which = (5, 3, 4)
    assert _analyze_selection(6, which) == (-3, 1)
    which = (5, 3, 4, 4, 3, 5)
    assert _analyze_selection(6, which) == (-3, 2)
    which = (5, 4, 5, 5, 4)
    assert _analyze_selection(6, which) == (None, None)

    which = ()
    assert _analyze_selection(6, which) == (0, 0)
    which = (0, 2, 4, 1, 3, 5)
    assert _analyze_selection(6, which) == (6, 1)
    which = (0, 2, 4, 1, 3, 5, 5, 3, 1, 4, 2, 0)
    assert _analyze_selection(6, which) == (6, 2)
    which = (0, 2, 4, 1, 3, 5, 3, 1, 4, 2, 0)
    assert _analyze_selection(6, which) == (None, None)

    which = (1, 3, 2, 4)
    assert _analyze_selection(6, which) == (None, None)
    which = (1, 3, 2, 4, 4, 3, 2, 1)
    assert _analyze_selection(6, which) == (None, None)


def test_select_from_end() -> None:
    h, n, k = H(6), 4, 2
    assert H((sum(roll), count) for roll, count in _select_from_end(h, n, k)) == (
        n @ P(h)
    ).h(slice(k))
    assert H((sum(roll), count) for roll, count in _select_from_end(h, n, -k)) == (
        n @ P(h)
    ).h(slice(-k, None))


def _brute_force_combinations_with_counts(hs: Sequence[H], key: slice):
    # Generate combinations naively, via Cartesian product, which is much less
    # efficient, but also much easier to read and reason about
    if len(operator.getitem(hs, key)) > 0:
        for rolls in itertools.product(*(h.items() for h in hs)):
            faces, counts = tuple(zip(*rolls))
            sliced_faces = operator.getitem(sorted(faces), key)
            yield sum(sliced_faces), functools.reduce(operator.mul, counts)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import functools
import itertools
import operator
from collections import defaultdict
from typing import DefaultDict, Iterator, Sequence, Tuple
from unittest.mock import Mock, patch

import pytest
from numerary import RealLikeSCU
from numerary.bt import beartype

from dyce import H, P
from dyce.p import (
    _analyze_selection,
    _RollCountT,
    _RollT,
    _rwc_homogeneous_n_h_using_karonen_partial_selection,
    _rwc_homogeneous_n_h_using_multinomial_coefficient,
)
from dyce.types import _GetItemT

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


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

    def test_init_symbols(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d6x = H(6) + x
        d8x = H(8) + x
        p_d6x_d8x = P(d8x, d6x)
        assert p_d6x_d8x == P(d6x, d8x)
        assert repr(p_d6x_d8x) == repr(P(d6x, d8x))

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
        try:
            import beartype  # noqa: F401
        except ImportError:
            pass
        else:
            pytest.skip("requires beartype not be installed")

        p_d6 = P(6)

        with pytest.raises(TypeError):
            _ = p_d6[""]  # type: ignore

    def test_getitem_wrong_type_beartype(self) -> None:
        roar = pytest.importorskip("beartype.roar", reason="requires beartype")
        p_d6 = P(6)

        with pytest.raises(roar.BeartypeException):
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

        assert p_d2 + P() == P()
        assert P() + p_d2 == P()
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

        assert p_d2 - P() == P()
        assert P() - p_d2 == P()
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
        h = H(-v if v % 2 else v for v in range(10, 20))
        p = P(h)
        assert -(2 @ p) == -(2 @ h)
        assert +(2 @ p) == +(2 @ h)
        assert abs(2 @ p) == abs(2 @ h)
        assert ~(2 @ p) == ~(2 @ h)

    def test_h_flatten(self) -> None:
        r_d6 = range(1, 7)
        r_d8 = range(1, 9)
        d6_d8 = H(sum(v) for v in itertools.product(r_d6, r_d8) if v)
        p_d6 = P(6)
        p_d8 = P(8)
        p_d6_d8 = P(p_d6, p_d8)
        assert p_d6_d8.h() == d6_d8
        assert P().h() == H({})

    def test_h_flatten_symbol(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        r_d6 = range(1, 7)
        r_d8 = range(1, 9)
        d6x_d8x = H(sum(v) + 2 * x for v in itertools.product(r_d6, r_d8) if v)
        p_d6x = P(H(6) + x)
        p_d8x = P(H(8) + x)
        p_d6x_d8x = P(p_d6x, p_d8x)
        assert p_d6x_d8x.h() == d6x_d8x
        assert p_d6x_d8x.h(slice(None)) == d6x_d8x

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

    def test_h_take_heterogeneous_dice_vs_known_correct(self) -> None:
        p_d3 = P(3)
        p_d3n = -p_d3
        p_d4 = P(4)
        p_d4n = -p_d4
        p_4d3_4d4 = 2 @ P(p_d3, p_d3n, p_d4n, p_d4)

        for which in (
            slice(0, 0),
            slice(-1, None),
            slice(-2, None),
            slice(2),
            slice(1),
        ):
            assert p_4d3_4d4.h(which) == H(
                (sum(roll), count)
                for roll, count in _brute_force_combinations_with_counts(
                    tuple(p_4d3_4d4), which
                )
            )

    def test_h_take_homogeneous_dice_vs_known_correct(self) -> None:
        # Use the brute-force mechanism to validate our harder-to-understand
        # implementation
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df

        for which in (
            slice(0, 0),
            slice(2, 3),
            slice(1, 2),
            slice(0, 1),
        ):
            assert p_4df.h(which) == H(
                (sum(roll), count)
                for roll, count in _brute_force_combinations_with_counts(
                    tuple(p_4df), which
                )
            )

    def test_h_take_n_twice_from_n_homogeneous_dice(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        assert p_4df.h(slice(None), slice(None)) == H(
            (sum(v * 2 for v in roll), count)
            for roll, count in p_4df.rolls_with_counts()
        )

    def test_homogeneous(self) -> None:
        assert P().is_homogeneous
        assert P(2).is_homogeneous
        assert P(2, 2).is_homogeneous
        assert not P(2, -3).is_homogeneous

    def test_appearances_in_rolls(self) -> None:
        def _sum_method(p: P, outcome: RealLikeSCU) -> H:
            return H(
                (sum(1 for v in roll if v == outcome), count)
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

        p_mixed = P(4, 4, 6, 6, 6)
        assert p_mixed.appearances_in_rolls(3) == _sum_method(p_mixed, 3)
        assert p_mixed.appearances_in_rolls(3) == (2 @ H(4).eq(3) + 3 @ H(6).eq(3))
        assert p_mixed.appearances_in_rolls(5) == _sum_method(p_mixed, 5)
        assert p_mixed.appearances_in_rolls(5) == (2 @ H(4).eq(5) + 3 @ H(6).eq(5))
        assert p_mixed.appearances_in_rolls(7) == _sum_method(p_mixed, 7)
        assert p_mixed.appearances_in_rolls(7) == (2 @ H(4).eq(7) + 3 @ H(6).eq(7))

    def test_roll(self) -> None:
        d10 = H(10)
        p_6d10 = 6 @ P(d10)

        for _ in range(100):
            roll = p_6d10.roll()
            assert len(roll) == len(p_6d10)
            assert all(v in d10 for v in roll)

    def test_roll_symbols(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d10x = H(10) + x
        p_6d10x = 6 @ P(d10x)

        for _ in range(50):
            roll = p_6d10x.roll()
            assert len(roll) == len(p_6d10x)
            assert all(v in d10x for v in roll)

    def test_rolls_with_counts_empty(self) -> None:
        assert tuple(P().rolls_with_counts()) == ()

    def test_rolls_with_counts_heterogeneous(self) -> None:
        assert sorted(P(2, 3).rolls_with_counts()) == [
            ((1, 1), 1),
            ((1, 2), 1),
            # originated as ((2, 1), 1), but outcomes get sorted in each roll
            ((1, 2), 1),
            ((1, 3), 1),
            ((2, 2), 1),
            ((2, 3), 1),
        ]

    def test_rolls_with_counts_homogeneous(self) -> None:
        assert sorted(P(2, 2).rolls_with_counts()) == [
            ((1, 1), 1),
            ((1, 2), 2),
            ((2, 2), 1),
        ]

    def test_rolls_with_counts_take_heterogeneous_dice_vs_known_correct(self) -> None:
        p_d3 = P(3)
        p_d4n = P(-4)
        p_3d3_4d4n = P(3 @ p_d3, 4 @ p_d4n)

        for which in (
            # All outcomes
            slice(None),
            # 4 outcomes
            slice(4),
            slice(-4, None),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_3d3_4d4n, which)
            karonen.assert_not_called()
            multinomial_coefficient.assert_called()

        for which in (
            # 3 outcomes
            slice(3),
            slice(-3, None),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_3d3_4d4n, which)
            karonen.assert_called()  # called for 4d4n where k < n
            multinomial_coefficient.assert_called()  # called for 3d3 where k == n

        for which in (
            # 2 outcomes
            slice(2),
            slice(-2, None),
            # 1 outcome
            slice(1),
            slice(-1, None),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_3d3_4d4n, which)
            karonen.assert_called()
            multinomial_coefficient.assert_not_called()

        for which in (
            # No outcomes
            slice(0, 0),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_3d3_4d4n, which)
            karonen.assert_not_called()
            multinomial_coefficient.assert_not_called()

    def test_rolls_with_counts_take_homogeneous_dice_vs_known_correct(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df

        for which in (
            # All outcomes
            slice(None),
            slice(0, 4),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_4df, which)
            karonen.assert_not_called()
            multinomial_coefficient.assert_called()

        for which in (
            # 1 Outcome
            slice(0, 1),
            slice(1, 2),
            slice(2, 3),
            slice(3, 4),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_4df, which)
            karonen.assert_called()
            multinomial_coefficient.assert_not_called()

        for which in (
            # No outcomes
            slice(0, 0),
        ):
            karonen, multinomial_coefficient = _rwc_validation_helper(p_4df, which)
            karonen.assert_not_called()
            multinomial_coefficient.assert_not_called()


def test_analyze_selection() -> None:
    which: Tuple[_GetItemT, ...]

    which = (0,)
    assert _analyze_selection(6, which) == 1
    which = (-1,)
    assert _analyze_selection(6, which) == -1
    which = (0, 1, 0, 0, 1)
    assert _analyze_selection(6, which) == 2
    which = (0, 1, 0, 0, 1, 4)
    assert _analyze_selection(6, which) == 5
    which = (5, 1, 5, 5, 1, 4)
    assert _analyze_selection(6, which) == -5

    which = tuple(range(6))
    assert _analyze_selection(6, which) == 6
    which = tuple(range(0, -6, -1))
    assert _analyze_selection(6, which) == 6
    which = tuple(range(6)) + tuple(range(0, -6, -1))
    assert _analyze_selection(6, which) == 12
    which = (slice(None),)
    assert _analyze_selection(6, which) == 6
    which = (slice(0, None), slice(-6, None))
    assert _analyze_selection(6, which) == 12

    which = (-1, 0)
    assert _analyze_selection(6, which) is None
    which = tuple(range(6)) + tuple(range(3))
    assert _analyze_selection(6, which) is None

    which = (2,)
    assert _analyze_selection(6, which) == 3
    which = (3,)
    assert _analyze_selection(6, which) == -3
    which = (2, 3)
    assert _analyze_selection(6, which) == 4
    which = (1, 2, 3)
    assert _analyze_selection(6, which) == 4
    which = (2, 3, 4)
    assert _analyze_selection(6, which) == -4

    which = (2,)
    assert _analyze_selection(5, which) == 3
    which = (1, 2)
    assert _analyze_selection(5, which) == 3
    which = (2, 3)
    assert _analyze_selection(5, which) == -3

    which = ()
    assert _analyze_selection(0, which) == 0
    which = ()
    assert _analyze_selection(6, which) == 0
    which = (slice(0, 0),)
    assert _analyze_selection(6, which) == 0

    with pytest.raises(IndexError):
        which = (1,)
        _ = _analyze_selection(0, which)


@beartype
def _brute_force_combinations_with_counts(
    hs: Sequence[H], key: slice
) -> Iterator[_RollCountT]:
    # Generate combinations naively, via Cartesian product, which is much less
    # efficient, but also much easier to read and reason about
    if len(operator.__getitem__(hs, key)) > 0:
        for rolls in itertools.product(*(h.items() for h in hs)):
            outcomes, counts = tuple(zip(*rolls))
            sliced_outcomes = tuple(operator.__getitem__(sorted(outcomes), key))
            count = functools.reduce(operator.__mul__, counts)
            yield sliced_outcomes, count


@beartype
def _rwc_validation_helper(p: P, which: slice) -> Tuple[Mock, Mock]:
    # Use the brute-force mechanism to validate our harder-to-understand implementation.
    # Note that there can be repeats and order is not guaranteed, which is why we have
    # to accumulate counts for rolls and then compare entire results.
    known_counts: DefaultDict[_RollT, int] = defaultdict(int)
    test_counts: DefaultDict[_RollT, int] = defaultdict(int)

    for roll, count in _brute_force_combinations_with_counts(tuple(p), which):
        known_counts[roll] += count

    with patch(
        "dyce.p._rwc_homogeneous_n_h_using_karonen_partial_selection",
        side_effect=_rwc_homogeneous_n_h_using_karonen_partial_selection,
    ) as karonen, patch(
        "dyce.p._rwc_homogeneous_n_h_using_multinomial_coefficient",
        side_effect=_rwc_homogeneous_n_h_using_multinomial_coefficient,
    ) as multinomial_coefficient:
        for roll, count in p.rolls_with_counts(which):
            test_counts[roll] += count

    assert test_counts == known_counts, f"which: {which}"

    return karonen, multinomial_coefficient

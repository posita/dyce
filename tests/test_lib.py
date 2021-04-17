# -*- encoding: utf-8 -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If that file is missing or appears to be
modified from its original, then please contact the author before viewing or using this
software in any capacity.
"""
# ======================================================================================

from __future__ import generator_stop
from typing import Optional, Sequence

import functools
import itertools
import operator
import os

from dyce.lib import D, H, _within

__all__ = ()


# ---- Classes -------------------------------------------------------------------------


class TestH:
    def test_init(self) -> None:
        assert H(()) == {}
        assert H(0) == {}
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
        assert base == base.concat(base)
        assert base == base.concat(base).concat(base)
        assert base.concat(base) == base.concat(base).concat(base)
        assert base != base.concat((0,))

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
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2
        assert d6_3 == 3 @ d6
        assert 4 @ d6 == d6 @ 2 @ 2

    def test_filter(self) -> None:
        d6 = H(range(1, 7))
        d8 = H(range(1, 9))
        within_filter = _within(-1, 1)

        def _within_filter(a: int, b: int) -> bool:
            return bool(within_filter(a, b))

        h_d8_v_d6 = d8.filter(_within_filter, d6, t_val=1, f_val=0)
        assert h_d8_v_d6 == {0: 17, 1: 31}

    def test_map(self) -> None:
        d6 = H(range(1, 7))
        d8 = H(range(1, 9))
        within_filter = _within(-1, 1)
        h_d8_v_d6 = d8.map(within_filter, d6)
        assert h_d8_v_d6 == {-1: 10, 0: 17, 1: 21}

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

    def test_concat(self) -> None:
        h = H(itertools.chain(range(0, 6), range(3, 9)))
        assert H(range(0, 6)).concat(H(range(3, 9))) == h

    def test_concat_does_not_invoke_lowest_terms(self) -> None:
        base = H(range(10))
        assert dict(base) != dict(base.concat(base))

    def test_format(self) -> None:
        assert H((1, 2, 3, 1, 2, 1)).format(width=115) == os.linesep.join(
            (
                "avg |    1.67",
                "  1 |  50.00% |##################################################",
                "  2 |  33.33% |#################################",
                "  3 |  16.67% |################",
            )
        )
        assert (
            H((1, 2, 3, 1, 2, 1)).format(width=0)
            == "{avg: 1.67, 1: 50.00%, 2: 33.33%, 3: 16.67%}"
        )

    def test_len_and_counts(self) -> None:
        h0 = H({})
        h6h8 = H(6) + H(8)
        assert len(h0) == 0
        assert len(h6h8) == 13  # num distinct values
        assert sum(h6h8.counts()) == 48  # combinations
        assert len((h6h8 + h6h8)) == 25
        assert sum((h6h8 + h6h8).counts()) == 2304

    def test_lowest_terms_identity(self) -> None:
        lowest_terms = H({i: i for i in range(10)})
        assert dict(lowest_terms) == dict(lowest_terms.lowest_terms())

    def test_substitute_double_odd_values(self) -> None:
        def double_odd_values(
            h: H,  # pylint: disable=unused-argument
            face: int,
        ) -> Optional[H]:
            return H({face * 2: 1}) if face % 2 != 0 else None

        h = H(4)
        assert h.substitute(double_odd_values) == H({6: 1, 4: 2, 2: 3})
        assert h.substitute(double_odd_values, max_depth=2) == H({6: 1, 4: 2, 2: 3})

    def test_substitute_never_expand(self) -> None:
        def never_expand(
            h: H,  # pylint: disable=unused-argument
            face: int,  # pylint: disable=unused-argument
        ) -> Optional[H]:
            return None

        h = H(20)
        assert h.substitute(never_expand) == h
        assert h.substitute(never_expand, operator.add, 20) == h

    def test_substitute_reroll_d4_threes(self) -> None:
        def reroll_d4_threes(h: H, face: int) -> Optional[H]:
            return h if max(h) == 4 and face == 3 else None

        h = H(4)
        assert h.substitute(reroll_d4_threes) == H({4: 5, 3: 1, 2: 5, 1: 5})
        assert h.substitute(reroll_d4_threes, operator.add) == H(
            {7: 1, 6: 1, 5: 1, 4: 5, 2: 4, 1: 4}
        )
        assert h.substitute(reroll_d4_threes, operator.mul, max_depth=2) == H(
            {36: 1, 27: 1, 18: 1, 12: 4, 9: 1, 6: 4, 4: 16, 3: 4, 2: 16, 1: 16}
        )


class TestD:
    def test_init_empty(self) -> None:
        assert D(0) == D()

    def test_init_neg(self) -> None:
        d2n = D(-2)
        h_d2n = H(range(-1, -3, -1))
        assert d2n.h() == h_d2n

    def test_init_pos(self) -> None:
        d6 = D(6)
        h_d6 = H(range(1, 7))
        assert d6.h() == h_d6

    def test_init_one_histogram(self) -> None:
        h = H(range(0, -10, -1))
        assert D(h).h() == h

    def test_init_multiple_histograms(self) -> None:
        h_d6 = H(6)
        d6 = D(6)
        d6_2 = D(h_d6, h_d6)
        assert d6_2.h() == H(sum(v) for v in itertools.product(h_d6, h_d6))
        assert D(d6, d6) == d6_2
        assert D(d6, h_d6) == d6_2
        assert D(h_d6, d6) == d6_2

    def test_init_exclude_empty_histograms(self) -> None:
        assert D(H({})) == D()
        assert D(2, H({}), 2, H({})) == D(2, 2)

    def test_repr(self) -> None:
        assert repr(D()) == "D()"
        assert repr(D(0)) == "D()"
        assert repr(D(-6)) == "D(-6)"
        assert repr(D(6)) == "D(6)"
        assert (
            repr(D(D(6), D(8), D(H({3: 1, 2: 2, 1: 3, 0: 1}))))
            == "D(H({0: 1, 1: 3, 2: 2, 3: 1}), 6, 8)"
        )

    def test_op_eq(self) -> None:
        d6_1 = D(H(range(6, 0, -1)))
        d6_2 = D(6)
        d6_3 = D(d6_2)
        assert d6_2 == d6_1
        assert d6_3 == d6_2

    def test_op_eq_ignores_order(self) -> None:
        h4 = H(4)
        h6 = H(6)
        assert D(h4, h6) == D(h6, h4)

    def test_op_eq_invokes_lowest_terms(self) -> None:
        h4 = H(4)
        h6 = H(6)
        assert D(h4, h6) == D(h4.concat(h4), h6.concat(h6))

    def test_op_ne(self) -> None:
        d6 = D(6)
        h6n = H(range(-1, -7, -1))
        d6n = D(h6n)
        assert d6n != d6

    def test_len(self) -> None:
        d0_1 = D()
        d0_2 = D(H({}))
        d6 = D(6)
        d8 = D(8)
        assert len(d0_1) == 0
        assert len(d0_2) == 0
        assert len(d6) == 1
        assert len(d8) == 1
        assert len(D(d6, d8)) == 2
        assert len(D(d6, d8, d6, d8)) == 4

    def test_getitem_empty(self) -> None:
        d_empty = D()
        assert d_empty[:] == d_empty.h()

    def test_getitem_identity(self) -> None:
        d20s = 5 @ D(20)
        assert d20s[:] == d20s.h()

    def test_getitem_nonuniform_dice(self) -> None:
        d4 = D(4)
        d8 = D(8)
        ds_mixed = 3 @ D(d4, d8, d4)
        assert ds_mixed[:] == ds_mixed.h()
        assert ds_mixed[range(len(ds_mixed))] == ds_mixed.h()
        assert ds_mixed[:1] == ds_mixed[0]
        assert ds_mixed[(0,)] == ds_mixed[0]
        assert ds_mixed[-1:] == ds_mixed[-1]
        assert ds_mixed[(-1,)] == ds_mixed[-1]
        assert ds_mixed[0, 2] == ds_mixed[:3:2]
        assert ds_mixed[0, 2::2] == ds_mixed[::2]
        assert ds_mixed[0, 2, 4, 6, 8] == ds_mixed[::2]
        assert ds_mixed[range(0, len(ds_mixed), 2)] == ds_mixed[::2]
        assert ds_mixed[(i for i in range(len(ds_mixed)) if i & 0x1)] == ds_mixed[1::2]
        assert ds_mixed[-2:] == {
            2: 1,
            3: 9,
            4: 511,
            5: 2304,
            6: 19165,
            7: 57513,
            8: 203095,
            9: 196608,
            10: 249853,
            11: 306432,
            12: 353053,
            13: 245760,
            14: 212992,
            15: 159744,
            16: 90112,
        }
        assert ds_mixed[:2] == {
            2: 1239848,
            3: 558873,
            4: 235398,
            5: 48384,
            6: 13699,
            7: 825,
            8: 125,
        }
        assert ds_mixed[::2] == {
            5: 1,
            6: 45,
            7: 327,
            8: 2163,
            9: 8271,
            10: 21409,
            11: 54051,
            12: 88437,
            13: 133858,
            14: 190958,
            15: 253810,
            16: 303398,
            17: 319022,
            18: 290062,
            19: 193026,
            20: 121930,
            21: 65741,
            22: 31253,
            23: 13383,
            24: 4583,
            25: 1171,
            26: 225,
            27: 27,
            28: 1,
        }

    def test_getitem_uniform_dice(self) -> None:
        d6_ish = D(H((2, 3, 3, 4, 4, 5)))
        d6_ish_2 = 2 @ d6_ish
        assert d6_ish_2[:] == d6_ish_2.h()
        assert d6_ish_2[:1] == {2: 11, 3: 16, 4: 8, 5: 1}
        assert d6_ish_2[-1:] == {2: 1, 3: 8, 4: 16, 5: 11}

    def test_op_add_d(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 + d3 == H((2, 3, 4, 3, 4, 5))
        assert d3 + d2 == H((2, 3, 3, 4, 4, 5))
        assert d2 + d3 == d3 + d2
        d2d3 = D(d2, d3)
        assert d2 + d3 == d2d3.h()

    def test_op_add_int(self) -> None:
        d6 = D(6)
        d6_plus = D(H(range(2, 8)))
        d8 = D(8)
        d8_plus = D(H(range(2, 10)))
        assert 1 + d6 == d6_plus
        assert d8_plus == d8 + 1

    def test_op_sub_d(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 - d3 == H((0, -1, -2, 1, 0, -1))
        assert d3 - d2 == H((0, -1, 1, 0, 2, 1))

    def test_op_sub_int(self) -> None:
        d6 = D(6)
        minus_d6 = D(H(range(0, -6, -1)))
        d8 = D(8)
        d8_minus = D(H(range(0, 8)))
        assert 1 - d6 == minus_d6
        assert d8_minus == d8 - 1

    def test_op_mul_d(self) -> None:
        d2 = D(2)
        d3 = D(3)
        assert d2 * d3 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert d3 * d2 == {1: 1, 2: 2, 3: 1, 4: 1, 6: 1}
        assert d2 * d3 == d3 * d2

    def test_op_mul_int(self) -> None:
        die1 = D(H(range(10, 20)))
        die2 = D(H(range(100, 200, 10)))
        assert die2 == die1 * 10
        assert 10 * die1 == die2

    def test_op_matmul(self) -> None:
        d6 = D(6)
        d6_2 = D(d6, d6)
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2

    def test_op_floordiv_d(self) -> None:
        die1 = D(H((1, 4)))
        die2 = D(H((1, 2)))
        assert die1 // die2 == H((1, 0, 4, 2))
        assert die2 // die1 == H((1, 0, 2, 0))

    def test_op_floordiv_int(self) -> None:
        d10 = D(10)
        die1 = D(H(range(10, 110, 10)))
        die2 = D(H((10, 5, 3, 2, 2, 1, 1, 1, 1, 1)))
        assert d10 == die1 // 10
        assert 100 // die1 == die2

    def test_op_mod_d(self) -> None:
        die1 = H((1, 5))
        die2 = H((1, 3))
        assert die1 % die2 == H((0, 1, 0, 2))
        assert die2 % die1 == H((0, 1, 0, 3))

    def test_op_mod_int(self) -> None:
        d10 = D(10)
        assert d10 % 5 == H((1, 2, 3, 4, 0, 1, 2, 3, 4, 0))
        assert 5 % d10 == H((0, 1, 2, 1, 0, 5, 5, 5, 5, 5))

    def test_op_pow_d(self) -> None:
        die1 = D(H((2, 5)))
        die2 = D(H((3, 4)))
        assert die1 ** die2 == H((8, 16, 125, 625))
        assert die2 ** die1 == H((9, 243, 16, 1024))

    def test_op_pow_int(self) -> None:
        d5 = D(5)
        assert d5 ** 2 == H((1, 4, 9, 16, 25))
        assert 2 ** d5 == H((2, 4, 8, 16, 32))
        assert d5 ** -1 == H((1, 0, 0, 0, 0))
        assert (-1) ** d5 == H((-1, 1, -1, 1, -1))

    def test_op_bitwise(self) -> None:
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

    def test_h_flatten(self) -> None:
        r_d6 = range(1, 7)
        r_d8 = range(1, 7)
        h_d6d8 = H(sum(v) for v in itertools.product(r_d6, r_d8) if v)
        d6 = D(6)
        d8 = D(6)
        d6d8 = D(d6, d8)
        assert d6d8.h() == h_d6d8
        assert D().h() == H({})

    def test_h_index(self) -> None:
        d4 = D(4)
        d8 = D(8)
        ds_mixed = 3 @ D(d4, d8, d4)
        assert ds_mixed.h(0) == d4.h()
        assert ds_mixed.h(1) == d4.h()
        assert ds_mixed.h(2) == d4.h()
        assert ds_mixed.h(-2) == d8.h()
        assert ds_mixed.h(-1) == d8.h()

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

    def test_validate_implementation_combinations_nonuniform_dice(self) -> None:
        d2 = D(2)
        d3 = D(3)
        d4 = D(4)
        d2d3d4 = D(d2, d3, d4)
        assert d2d3d4[:] == d2d3d4.h()
        assert d2d3d4[-1:] == {1: 1, 2: 7, 3: 10, 4: 6}
        assert d2d3d4[-1:] == H(
            _inefficient_combinations_with_counts(tuple(d2d3d4), slice(-1, None))
        )
        assert d2d3d4[-2:] == {2: 1, 3: 3, 4: 6, 5: 7, 6: 5, 7: 2}
        assert d2d3d4[-2:] == H(
            _inefficient_combinations_with_counts(tuple(d2d3d4), slice(-2, None))
        )
        assert d2d3d4[:2] == {2: 7, 3: 9, 4: 6, 5: 2}
        assert d2d3d4[:2] == H(
            _inefficient_combinations_with_counts(tuple(d2d3d4), slice(None, 2))
        )
        assert d2d3d4[:1] == {1: 18, 2: 6}
        assert d2d3d4[:1] == H(
            _inefficient_combinations_with_counts(tuple(d2d3d4), slice(None, 1))
        )

    def test_validate_implementation_combinations_uniform_dice(self) -> None:
        # Use the inefficient mechanism to validate our hard-to-understand implementation
        h6 = H(6)
        d6 = D(h6)
        d6s = 3 @ d6
        assert d6s[2:3] == {1: 1, 2: 7, 3: 19, 4: 37, 5: 61, 6: 91}
        assert d6s[2:3] == H(
            _inefficient_combinations_with_counts((h6, h6, h6), slice(2, 3))
        )
        assert d6s[1:2] == {1: 16, 2: 40, 3: 52, 4: 52, 5: 40, 6: 16}
        assert d6s[1:2] == H(
            _inefficient_combinations_with_counts((h6, h6, h6), slice(1, 2))
        )
        assert d6s[0:1] == {1: 91, 2: 61, 3: 37, 4: 19, 5: 7, 6: 1}
        assert d6s[0:1] == H(
            _inefficient_combinations_with_counts((h6, h6, h6), slice(0, 1))
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


def _inefficient_combinations_with_counts(hs: Sequence[H], key: slice):
    # Generate combinations naively, via Cartesian product, which is much less
    # efficient, but also much easier to read and reason about
    if len(operator.getitem(hs, key)) > 0:
        for rolls in itertools.product(*(h.items() for h in hs)):
            faces, counts = tuple(zip(*rolls))
            sliced_faces = operator.getitem(sorted(faces), key)
            yield sum(sliced_faces), functools.reduce(operator.mul, counts)

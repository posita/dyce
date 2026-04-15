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

import operator
import warnings
from collections import Counter
from collections.abc import Iterator, Sequence
from decimal import Decimal
from fractions import Fraction
from itertools import chain, combinations_with_replacement, groupby
from itertools import product as iproduct
from math import factorial, prod
from typing import Any, TypeVar
from unittest.mock import Mock, call, patch

import pytest

from dyce import H, P
from dyce.h import _ConvolveFallbackWarning
from dyce.p import (
    _MAX_FILL,
    _MIN_FILL,
    RollCountT,
    RollT,
    _analyze_selection,
    _rwc_heterogeneous_extremes,
    _rwc_homogeneous_n_h_using_partial_selection,
    _SelectionEmpty,
    _SelectionExtremes,
    _SelectionPrefix,
    _SelectionSuffix,
    _SelectionUniform,
)
from dyce.types import _GetItemT, natural_key

from .test_h import _OUTCOME_TYPES
from .test_types import _NoCompare

__all__ = ()

_T = TypeVar("_T")


class TestPInit:
    def test_empty(self) -> None:
        assert P(H(())) == P()
        assert P(H({})) == P()
        assert P() == H({})
        assert len(P()) == 0

    def test_int_zero_is_empty(self) -> None:
        assert P(0) == H({})
        assert len(P(0)) == 0

    def test_int_scalar(self) -> None:
        assert P(6) == P(H(6))
        assert P(-6) == P(H(-6))

    def test_non_int_scalar_raises(self) -> None:
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            P(None)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            P(3.0)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            P(Fraction(3))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            P(Decimal(3))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    def test_h(self) -> None:
        h = H({1: 1, 2: 2})
        assert list(P(h)) == [h]

    def test_p_flattened(self) -> None:
        p = P(4, P(6, P(8)))
        assert list(p) == [H(4), H(6), H(8)]
        p = P(2 @ P(3 @ P(6, 2 @ P(4))), P(8, 10), P(8, P(10)), P(10, P(8)))
        assert p == P(12 @ P(4), 6 @ P(6), 3 @ P(8), 3 @ P(10))
        assert list(p) == 12 * [H(4)] + 6 * [H(6)] + 3 * [H(8)] + 3 * [H(10)]

    def test_empty_h_filtered(self) -> None:
        assert P(P(4), H({}), H(6)) == P(H(4), H(6))

    def test_h_order(self) -> None:
        from dyce import p as p_module

        d4pls1 = H(4) + 1
        d6pls1 = H(6) + 1
        with patch.object(
            p_module, "natural_key", side_effect=p_module.natural_key
        ) as mock:
            p = P(d4pls1, 8, 6, 4, d6pls1)
            mock.assert_not_called()
        assert list(p) == [H(4), H(6), H(8), d4pls1, d6pls1]
        assert repr(p) == repr(P(4, 6, 8, d4pls1, d6pls1))

    def test_h_order_symbols(self) -> None:
        from dyce import p as p_module

        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d6x = H(6) + x
        d8x = H(8) + x
        with patch.object(
            p_module, "natural_key", side_effect=p_module.natural_key
        ) as mock:
            p = P(d8x, d6x)
            mock.assert_not_called()
        assert list(p) == [d6x, d8x]
        assert repr(p) == repr(P(d6x, d8x))

    def test_h_natural_order(self) -> None:
        from dyce import p as p_module

        hs = [
            H({_NoCompare(str(i**2 * (-1) ** i) + "abc" + str(-i)) for i in range(n)})
            for n in range(1, 6)
        ]
        with patch.object(
            p_module, "natural_key", side_effect=p_module.natural_key
        ) as mock:
            p = P(8, 4, *hs, 6)
            mock.assert_called()
        assert (
            str(list(p))
            == "[H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), H({1: 1, 2: 1, 3: 1, 4: 1}), "
            "H({_NoCompare('0abc0'): 1, _NoCompare('4abc-2'): 1, _NoCompare('16abc-4'): 1, _NoCompare('-1abc-1'): 1, _NoCompare('-9abc-3'): 1}), "
            "H({_NoCompare('0abc0'): 1, _NoCompare('4abc-2'): 1, _NoCompare('-1abc-1'): 1, _NoCompare('-9abc-3'): 1}), "
            "H({_NoCompare('0abc0'): 1, _NoCompare('4abc-2'): 1, _NoCompare('-1abc-1'): 1}), "
            "H({_NoCompare('0abc0'): 1, _NoCompare('-1abc-1'): 1}), "
            "H({_NoCompare('0abc0'): 1})]"
        )


class TestPRepr:
    def test_single(self) -> None:
        assert repr(P(6)) == "P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))"

    def test_homogeneous(self) -> None:
        assert repr(2 @ P(6)) == "2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))"
        assert repr(3 @ P(6)) == "3@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))"

    def test_heterogeneous(self) -> None:
        assert repr(P(4, 6, 8)) == (
            "P("
            "H({1: 1, 2: 1, 3: 1, 4: 1}), "
            "H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), "
            "H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1})"
            ")"
        )

    def test_heterogeneous_with_duplicates(self) -> None:
        assert repr(P(4, 6, 6, 8, 10, 10)) == (
            "P("
            "H({1: 1, 2: 1, 3: 1, 4: 1}), "
            "2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})), "
            "H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}), "
            "2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1}))"
            ")"
        )


class TestPEq:
    def test_equal(self) -> None:
        assert P(4, 6) == P(4, 6)
        assert P(4, 6) == P(6, 4)  # sorted

    def test_not_equal(self) -> None:
        assert P(4, 6) != P(4, 8)
        assert P(4, 6) != P(4)
        assert P(4, 6) != P(6)

    def test_not_equal_to_non_p(self) -> None:
        # P.__eq__ returns NotImplemented for non-P; H.__eq__ then considers P(6) ==
        # H(6) True via HableT (both flatten to the same histogram)
        assert (P(6) == H(6)) is True
        assert P(6) != 6

    def test_ne_is_complement_of_eq(self) -> None:
        assert (P(4, 6) != P(4, 6)) is False
        assert (P(4, 6) != P(4, 8)) is True

    def test_eq_order_independent(self) -> None:
        assert P(H(4), H(6)) == P(H(6), H(4))

    def test_eq_invokes_lowest_terms(self) -> None:
        d4 = H(4)
        d6 = H(6)
        p = P(d4, d6)
        assert hash(p) == hash(P(d4.merge(d4), d6.merge(d6)))
        assert hash(p) == p._hash  # noqa: SLF001

    def test_eq_sanity_check(self) -> None:
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


class TestPSequence:
    def test_int_index(self) -> None:
        p = P(4, 6, 8)
        assert p[0] == H(4)
        assert p[1] == H(6)
        assert p[2] == H(8)

    def test_negative_index(self) -> None:
        p = P(4, 6, 8)
        assert p[-1] == H(8)
        assert p[-3] == H(4)

    def test_slice(self) -> None:
        p = P(4, 6, 8)
        assert p[1:] == P(6, 8)
        assert p[:2] == P(4, 6)
        assert p[::2] == P(4, 8)

    def test_slice_returns_p(self) -> None:
        assert isinstance(P(4, 6, 8)[1:], P)

    def test_which_out_of_range_index_raises(self) -> None:
        with pytest.raises(IndexError):
            P()[0]
        with pytest.raises(IndexError):
            P()[-1]
        with pytest.raises(IndexError):
            P(6)[1]
        with pytest.raises(IndexError):
            P(6)[-2]

    def test_which_out_of_range_slice_empty(self) -> None:
        assert P()[0:1] == H({})
        assert P()[-2:-1] == H({})
        assert P(6)[1:2] == H({})
        assert P(6)[-3:-2] == H({})

    def test_ordering_invariant(self) -> None:
        assert P(8, 6, 4)[0] == P(8, 4, 6)[0] == H(4)

    def test_getitem_complex(self) -> None:
        d4n = H(-4)
        d8 = H(8)
        p = 3 @ P(d4n, d8)
        assert p[0] == d4n
        assert p[2] == d4n
        assert p[-3] == d8
        assert p[-1] == d8
        assert p[:] == p
        assert p[:0] == P()
        assert p[6:] == P()
        assert p[2:4] == P(d4n, d8)

    def test_iter_empty(self) -> None:
        assert list(P()) == []

    def test_iter(self) -> None:
        assert list(P(4, 2 @ P(6), 8)) == [H(4), H(6), H(6), H(8)]

    def test_len_empty(self) -> None:
        assert len(P()) == 0

    def test_len(self) -> None:
        assert len(P(6)) == 1
        assert len(P(4, 6, 8)) == 3
        assert len(2 @ P(6)) == 2
        assert len(P(2 @ P(6), 2 @ P(8))) == 4

    def test_as_bool(self) -> None:
        assert bool(P()) is False
        assert bool(P(6)) is True
        assert bool(P(*(H({}) for _ in range(10)))) is False


class TestPMatmul:
    def test_matmul_returns_p(self) -> None:
        assert isinstance(2 @ P(6), P)

    def test_matmul_correct_length(self) -> None:
        assert len(2 @ P(6)) == 2
        assert len(3 @ P(6)) == 3

    def test_matmul_zero(self) -> None:
        assert 0 @ P(6) == P()

    def test_matmul_one(self) -> None:
        assert 1 @ P(6) == P(6)

    def test_rmatmul(self) -> None:
        assert 2 @ P(6) == P(6, 6)

    def test_matmul_negative_returns_not_implemented(self) -> None:
        result = P(6).__matmul__(-1)
        assert result is NotImplemented

    def test_matmul_composition(self) -> None:
        assert 2 @ (2 @ P(6)) == 4 @ P(6)

    def test_matmul_negative_rhs(self) -> None:
        result = P(6).__matmul__(-1)
        assert result is NotImplemented
        with pytest.raises(TypeError):
            _ = -1 @ P(6)

    def test_rmatmul_non_int_rhs(self) -> None:
        result = P(6).__rmatmul__(1.5)
        assert result is NotImplemented
        with pytest.raises(TypeError):
            _ = 1.5 @ P(6)

    def test_op_matmul(self) -> None:
        d6 = P(6)
        d6_2 = P(d6, d6)
        assert 2 @ d6 == d6_2
        assert d6_2 == d6 @ 2


class TestPOp:
    def test_op_add_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 + P() == H({})
        assert P() + p_d2 == H({})
        assert P() + P() == H({})

    def test_op_add_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_add_d3n = d2 + d3n
        d3n_add_d2 = d3n + d2
        assert p_d2 + p_d3n == d2_add_d3n
        assert p_d2 + d3n == d2_add_d3n
        assert d2 + p_d3n == d2_add_d3n  # H + P — exercises _flatten_to_h
        assert p_d3n + p_d2 == d3n_add_d2
        assert p_d3n + d2 == d3n_add_d2
        assert d3n + p_d2 == d3n_add_d2  # H + P
        assert d2_add_d3n == d3n_add_d2
        assert p_d2 + p_d3n == p_d3n + p_d2

    def test_op_add_num(self) -> None:
        p_d6 = P(6)
        p_d6_plus = P(H(range(2, 8)))
        p_d8 = P(8)
        p_d8_plus = P(H(range(2, 10)))
        assert 1 + p_d6 == p_d6_plus
        assert p_d8_plus == p_d8 + 1

    def test_op_sub_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 - P() == P()
        assert P() - p_d2 == P()
        assert P() - P() == P()

    def test_op_sub_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_sub_d3n = d2 - d3n
        d3n_sub_d2 = d3n - d2
        assert p_d2 - p_d3n == d2_sub_d3n
        assert p_d2 - d3n == d2_sub_d3n
        assert d2 - p_d3n == d2_sub_d3n  # H - P
        assert p_d3n - p_d2 == d3n_sub_d2
        assert p_d3n - d2 == d3n_sub_d2
        assert d3n - p_d2 == d3n_sub_d2  # H - P
        assert p_d2 - p_d3n != p_d3n - p_d2

    def test_op_sub_num(self) -> None:
        p_d6 = P(6)
        p_minus_d6 = P(H(range(0, -6, -1)))
        p_d8 = P(8)
        p_d8_minus = P(H(range(8)))
        assert 1 - p_d6 == p_minus_d6
        assert p_d8_minus == p_d8 - 1

    def test_op_mul_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 * P() == P()
        assert P() * p_d2 == P()
        assert P() * P() == P()

    def test_op_mul_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_mul_d3n = d2 * d3n
        d3n_mul_d2 = d3n * d2
        assert p_d2 * p_d3n == d2_mul_d3n
        assert p_d2 * d3n == d2_mul_d3n
        assert d2 * p_d3n == d2_mul_d3n  # H * P
        assert p_d3n * p_d2 == d3n_mul_d2
        assert p_d3n * d2 == d3n_mul_d2
        assert d3n * p_d2 == d3n_mul_d2  # H * P
        assert d2_mul_d3n == d3n_mul_d2
        assert p_d2 * p_d3n == p_d3n * p_d2

    def test_op_mul_num(self) -> None:
        p1 = P(H(range(10, 20)))
        p2 = P(H(range(100, 200, 10)))
        assert p2 == p1 * 10
        assert 10 * p1 == p2

    def test_op_truediv_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_truediv_d3n = d2 / d3n
        d3n_truediv_d2 = d3n / d2
        assert p_d2 / p_d3n == d2_truediv_d3n
        assert p_d2 / d3n == d2_truediv_d3n
        assert d2 / p_d3n == d2_truediv_d3n  # H / P
        assert p_d3n / p_d2 == d3n_truediv_d2
        assert p_d3n / d2 == d3n_truediv_d2
        assert d3n / p_d2 == d3n_truediv_d2  # H / P
        assert p_d2 / p_d3n != p_d3n / p_d2

    def test_op_truediv_num(self) -> None:
        p_d10 = P(10)
        p1 = P(H(range(100, 0, -10)))
        # Integer results only, even with truediv
        assert p_d10 == p1 / 10  # noqa: RUF069
        lcm_of_1_to_10 = 2 * 2 * 2 * 3 * 3 * 5 * 7
        assert lcm_of_1_to_10 / p_d10 == H(
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

    def test_op_floordiv_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 // P() == P()
        assert P() // p_d2 == P()
        assert P() // P() == P()

    def test_op_floordiv_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_floordiv_d3n = d2 // d3n
        d3n_floordiv_d2 = d3n // d2
        assert p_d2 // p_d3n == d2_floordiv_d3n
        assert p_d2 // d3n == d2_floordiv_d3n
        assert d2 // p_d3n == d2_floordiv_d3n  # H // P
        assert p_d3n // p_d2 == d3n_floordiv_d2
        assert p_d3n // d2 == d3n_floordiv_d2
        assert d3n // p_d2 == d3n_floordiv_d2  # H // P
        assert p_d2 // p_d3n != p_d3n // p_d2

    def test_op_floordiv_num(self) -> None:
        p_d10 = P(10)
        p1 = P(H(range(10, 110, 10)))
        p2 = P(H((10, 5, 3, 2, 2, 1, 1, 1, 1, 1)))
        assert p_d10 == p1 // 10
        assert 100 // p1 == p2

    def test_op_mod_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 % P() == P()
        assert P() % p_d2 == P()
        assert P() % P() == P()

    def test_op_mod_h(self) -> None:
        d2 = H(2)
        d3n = H(-3)
        p_d2 = P(d2)
        p_d3n = P(d3n)
        d2_mod_d3n = d2 % d3n
        d3n_mod_d2 = d3n % d2
        assert p_d2 % p_d3n == d2_mod_d3n
        assert p_d2 % d3n == d2_mod_d3n
        assert d2 % p_d3n == d2_mod_d3n  # H % P
        assert p_d3n % p_d2 == d3n_mod_d2
        assert p_d3n % d2 == d3n_mod_d2
        assert d3n % p_d2 == d3n_mod_d2  # H % P
        assert p_d2 % p_d3n != p_d3n % p_d2

    def test_op_mod_num(self) -> None:
        p_d10 = P(10)
        assert p_d10 % 5 == H((1, 2, 3, 4, 0, 1, 2, 3, 4, 0))
        assert 5 % p_d10 == H((0, 1, 2, 1, 0, 5, 5, 5, 5, 5))

    def test_op_pow_empty(self) -> None:
        p_d2 = P(2)
        assert p_d2 ** P() == P()
        assert P() ** p_d2 == P()
        assert P() ** P() == P()

    def test_op_pow_h(self) -> None:
        d2 = H(2)
        d3 = H(3)
        p_d2 = P(d2)
        p_d3 = P(d3)
        d2_pow_d3 = d2**d3
        d3_pow_d2 = d3**d2
        assert p_d2**p_d3 == d2_pow_d3
        assert p_d2**d3 == d2_pow_d3
        assert d2**p_d3 == d2_pow_d3  # H ** P
        assert p_d3**p_d2 == d3_pow_d2
        assert p_d3**d2 == d3_pow_d2
        assert d3**p_d2 == d3_pow_d2  # H ** P
        assert p_d2**p_d3 != p_d3**p_d2

    def test_op_pow_num(self) -> None:
        p_d5 = P(5)
        assert p_d5**2 == H((1, 4, 9, 16, 25))
        assert 2**p_d5 == H((2, 4, 8, 16, 32))
        assert p_d5**-1 == H((1, 1 / 2, 1 / 3, 1 / 4, 1 / 5))
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


class TestPTotal:
    def test_homogeneous(self) -> None:
        assert P(6, 6).total == 36

    def test_heterogeneous(self) -> None:
        assert P(4, 6).total == 24

    def test_empty(self) -> None:
        assert P().total == 1  # empty product

    def test_memoized(self) -> None:
        p = P(4, 6, 8)
        assert p.total == 192
        assert p.total is p._total  # noqa: SLF001


class TestPApply:
    def test_scalar_empty(self) -> None:
        assert P().apply(operator.add, 1) == P()
        assert P(H({})).apply(operator.add, 1) == P(H({}))

    def test_scalar_basic(self) -> None:
        assert P(6).apply(operator.pow, 2) == P(
            H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1})
        )

    def test_scalar_collision(self) -> None:
        assert P(H({1: 2, 2: 3, 3: 1})).apply(operator.mod, 2) == P(H({1: 3, 0: 3}))
        assert P(6).apply(operator.ge, 3) == P(H({False: 2, True: 4}))

    def test_h_empty(self) -> None:
        assert P(H({})).apply(operator.add, H(1)) == P(H({}))
        assert P(1).apply(operator.add, H({})) == P(H({}))

    def test_h_basic(self) -> None:
        assert P(H({10: 1, 20: 1})).apply(operator.sub, H({1: 1, 2: 1})) == P(
            H({9: 1, 19: 1, 8: 1, 18: 1})
        )

    def test_h_collision(self) -> None:
        # (1+2)=3 and (2+1)=3 collide; (1+1)=2, (2+2)=4
        assert P(2).apply(operator.add, H(2)) == P(H({2: 1, 3: 2, 4: 1}))

    def test_group_by_application_of_func(self) -> None:
        class IncrementAndReturnEveryCall:
            def __init__(self) -> None:
                self._count = 0

            def __call__(self, _: int) -> int:
                self._count += 1
                return self._count

        func = IncrementAndReturnEveryCall()
        assert P(3 @ P(4), 2 @ P(6), 8).apply(func) == P(
            3 @ P(H({1: 1, 2: 1, 3: 1, 4: 1})),
            2 @ P(H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})),
            H({11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1}),
        )
        func = IncrementAndReturnEveryCall()
        assert P(4, 4, 4, 6, 6, 8).apply(func, apply_to_each=True) == P(
            H({1: 1, 2: 1, 3: 1, 4: 1}),
            H({5: 1, 6: 1, 7: 1, 8: 1}),
            H({9: 1, 10: 1, 11: 1, 12: 1}),
            H({13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1}),
            H({19: 1, 20: 1, 21: 1, 22: 1, 23: 1, 24: 1}),
            H({25: 1, 26: 1, 27: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1}),
        )


class TestPH:
    def test_no_args_flattens_empty_pool(self) -> None:
        assert P().h() == H({})

    def test_no_args_flattens(self) -> None:
        assert (2 @ P(6)).h() == H(6) + H(6)

    def test_no_args_flattens_symbol(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d6x = H(6) * x
        assert (2 @ P(d6x)).h() == 2 @ d6x

    def test_no_args_weird_single(
        self,
    ) -> None:
        h = H({_NoCompare("oh-01"): 1, _NoCompare("oh-02"): 2})
        p_weird = P(h)
        assert p_weird.h() == h

    def test_no_args_weird_multiple_raises(
        self,
    ) -> None:
        p_weird = 2 @ P(
            H({_NoCompare("oh-01"): 1, _NoCompare("oh-02"): 2}),
            H({_NoCompare("oh-03"): 3, _NoCompare("oh-04"): 4}),
        )
        with (  # noqa: PT012
            pytest.raises(TypeError, match=r"\bunsupported operand\b"),
            warnings.catch_warnings(record=True),
        ):
            warnings.simplefilter("always", category=_ConvolveFallbackWarning)
            p_weird.h()

    def test_which_selects_all_shortcuts(self) -> None:
        class MockableP(P):
            pass

        p = MockableP(2 @ P(H({1: 1, 2: 2}), H({3: 1, 4: 1})))
        with patch.object(
            p, "rolls_with_counts", side_effect=p.rolls_with_counts
        ) as mock:
            assert p.h(slice(None)) == p.h()
            mock.assert_not_called()

    def test_which_selects_all_exactly_n_times_still_shortcuts(self) -> None:
        class MockableP(P):
            pass

        p = MockableP(2 @ P(H({1: 1, 2: 2}), H({3: 1, 4: 1})))
        with patch.object(
            p, "rolls_with_counts", side_effect=p.rolls_with_counts
        ) as mock:
            assert p.h(slice(None), slice(None), slice(None)) == 3 * p.h()
            mock.assert_not_called()

    def test_which_selects_all_exactly_n_times_still_shortcuts_with_operation_aware_outcomes(
        self,
    ) -> None:
        class MockableP(P):
            pass

        for p in (
            MockableP(2 @ P(H({"one": 1, "two": 2}), H({"three": 1, "four": 1}))),
            *(
                MockableP(2 @ H(o_type(i) for i in range(10)))
                for o_type in _OUTCOME_TYPES
            ),
        ):
            with patch.object(
                p, "rolls_with_counts", side_effect=p.rolls_with_counts
            ) as mock:
                p_h = p.h(slice(None), slice(None), slice(None))
                assert p_h == 3 * p.h()
                assert type(next(iter(p_h.outcomes()))) is type(
                    next(iter(p[0].outcomes()))
                )
                mock.assert_not_called()

    def test_which_single_index_weird_outcomes(
        self,
    ) -> None:
        p = 2 @ P(H({1: 1, 2: 2}), H({3: 3, 4: 4}))
        p_weird = 2 @ P(
            H({_NoCompare("oh-01"): 1, _NoCompare("oh-02"): 2}),
            H({_NoCompare("oh-03"): 3, _NoCompare("oh-04"): 4}),
        )
        p_h_lo = p.h(0)
        assert repr(p_weird.h(0)) == repr(
            H({_NoCompare("oh-01"): p_h_lo[1], _NoCompare("oh-02"): p_h_lo[2]})
        )
        p_h_hi = p.h(-1)
        assert repr(p_weird.h(-1)) == repr(
            H({_NoCompare("oh-03"): p_h_hi[3], _NoCompare("oh-04"): p_h_hi[4]})
        )
        for i in range(len(p_weird)):
            assert type(next(iter(p_weird.h(i).outcomes()))) is type(
                next(iter(p_weird[i].outcomes()))
            )

    def test_which_selects_all_exactly_n_times_falls_back_with_weird_outcomes(
        self,
    ) -> None:
        class MockableP(P):
            pass

        p = MockableP(
            2
            @ P(
                H({_NoCompareCanOnlyAdd("one"): 1, _NoCompareCanOnlyAdd("two"): 2}),
                H({_NoCompareCanOnlyAdd("three"): 1, _NoCompareCanOnlyAdd("four"): 1}),
            )
        )
        with patch.object(
            p, "rolls_with_counts", side_effect=p.rolls_with_counts
        ) as mock:
            p_h = p.h(slice(None), slice(None), slice(None))
            assert type(next(iter(p_h.outcomes()))) is type(next(iter(p[0].outcomes())))
            mock.assert_called()

    def test_which_equivalence_with_rwc(self) -> None:
        # h(*which) must agree with manually accumulating rolls_with_counts(*which)
        p = 3 @ P(H({1: 1, 2: 2, 3: 1}), H({3: 1, 4: 1, 5: 1}))
        for which in (
            (-1,),
            (0,),
            (0, -1),
            (slice(1, 2),),
            (slice(None),),
        ):
            from_h = p.h(*which)
            from_rwc = H.from_counts(
                (sum(roll), count) for roll, count in p.rolls_with_counts(*which)
            )
            assert from_h == from_rwc, f"mismatch for which={which}"

    def test_which_index_highest(self) -> None:
        # Highest of 2d6 — known distribution
        assert (2 @ P(6)).h(-1) == H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})

    def test_which_index_lowest(self) -> None:
        # Lowest of 2d6 — mirror of highest
        assert (2 @ P(6)).h(0) == H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})

    def test_h_which_homogeneous(self) -> None:
        # Use the brute-force mechanism to validate our harder-to-understand
        # implementation
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        for which in (
            (slice(2, 3),),
            (slice(1, 2),),
            (slice(0, 1),),
            (slice(2),),
            (slice(-2, None),),
            (0, 1, 1, 0),
            (-2, -1, -1, -2),
        ):
            from_brute = H.from_counts(
                (sum(roll), count)
                for roll, count in _rwc_heterogeneous_brute_force_combinations(
                    tuple(p_4df), *which
                )
            )
            assert p_4df.h(*which) == from_brute, f"mismatch for which={which}"

    def test_which_heterogeneous(self) -> None:
        p_d3 = P(3)
        p_d3n = -p_d3
        p_d4 = P(4)
        p_d4n = -p_d4
        p_4d3_4d4 = 2 @ P(p_d3, p_d3n, p_d4n, p_d4)
        for which in (
            (slice(0, 0),),
            (slice(-1, None),),
            (slice(-2, None),),
            (slice(2),),
            (slice(1),),
            (0, 1, 1, 0),
            (-2, -1, -1, -2),
        ):
            from_brute = H.from_counts(
                (sum(roll), count)
                for roll, count in _rwc_heterogeneous_brute_force_combinations(
                    tuple(p_4d3_4d4), *which
                )
            )
            assert p_4d3_4d4.h(*which) == from_brute, f"mismatch for which={which}"

    def test_which_all_exactly_twice(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        from_rwc = H.from_counts(
            (sum(roll) * 2, count) for roll, count in p_4df.rolls_with_counts()
        )
        assert p_4df.h(slice(None), slice(None)) == from_rwc

    def test_which_out_of_range_index_raises(self) -> None:
        # Out-of-bounds index raises (analogous to [][0], [][-1])
        with pytest.raises(IndexError):
            P().h(0)
        with pytest.raises(IndexError):
            P().h(-1)

    def test_which_out_of_range_slice_empty(self) -> None:
        # Slice that selects nothing yields no rolls (analogous to [][0:1])
        assert P().h(slice(0, 1)) == H({})
        assert P().h(slice(-2, -1)) == H({})


class TestPRoll:
    def test_roll_empty(self) -> None:
        assert P().roll() == ()

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


class TestPRollsWithCounts:
    def test_no_args_empty_pool(self) -> None:
        assert list(P().rolls_with_counts()) == []

    def test_no_arg_equivalent_vs_brute_force(self) -> None:
        for p in (2 @ P(6), P(3 @ P(2), 2 @ P(3))):
            from_rwc: Counter[RollT[int]] = Counter()
            for roll, count in p.rolls_with_counts():
                from_rwc[roll] += count
            expected: Counter[RollT[int]] = Counter()
            for roll, count in _rwc_heterogeneous_brute_force_combinations(tuple(p)):
                expected[roll] += count
            assert from_rwc == expected, f"mismatch for p={p}"

    def test_total_count(self) -> None:
        for p in (2 @ P(6), P(4, 6)):
            total = sum(c for _, c in p.rolls_with_counts())
            assert total == p.total, f"mismatch for p={p}"

    def test_which_selects_all_via_non_overlapping_slices(self) -> None:
        p = 2 @ P(H((-1, 0, 1)))
        default = sorted(p.rolls_with_counts())
        split = sorted(p.rolls_with_counts(slice(None, 1), slice(1, None)))
        assert default == split

    def test_which_index_highest(self) -> None:
        # highest of 3d6 — known distribution
        highs = H.from_counts(
            (roll[0], count) for roll, count in (3 @ P(6)).rolls_with_counts(-1)
        )
        assert highs == {6: 91, 5: 61, 4: 37, 3: 19, 2: 7, 1: 1}

    def test_which_index_lowest(self) -> None:
        lows = H.from_counts(
            (roll[0], count) for roll, count in (3 @ P(6)).rolls_with_counts(0)
        )
        assert lows == {1: 91, 2: 61, 3: 37, 4: 19, 5: 7, 6: 1}

    def test_which_index_lowest_and_highest(self) -> None:
        p = 3 @ P(6)
        lo_hi = sorted(p.rolls_with_counts(0, -1))
        expected = sorted(((r[0], r[-1]), c) for r, c in p.rolls_with_counts())
        assert lo_hi == expected

    def test_simple_known_output(self) -> None:
        assert sorted(P(2, 2).rolls_with_counts()) == [
            ((1, 1), 1),
            ((1, 2), 2),
            ((2, 2), 1),
        ]

    def test_may_yield_rolls_more_than_once(self) -> None:
        assert sorted(P(H(2), H(3)).rolls_with_counts()) == [
            ((1, 1), 1),
            ((1, 2), 1),
            # Originated as ((2, 1), 1), but outcomes get sorted in each roll
            ((1, 2), 1),
            ((1, 3), 1),
            ((2, 2), 1),
            ((2, 3), 1),
        ]

    def test_which_out_of_range_index_raises(self) -> None:
        # Out-of-bounds index raises (analogous to [][0])
        with pytest.raises(IndexError):
            list(P().rolls_with_counts(0))
        with pytest.raises(IndexError):
            list(P(6).rolls_with_counts(6))

    def test_which_out_of_range_slice_empty(self) -> None:
        # Slice that selects nothing yields no rolls (analogous to [][0:1])
        assert list(P().rolls_with_counts(slice(None, None, None))) == []
        assert list(P(6).rolls_with_counts(slice(6, 7))) == []

    def test_which_index_each_twice(self) -> None:
        # Selecting all elements twice doubles each roll's count
        p = 2 @ P(6)
        doubled_keys = dict(p.rolls_with_counts(0, 0, 1, 1))
        # Each roll (a, b) becomes (a, a, b, b) with same count
        expected = {(r[0], r[0], r[1], r[1]): c for r, c in p.rolls_with_counts()}
        assert doubled_keys == expected

    def test_homogeneous_vs_known_correct(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        for which in (
            slice(None),
            slice(0, 4),
            slice(-4, None),
        ):
            using_partial_selection = _rwc_validation_helper(p_4df, which)
            assert using_partial_selection.call_args_list == [
                call(4, H({-1: 1, 0: 1, 1: 1}), k=4)
            ]
        # 1 outcome from left (each distinct position)
        using_partial_selection = _rwc_validation_helper(p_4df, slice(0, 1))
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=1, fill=0)
        ]
        using_partial_selection = _rwc_validation_helper(p_4df, slice(1, 2))
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=2, fill=0)
        ]
        using_partial_selection = _rwc_validation_helper(p_4df, slice(2, 3))
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=-2, fill=0)
        ]
        using_partial_selection = _rwc_validation_helper(p_4df, slice(3, 4))
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=-1, fill=0)
        ]
        # No outcomes — early-exit before _rwc_homogeneous_n_h_using_partial_selection
        using_partial_selection = _rwc_validation_helper(p_4df, slice(0, 0))
        assert using_partial_selection.call_args_list == []
        # 2 outcomes from right
        using_partial_selection = _rwc_validation_helper(p_4df, slice(2, 4))
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=-2, fill=0)
        ]
        # Non-contiguous
        using_partial_selection = _rwc_validation_helper(p_4df, 1, 3)
        assert using_partial_selection.call_args_list == [
            call(4, H({-1: 1, 0: 1, 1: 1}), k=-3, fill=0)
        ]
        # Off the deep end — early-exit before _rwc_homogeneous_n_h_using_partial_selection
        using_partial_selection = _rwc_validation_helper(p_4df, slice(5, 7))
        assert using_partial_selection.call_args_list == []
        using_partial_selection = _rwc_validation_helper(p_4df, slice(-7, -5))
        assert using_partial_selection.call_args_list == []

    def test_heterogeneous_vs_known_correct(self) -> None:
        p_d3 = P(3)
        p_d4n = P(-4)
        p_3d3_4d4n = P(3 @ p_d3, 4 @ p_d4n)
        for which in (
            # All outcomes
            slice(None),
            # 4 lowest or highest outcomes
            slice(4),
            slice(-4, None),
            # Middle bit
            slice(2, 4),
        ):
            using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, which)
            using_partial_selection.assert_has_calls(
                [
                    call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 4),
                    call(3, H({1: 1, 2: 1, 3: 1}), 3),
                ]
            )
        # 3 outcomes from left
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(3))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 3),
            call(3, H({1: 1, 2: 1, 3: 1}), 3),
        ]
        # 3 outcomes from right
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(-3, None))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), -3),
            call(3, H({1: 1, 2: 1, 3: 1}), 3),
        ]
        # 2 outcomes from left
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(2))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 2),
            call(3, H({1: 1, 2: 1, 3: 1}), 2),
        ]
        # 2 outcomes from right
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(-2, None))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), -2),
            call(3, H({1: 1, 2: 1, 3: 1}), -2),
        ]
        # 1 outcome from left
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(1))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 1),
            call(3, H({1: 1, 2: 1, 3: 1}), 1),
        ]
        # 1 outcome from right
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(-1, None))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), -1),
            call(3, H({1: 1, 2: 1, 3: 1}), -1),
        ]
        # No outcomes — early-exit before _rwc_homogeneous_n_h_using_partial_selection
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(0, 0))
        assert using_partial_selection.call_args_list == []
        # Non-contiguous
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, 1, 3)
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 4),
            call(3, H({1: 1, 2: 1, 3: 1}), 3),
        ]
        # Near the combined-roll ends but outside any sub-pool
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(5, 7))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), -2),
            call(3, H({1: 1, 2: 1, 3: 1}), -2),
        ]
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(-7, -5))
        assert using_partial_selection.call_args_list == [
            call(4, H({-4: 1, -3: 1, -2: 1, -1: 1}), 2),
            call(3, H({1: 1, 2: 1, 3: 1}), 2),
        ]
        # Off the deep end — early-exit before _rwc_homogeneous_n_h_using_partial_selection
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(7, 9))
        assert using_partial_selection.call_args_list == []
        using_partial_selection = _rwc_validation_helper(p_3d3_4d4n, slice(-9, -7))
        assert using_partial_selection.call_args_list == []


class TestFillSentinels:
    def test_min_fill_hash(self) -> None:
        assert {_MIN_FILL: 1}[_MIN_FILL] == 1

    def test_min_fill_repr(self) -> None:
        assert repr(_MIN_FILL) == "_MinFill()"

    def test_min_fill_lt(self) -> None:
        assert _MIN_FILL < 0
        assert not (_MIN_FILL < _MIN_FILL)

    def test_min_fill_le(self) -> None:
        assert _MIN_FILL <= 0
        assert _MIN_FILL <= _MIN_FILL

    def test_min_fill_ge(self) -> None:
        assert not (_MIN_FILL >= 0)
        assert _MIN_FILL >= _MIN_FILL

    def test_min_fill_eq(self) -> None:
        assert _MIN_FILL == _MIN_FILL
        assert _MIN_FILL != 0

    def test_min_fill_gt(self) -> None:
        assert not (_MIN_FILL > 0)
        assert not (_MIN_FILL > _MIN_FILL)

    def test_max_fill_hash(self) -> None:
        assert {_MAX_FILL: 1}[_MAX_FILL] == 1

    def test_max_fill_repr(self) -> None:
        assert repr(_MAX_FILL) == "_MaxFill()"

    def test_max_fill_lt(self) -> None:
        assert not (_MAX_FILL < 0)
        assert not (_MAX_FILL < _MAX_FILL)

    def test_max_fill_le(self) -> None:
        assert not (_MAX_FILL <= 0)
        assert _MAX_FILL <= _MAX_FILL

    def test_max_fill_eq(self) -> None:
        assert _MAX_FILL == _MAX_FILL
        assert _MAX_FILL != 0

    def test_max_fill_ge(self) -> None:
        assert _MAX_FILL >= 0
        assert _MAX_FILL >= _MAX_FILL

    def test_max_fill_gt(self) -> None:
        assert _MAX_FILL > 0
        assert not (_MAX_FILL > _MAX_FILL)


# ---- Helpers -------------------------------------------------------------------------


def test_analyze_selection() -> None:
    # Prefix: only the first lo positions selected
    assert _analyze_selection(6, (0,)) == _SelectionPrefix(max_index=1)
    assert _analyze_selection(6, (0, 1, 0, 0, 1)) == _SelectionPrefix(max_index=2)
    assert _analyze_selection(6, (0, 1, 0, 0, 1, 4)) == _SelectionPrefix(max_index=5)
    assert _analyze_selection(6, (2,)) == _SelectionPrefix(max_index=3)
    assert _analyze_selection(6, (2, 3)) == _SelectionPrefix(max_index=4)
    assert _analyze_selection(6, (1, 2, 3)) == _SelectionPrefix(max_index=4)
    assert _analyze_selection(6, (1, 3)) == _SelectionPrefix(max_index=4)
    assert _analyze_selection(5, (2,)) == _SelectionPrefix(max_index=3)
    assert _analyze_selection(5, (1, 2)) == _SelectionPrefix(max_index=3)

    # Suffix: only the last hi positions selected
    assert _analyze_selection(6, (-1,)) == _SelectionSuffix(min_index=-1)
    assert _analyze_selection(6, (5, 1, 5, 5, 1, 4)) == _SelectionSuffix(min_index=-5)
    assert _analyze_selection(6, (3,)) == _SelectionSuffix(min_index=-3)
    assert _analyze_selection(6, (2, 3, 4)) == _SelectionSuffix(min_index=-4)
    assert _analyze_selection(6, (2, 4)) == _SelectionSuffix(min_index=-4)
    assert _analyze_selection(5, (2, 3)) == _SelectionSuffix(min_index=-3)

    # Uniform: every position selected the same number of times
    assert _analyze_selection(6, tuple(range(6))) == _SelectionUniform(times=1)
    assert _analyze_selection(6, tuple(range(0, -6, -1))) == _SelectionUniform(times=1)
    assert _analyze_selection(
        6, tuple(range(6)) + tuple(range(0, -6, -1))
    ) == _SelectionUniform(times=2)
    assert _analyze_selection(6, (slice(None),)) == _SelectionUniform(times=1)
    assert _analyze_selection(
        6, (slice(0, None), slice(-6, None))
    ) == _SelectionUniform(times=2)

    # Extremes: lo lowest + hi highest, with at least one unselected interior position
    assert _analyze_selection(6, (0, -1)) == _SelectionExtremes(lo=1, hi=1)
    assert _analyze_selection(6, (-1, 0)) == _SelectionExtremes(
        lo=1, hi=1
    )  # order-independent
    assert _analyze_selection(6, (0, 1, -1)) == _SelectionExtremes(lo=2, hi=1)
    assert _analyze_selection(6, (0, -2, -1)) == _SelectionExtremes(lo=1, hi=2)
    assert _analyze_selection(6, (0, 1, -2, -1)) == _SelectionExtremes(lo=2, hi=2)
    assert _analyze_selection(3, (0, 2)) == _SelectionExtremes(
        lo=1, hi=1
    )  # n=3, gap of 1

    # Arbitrary: non-prefix/suffix/extremes selections return None
    assert (
        _analyze_selection(6, (0, 2, -1)) is None
    )  # gap on both sides but lo-side isn't contiguous
    assert _analyze_selection(6, tuple(range(6)) + tuple(range(3))) is None

    # Empty: no positions selected
    assert _analyze_selection(0, ()) == _SelectionEmpty()
    assert _analyze_selection(6, ()) == _SelectionEmpty()
    assert _analyze_selection(6, (slice(0, 0),)) == _SelectionEmpty()

    with pytest.raises(IndexError):
        _ = _analyze_selection(0, (1,))


def test_rwc_heterogeneous_extremes_matches_brute_force() -> None:
    r"""Verify the inclusion-exclusion result matches Cartesian-product enumeration."""
    cases = [
        # (list-of-dice, description)  # noqa: ERA001
        ([H(4), H(6)], "d4+d6"),
        ([H(4), H(4), H(6)], "2d4+d6"),
        ([H(4), H(6), H(8)], "d4+d6+d8"),
        ([H(4), H(6), H(8), H(10), H(12), H(20)], "d4..d20"),
    ]
    for dice, desc in cases:
        brute: Counter[RollT[int]] = Counter()
        for roll, count in _rwc_heterogeneous_brute_force_combinations(dice, 0, -1):
            brute[roll] += count
        optimised: Counter[RollT[int]] = Counter()
        groups = [(h, 1) for h in dice]
        for roll, count in _rwc_heterogeneous_extremes(groups, 1, 1):
            optimised[roll] += count
        assert optimised == brute, f"mismatch for {desc}"


def test_rwc_heterogeneous_extremes_via_h() -> None:
    r"""P.h(0, -1) on a heterogeneous pool agrees with the brute-force sum."""
    d4, d6, d8, d10, d12, d20 = (H(n) for n in (4, 6, 8, 10, 12, 20))
    p = P(d4, d6, d8, d10, d12, d20)
    from_brute = H.from_counts(
        (sum(roll), count)
        for roll, count in _rwc_heterogeneous_brute_force_combinations(list(p), 0, -1)
    )
    assert p.h(0, -1) == from_brute


def test_rwc_heterogeneous_extremes_natural_order() -> None:
    r"""P.h(0, -1) on a heterogeneous pool agrees with the brute-force sum."""
    sympy = pytest.importorskip("sympy", reason="requires sympy")
    x = sympy.symbols("x")
    d6x = H(6) + x
    d8x = H(8) + x
    p = P(d6x, d6x, d8x)
    from_brute = H.from_counts(
        (sum(roll), count)
        for roll, count in _rwc_heterogeneous_brute_force_combinations(list(p), 0, -1)
    )
    assert p.h(0, -1) == from_brute


def test_first_principles() -> None:
    for n, h, which in (
        (3, H(6), ()),
        (3, H((2, 3, 3, 4, 4, 5)), ()),
        (6, H(4), ()),
        (3, H({i: i for i in range(1, 11)}), ()),
        (3, H({i: 11 - i for i in range(1, 11)}), ()),
        (3, H(6), (0,)),
        (3, H(6), (1,)),
        (3, H(6), (-1,)),
        (4, H((-1, 0, 1)), (0, 2)),
        (4, H((-1, 0, 1)), (1, 3)),
    ):
        brute_force: Counter[RollT[int]] = Counter()
        multinomial: Counter[RollT[int]] = Counter()
        for roll, count in _rwc_heterogeneous_brute_force_combinations([h] * n, *which):
            brute_force[roll] += count
        for roll, count in _rwc_homogeneous_n_h_using_multinomial_coefficient(
            n, h, *which
        ):
            multinomial[roll] += count
        assert brute_force == multinomial


# ---- Helpers -------------------------------------------------------------------------


class _NoCompareCanOnlyAdd(_NoCompare):
    def __add__(self, other: Any) -> "_NoCompareCanOnlyAdd":  # noqa: ANN401
        return _NoCompareCanOnlyAdd(f"{self.val}+{other}")


def _roll_which(roll: RollT[_T], *keys: _GetItemT) -> RollT[_T]:
    if not keys:
        keys = (slice(None),)

    def _roll_selection_from_key(key: _GetItemT) -> RollT[_T]:
        if isinstance(key, slice):
            return tuple(roll[key])
        else:
            return (roll[key],)

    return tuple(chain(*(_roll_selection_from_key(key) for key in keys)))


def _rwc_heterogeneous_brute_force_combinations(
    hs: Sequence[H[_T]],
    *keys: _GetItemT,
) -> Iterator[RollCountT[_T]]:
    r"""Naive Cartesian-product enumeration correct for any count magnitude."""
    for rolls in iproduct(*(h.items() for h in hs)):
        outcomes, counts = tuple(zip(*rolls, strict=True))
        try:
            roll: RollT[_T] = tuple(sorted(outcomes))
        except TypeError:
            roll = tuple(sorted(outcomes, key=natural_key))  # pyrefly: ignore[bad-argument-type]
        count = prod(counts)
        roll_selection = _roll_which(roll, *keys)
        if roll_selection:
            yield roll_selection, count


def _rwc_homogeneous_n_h_using_multinomial_coefficient(
    n: int,
    h: H[_T],
    *keys: _GetItemT,
) -> Iterator[RollCountT[_T]]:
    r"""Independent reference implementation using multinomial coefficients."""
    multinomial_coefficient_numerator = factorial(n)
    for sorted_outcomes_for_roll in combinations_with_replacement(h, n):
        count_scalar = prod(h[outcome] for outcome in sorted_outcomes_for_roll)
        multinomial_coefficient_denominator = prod(
            factorial(sum(1 for _ in g)) for _, g in groupby(sorted_outcomes_for_roll)
        )
        roll_selection = _roll_which(sorted_outcomes_for_roll, *keys)
        if roll_selection:
            yield (
                roll_selection,
                count_scalar
                * multinomial_coefficient_numerator
                // multinomial_coefficient_denominator,
            )


def _rwc_validation_helper(p: P[_T], *which: _GetItemT) -> Mock:
    r"""
    Validate rolls_with_counts against brute force and return a mock used to track would-be calls to _rwc_homogeneous_n_h_using_partial_selection.
    """
    known_counts: Counter[RollT[_T]] = Counter()
    test_counts: Counter[RollT[_T]] = Counter()
    for roll, count in _rwc_heterogeneous_brute_force_combinations(tuple(p), *which):
        known_counts[roll] += count
    with patch(
        "dyce.p._rwc_homogeneous_n_h_using_partial_selection",
        side_effect=_rwc_homogeneous_n_h_using_partial_selection,
    ) as using_partial_selection:
        for roll, count in p.rolls_with_counts(*which):
            test_counts[roll] += count
    assert test_counts == known_counts
    return using_partial_selection

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
from collections.abc import Iterable
from decimal import Decimal
from fractions import Fraction
from typing import Any, TypeVar
from unittest.mock import patch

import pytest

from dyce import H, P
from dyce.h import _ConvolveFallbackWarning
from dyce.p import (
    RollT,
    _rwc_homogeneous_one_end,
    _WhichHSurveyor,
    _WhichRollSurveyor,
)
from dyce.types import BeartypeCallHintViolation, GetItemT

from ._helpers import (
    SAMPLE_OUTCOME_TYPES,
    NoCompare,
    NoCompareCanOnlyAdd,
    enumerate_weighted_unsorted_rolls_multinomial_coefficient,
    sort_and_select_from_rolls,
)

__all__ = ()

_T = TypeVar("_T")


class _PatchableP(P):
    pass


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
            H({NoCompare(str(i**2 * (-1) ** i) + "abc" + str(-i)) for i in range(n)})
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
            "H({NoCompare('0abc0'): 1, NoCompare('4abc-2'): 1, NoCompare('16abc-4'): 1, NoCompare('-1abc-1'): 1, NoCompare('-9abc-3'): 1}), "
            "H({NoCompare('0abc0'): 1, NoCompare('4abc-2'): 1, NoCompare('-1abc-1'): 1, NoCompare('-9abc-3'): 1}), "
            "H({NoCompare('0abc0'): 1, NoCompare('4abc-2'): 1, NoCompare('-1abc-1'): 1}), "
            "H({NoCompare('0abc0'): 1, NoCompare('-1abc-1'): 1}), "
            "H({NoCompare('0abc0'): 1})]"
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
        assert hash(p) == p._hash  # ruff: ignore[private-member-access]

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

    def test_getitem(self) -> None:
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

    def test_getitem_heterogeneous_index_negative(self) -> None:
        p = P(7 @ P(4), 11 @ P(6), 13 @ P(8), 17 @ P(10))
        for i in range(-1, -1 - 17, -1):
            assert p[i] == H(10)
        for i in range(-1 - 17, -1 - 17 - 13, -1):
            assert p[i] == H(8)
        for i in range(-1 - 17 - 13, -1 - 17 - 13 - 11, -1):
            assert p[i] == H(6)
        for i in range(-1 - 17 - 13 - 11, -1 - 17 - 13 - 11 - 7, -1):
            assert p[i] == H(4)
        with pytest.raises(IndexError):
            p[-1 - 17 - 13 - 11 - 7]

    def test_getitem_heterogeneous_index_positive(self) -> None:
        p = P(7 @ P(4), 11 @ P(6), 13 @ P(8), 17 @ P(10))
        for i in range(7):
            assert p[i] == H(4)
        for i in range(7, 7 + 11):
            assert p[i] == H(6)
        for i in range(7 + 11, 7 + 11 + 13):
            assert p[i] == H(8)
        for i in range(7 + 11 + 13, 7 + 11 + 13 + 17):
            assert p[i] == H(10)
        with pytest.raises(IndexError):
            p[7 + 11 + 13 + 17]

    def test_getitem_heterogeneous_slice_negative(self) -> None:
        p = P(7 @ P(4), 11 @ P(6), 13 @ P(8), 17 @ P(10))
        assert p[-17:] == 17 @ P(10)
        assert p[: -1 - 17 : -1] == 17 @ P(10)
        assert p[-17 - 3 : -17 + 3] == P(3 @ P(8), 3 @ P(10))
        assert p[-17 - 3 : -17 + 3 : 2] == P(2 @ P(8), P(10))
        assert p[-17 + 2 : -17 - 4 : -1] == P(3 @ P(8), 3 @ P(10))
        assert p[-17 + 2 : -17 - 4 : -2] == P(P(8), 2 @ P(10))
        assert p[-17 - 13 : -17] == 13 @ P(8)
        assert p[-1 - 17 : -1 - 17 - 13 : -1] == 13 @ P(8)
        assert p[-17 - 13 - 3 : -17 - 13 + 3] == P(3 @ P(6), 3 @ P(8))
        assert p[-17 - 13 - 3 : -17 - 13 + 3 : 2] == P(2 @ P(6), P(8))
        assert p[-17 - 13 + 2 : -17 - 13 - 4 : -1] == P(3 @ P(6), 3 @ P(8))
        assert p[-17 - 13 + 2 : -17 - 13 - 4 : -2] == P(P(6), 2 @ P(8))
        assert p[-17 - 13 - 11 : -17 - 13] == 11 @ P(6)
        assert p[-1 - 17 - 13 : -1 - 17 - 13 - 11 : -1] == 11 @ P(6)
        assert p[-17 - 13 - 11 - 3 : -17 - 13 - 11 + 3] == P(3 @ P(4), 3 @ P(6))
        assert p[-17 - 13 - 11 - 3 : -17 - 13 - 11 + 3 : 2] == P(2 @ P(4), P(6))
        assert p[-17 - 13 - 11 + 2 : -17 - 13 - 11 - 4 : -1] == P(3 @ P(4), 3 @ P(6))
        assert p[-17 - 13 - 11 + 2 : -17 - 13 - 11 - 4 : -2] == P(P(4), 2 @ P(6))
        assert p[: -17 - 13 - 11] == 7 @ P(4)
        assert p[-1 - 17 - 13 - 11 :: -1] == 7 @ P(4)

    def test_getitem_heterogeneous_slice_positive(self) -> None:
        p = P(7 @ P(4), 11 @ P(6), 13 @ P(8), 17 @ P(10))
        assert p[:7] == 7 @ P(4)
        assert p[7 - 1 :: -1] == 7 @ P(4)
        assert p[7 - 3 : 7 + 3] == P(3 @ P(4), 3 @ P(6))
        assert p[7 - 3 : 7 + 3 : 2] == P(2 @ P(4), P(6))
        assert p[7 + 2 : 7 - 4 : -1] == P(3 @ P(4), 3 @ P(6))
        assert p[7 + 2 : 7 - 4 : -2] == P(P(4), 2 @ P(6))
        assert p[7 : 7 + 11] == 11 @ P(6)
        assert p[7 + 11 - 1 : 7 - 1 : -1] == 11 @ P(6)
        assert p[7 + 11 - 3 : 7 + 11 + 3] == P(3 @ P(6), 3 @ P(8))
        assert p[7 + 11 - 3 : 7 + 11 + 3 : 2] == P(2 @ P(6), P(8))
        assert p[7 + 11 + 2 : 7 + 11 - 4 : -1] == P(3 @ P(6), 3 @ P(8))
        assert p[7 + 11 + 2 : 7 + 11 - 4 : -2] == P(P(6), 2 @ P(8))
        assert p[7 + 11 : 7 + 11 + 13] == 13 @ P(8)
        assert p[7 + 11 + 13 - 1 : 7 + 11 - 1 : -1] == 13 @ P(8)
        assert p[7 + 11 + 13 - 3 : 7 + 11 + 13 + 3] == P(3 @ P(8), 3 @ P(10))
        assert p[7 + 11 + 13 - 3 : 7 + 11 + 13 + 3 : 2] == P(2 @ P(8), P(10))
        assert p[7 + 11 + 13 + 2 : 7 + 11 + 13 - 4 : -1] == P(3 @ P(8), 3 @ P(10))
        assert p[7 + 11 + 13 + 2 : 7 + 11 + 13 - 4 : -2] == P(P(8), 2 @ P(10))
        assert p[7 + 11 + 13 :] == 17 @ P(10)
        assert p[: 7 + 11 + 13 - 1 : -1] == 17 @ P(10)

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

    def test_matmul_composition(self) -> None:
        assert 2 @ (2 @ P(6)) == 4 @ P(6)

    def test_matmul_negative_rhs(self) -> None:
        with pytest.raises(ValueError, match=r"\brequires non-negative operand\b"):
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
        assert d2 + p_d3n == d2_add_d3n  # H + P exercises _flatten_to_h
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
        assert p_d10 == p1 / 10  # ruff: ignore[float-equality-comparison]
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
        assert p.total is p._total  # ruff: ignore[private-member-access]


class TestPApplyEachH:
    def test_scalar_empty(self) -> None:
        assert P().apply_to_each_h(operator.add, 1) == P()
        assert P(H({})).apply_to_each_h(operator.add, 1) == P(H({}))

    def test_scalar_basic(self) -> None:
        assert P(6).apply_to_each_h(operator.pow, 2) == P(
            H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1})
        )

    def test_scalar_collision(self) -> None:
        assert P(H({1: 2, 2: 3, 3: 1})).apply_to_each_h(operator.mod, 2) == P(
            H({1: 3, 0: 3})
        )
        assert P(6).apply_to_each_h(operator.ge, 3) == P(H({False: 2, True: 4}))

    def test_h_empty(self) -> None:
        assert P(H({})).apply_to_each_h(operator.add, H(1)) == P(H({}))
        assert P(1).apply_to_each_h(operator.add, H({})) == P(H({}))

    def test_h_basic(self) -> None:
        assert P(H({10: 1, 20: 1})).apply_to_each_h(operator.sub, H({1: 1, 2: 1})) == P(
            H({9: 1, 19: 1, 8: 1, 18: 1})
        )

    def test_h_collision(self) -> None:
        # (1+2)=3 and (2+1)=3 collide; (1+1)=2, (2+2)=4
        assert P(2).apply_to_each_h(operator.add, H(2)) == P(H({2: 1, 3: 2, 4: 1}))

    def test_group_by_application_of_func(self) -> None:
        class IncrementAndReturnEveryCall:
            def __init__(self) -> None:
                self._count = 0

            def __call__(self, _: int) -> int:
                self._count += 1
                return self._count

        func = IncrementAndReturnEveryCall()
        assert P(3 @ P(4), 2 @ P(6), 8).apply_to_each_h(func) == P(
            3 @ P(H({1: 1, 2: 1, 3: 1, 4: 1})),
            2 @ P(H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})),
            H({11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1}),
        )
        func = IncrementAndReturnEveryCall()
        assert P(4, 4, 4, 6, 6, 8).apply_to_each_h(func, apply_to_each=True) == P(
            H({1: 1, 2: 1, 3: 1, 4: 1}),
            H({5: 1, 6: 1, 7: 1, 8: 1}),
            H({9: 1, 10: 1, 11: 1, 12: 1}),
            H({13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1}),
            H({19: 1, 20: 1, 21: 1, 22: 1, 23: 1, 24: 1}),
            H({25: 1, 26: 1, 27: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1}),
        )


class TestPApplyEachRoll:
    def test_sum(self) -> None:
        p = 3 @ P(6)
        assert p.h() == p.apply_to_each_roll(sum)

    def test_sum_which(self) -> None:
        p = 3 @ P(6)
        for m in range(len(p)):
            for n in range(m + 1, len(p) + 1):
                which = slice(m, n)
                assert p.h(which) == p.apply_to_each_roll(sum, which)

    def test_sum_which_multi(self) -> None:
        p = 4 @ P(6)
        for m in range(len(p)):
            for n in range(m + 1, len(p) + 1):
                which = slice(m, n)
                assert p.h(slice(None), which, slice(None)) == p.apply_to_each_roll(
                    sum, slice(None), which, slice(None)
                )
        assert p.h(slice(0, 0)) == p.apply_to_each_roll(sum, slice(0, 0))


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
        h = H({NoCompare("oh-01"): 1, NoCompare("oh-02"): 2})
        p_weird = P(h)
        assert p_weird.h() == h  # type: ignore[call-arg] # ty: ignore[no-matching-overload]

    def test_no_args_weird_multiple_raises(
        self,
    ) -> None:
        p_weird = 2 @ P(
            H({NoCompare("oh-01"): 1, NoCompare("oh-02"): 2}),
            H({NoCompare("oh-03"): 3, NoCompare("oh-04"): 4}),
        )
        with (  # ruff: ignore[pytest-raises-with-multiple-statements]
            pytest.raises(
                (TypeError, BeartypeCallHintViolation),
                match=r"\b(unsupported operand type|violates type hint)\b",
            ) as exc_info,
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter("always", category=_ConvolveFallbackWarning)
            p_weird.h()  # type: ignore[call-arg] # ty: ignore[no-matching-overload]

        # TODO(posita): # ruff: ignore[missing-todo-link] - Is this really the right
        # logic? It "works", but beartype kills the transgression before the warning is
        # emitted (i.e., the fallback path is taken).
        if exc_info.type is TypeError:
            assert len(w) == 1
            assert issubclass(w[0].category, _ConvolveFallbackWarning)

    def test_which_selects_all_exactly_n_times_with_operation_aware_outcomes(
        self,
    ) -> None:
        for p in (
            _PatchableP(
                2 @ P(H({("one",): 1, ("two",): 2}), H({("three",): 1, ("four",): 1}))
            ),
            *(
                _PatchableP(2 @ H(o_type(i) for i in range(10)))
                for o_type in SAMPLE_OUTCOME_TYPES
            ),
        ):
            p_h = p.h(slice(None), slice(None), slice(None))
            expected = H.from_counts(
                (
                    (
                        tuple(sorted(outcome))
                        if isinstance(outcome, Iterable)
                        else outcome
                    ),
                    count,
                )
                for outcome, count in (3 * p.h()).items()
            )
            assert p_h == expected
            assert type(next(iter(p_h.outcomes()))) is type(next(iter(p[0].outcomes())))

    def test_which_single_index_weird_outcomes(
        self,
    ) -> None:
        p = 2 @ P(H({1: 1, 2: 2}), H({3: 3, 4: 4}))
        p_weird = 2 @ P(
            H({NoCompare("oh-01"): 1, NoCompare("oh-02"): 2}),
            H({NoCompare("oh-03"): 3, NoCompare("oh-04"): 4}),
        )
        p_h_lo = p.h(0)
        assert repr(p_weird.h(0)) == repr(
            H({NoCompare("oh-01"): p_h_lo[1], NoCompare("oh-02"): p_h_lo[2]})
        )
        p_h_hi = p.h(-1)
        assert repr(p_weird.h(-1)) == repr(
            H({NoCompare("oh-03"): p_h_hi[3], NoCompare("oh-04"): p_h_hi[4]})
        )
        for i in range(len(p_weird)):
            assert type(next(iter(p_weird.h(i).outcomes()))) is type(
                next(iter(p_weird[i].outcomes()))
            )

    def test_which_selects_all_exactly_n_times_with_weird_outcomes(
        self,
    ) -> None:
        p = _PatchableP(
            2
            @ P(
                H({NoCompareCanOnlyAdd("one"): 1, NoCompareCanOnlyAdd("two"): 2}),
                H({NoCompareCanOnlyAdd("three"): 1, NoCompareCanOnlyAdd("four"): 1}),
            )
        )
        p_h: H[Any] = p.h(slice(None), slice(None), slice(None))
        assert tuple((str(outcome), count) for outcome, count in p_h.items()) == (
            ("four+four+four+four+four+four+one+one+one+one+one+one", 1),
            ("four+four+four+four+four+four+one+one+one+two+two+two", 4),
            ("four+four+four+four+four+four+two+two+two+two+two+two", 4),
            ("four+four+four+one+one+one+one+one+one+three+three+three", 2),
            ("four+four+four+one+one+one+three+three+three+two+two+two", 8),
            ("four+four+four+three+three+three+two+two+two+two+two+two", 8),
            ("one+one+one+one+one+one+three+three+three+three+three+three", 1),
            ("one+one+one+three+three+three+three+three+three+two+two+two", 4),
            ("three+three+three+three+three+three+two+two+two+two+two+two", 4),
        )
        assert type(next(iter(p_h.outcomes()))) is type(next(iter(p[0].outcomes())))

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
        # Highest of 2d6 (known distribution)
        assert (2 @ P(6)).h(-1) == H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})

    def test_which_index_lowest(self) -> None:
        # Lowest of 2d6 (known distribution, mirrors highest)
        assert (2 @ P(6)).h(0) == H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})

    def test_which_single_homogeneous_position_uses_order_stat(self) -> None:
        p = 4 @ P(H({1: 1, 2: 2, 3: 1}))
        with (
            patch.object(
                H,
                "order_stat_for_n_at_pos",
                wraps=H.order_stat_for_n_at_pos,
                autospec=True,
            ) as order_stat_for_n_at_pos,
            warnings.catch_warnings(record=True) as caught_warnings,
        ):
            assert p.h(2) == H({1: 13, 2: 176, 3: 67})
        order_stat_for_n_at_pos.assert_called_once_with(p[0], 4, 2)
        assert not caught_warnings

    def test_which_contiguous_homogeneous_end_uses_partial_selection(self) -> None:
        p = 4 @ P(H((-1, 0, 1)))
        with (
            patch(
                "dyce.p._rwc_homogeneous_one_end",
                wraps=_rwc_homogeneous_one_end,
            ) as rwc_homogeneous_one_end,
            patch("dyce.p._WhichHSurveyor") as which_h_surveyor,
        ):
            p.h(-2, -1)
        rwc_homogeneous_one_end.assert_called_once_with(4, p[0], 2, from_right=True)
        which_h_surveyor.assert_not_called()

    def test_which_contiguous_homogeneous_large_selection_uses_surveyor(self) -> None:
        p = 4 @ P(H((-1, 0, 1)))
        with (
            patch("dyce.p._rwc_homogeneous_one_end") as rwc_homogeneous_one_end,
            patch(
                "dyce.p._WhichHSurveyor",
                wraps=_WhichHSurveyor,
            ) as which_h_surveyor,
        ):
            p.h(-3, -2, -1)
        rwc_homogeneous_one_end.assert_not_called()
        which_h_surveyor.assert_called_once_with(p, (1, 2, 3))

    def test_h_which_homogeneous(self) -> None:
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
            expected = H.from_counts(
                (sum(roll), count)
                for roll, count in sort_and_select_from_rolls(
                    enumerate_weighted_unsorted_rolls_multinomial_coefficient(p_4df),
                    *which,
                )
            )
            assert p_4df.h(*which) == expected, f"mismatch for which={which}"

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
            expected = H.from_counts(
                (sum(roll), count)
                for roll, count in sort_and_select_from_rolls(
                    enumerate_weighted_unsorted_rolls_multinomial_coefficient(
                        p_4d3_4d4
                    ),
                    *which,
                )
            )
            assert p_4d3_4d4.h(*which) == expected, f"mismatch for which={which}"

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

    def test_single_die_pool_via_h_returns_self_for_minus_1(self) -> None:
        p = P(6)
        assert p.h(-1) == H(6)
        assert p.h(0) == H(6)

    def test_heterogeneous_max_matches_brute_force(self) -> None:
        # Cross-check the decomposed result against brute-force enumeration on a
        # small-enough pool to enumerate fully
        p = P(2 @ P(4), 3 @ P(6))
        via_decomp = p.h(-1)
        expected = H.from_counts(
            (max(roll), weight)
            for roll, weight in enumerate_weighted_unsorted_rolls_multinomial_coefficient(
                p
            )
        )
        assert dict(via_decomp) == dict(expected)

    def test_heterogeneous_min_matches_brute_force(self) -> None:
        p = P(2 @ P(4), 3 @ P(6))
        via_decomp = p.h(0)
        expected = H.from_counts(
            (min(roll), weight)
            for roll, weight in enumerate_weighted_unsorted_rolls_multinomial_coefficient(
                p
            )
        )
        assert dict(via_decomp) == dict(expected)


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
            for (
                roll,
                count,
            ) in sort_and_select_from_rolls(
                enumerate_weighted_unsorted_rolls_multinomial_coefficient(p)
            ):
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
        # Highest of 3d6 (known distribution)
        highs = H.from_counts(
            (roll[0], count) for roll, count in (3 @ P(6)).rolls_with_counts(-1)
        )
        assert highs == {6: 91, 5: 61, 4: 37, 3: 19, 2: 7, 1: 1}

    def test_which_index_lowest(self) -> None:
        lows = H.from_counts(
            (roll[0], count) for roll, count in (3 @ P(6)).rolls_with_counts(0)
        )
        assert lows == {1: 91, 2: 61, 3: 37, 4: 19, 5: 7, 6: 1}

    def test_which_single_homogeneous_position_uses_order_stat(self) -> None:
        p = 4 @ P(H({1: 1, 2: 2, 3: 1}))
        with (
            patch.object(
                H,
                "order_stat_for_n_at_pos",
                wraps=H.order_stat_for_n_at_pos,
                autospec=True,
            ) as order_stat_for_n_at_pos,
            patch("dyce.p._WhichRollSurveyor") as which_roll_surveyor,
            warnings.catch_warnings(record=True) as caught_warnings,
        ):
            assert dict(p.rolls_with_counts(2)) == {
                (1,): 13,
                (2,): 176,
                (3,): 67,
            }
        order_stat_for_n_at_pos.assert_called_once_with(p[0], 4, 2)
        which_roll_surveyor.assert_not_called()
        assert not caught_warnings

    def test_which_contiguous_homogeneous_end_uses_partial_selection(self) -> None:
        p = 4 @ P(H((-1, 0, 1)))
        with (
            patch(
                "dyce.p._rwc_homogeneous_one_end",
                wraps=_rwc_homogeneous_one_end,
            ) as rwc_homogeneous_one_end,
            patch("dyce.p._WhichRollSurveyor") as which_roll_surveyor,
        ):
            list(p.rolls_with_counts(-2, -1))
        rwc_homogeneous_one_end.assert_called_once_with(4, p[0], 2, from_right=True)
        which_roll_surveyor.assert_not_called()

    def test_which_multiple_positions_uses_surveyor(self) -> None:
        p = 4 @ P(H((-1, 0, 1)))
        with patch(
            "dyce.p._WhichRollSurveyor",
            wraps=_WhichRollSurveyor,
        ) as which_roll_surveyor:
            list(p.rolls_with_counts(1, 3))
        which_roll_surveyor.assert_called_once_with(p, (1, 3))

    def test_which_index_lowest_and_highest(self) -> None:
        p = 3 @ P(6)
        lo_hi = H.from_counts(p.rolls_with_counts(0, -1))
        expected = H.from_counts(((r[0], r[-1]), c) for r, c in p.rolls_with_counts())
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
            ((1, 2), 2),
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

    def test_which_homogeneous_matches_brute_force(self) -> None:
        p_df = P(H((-1, 0, 1)))
        p_4df = 4 @ p_df
        for which in (
            (slice(None),),
            (slice(0, 4),),
            (slice(-4, None),),
            (slice(0, 1),),
            (slice(1, 2),),
            (slice(2, 3),),
            (slice(3, 4),),
            (slice(0, 0),),
            (slice(2, 4),),
            (1, 3),
            (slice(5, 7),),
            (slice(-7, -5),),
        ):
            _assert_rwc_matches_brute_force(p_4df, *which)
        p_weighted = 4 @ P(H({1: 1, 2: 2, 3: 1}))
        _assert_rwc_matches_brute_force(p_weighted, slice(2))
        _assert_rwc_matches_brute_force(p_weighted, slice(-2, None))
        p_with_zero_weight = 4 @ P(H({1: 1, 2: 0, 3: 1}))
        _assert_rwc_matches_brute_force(p_with_zero_weight, slice(2))
        _assert_rwc_matches_brute_force(p_with_zero_weight, slice(-2, None))

    def test_which_heterogeneous_matches_brute_force(self) -> None:
        p_3 = P(H({i: i for i in range(1, 4)}))
        p_4n = P(H({-i: i for i in range(1, 5)}))
        p_3x3_4x4n = P(3 @ p_3, 4 @ p_4n)
        for which in (
            (slice(None),),
            (slice(4),),
            (slice(-4, None),),
            (slice(2, 4),),
            (slice(3),),
            (slice(-3, None),),
            (slice(2),),
            (slice(-2, None),),
            (slice(1),),
            (slice(-1, None),),
            (slice(0, 0),),
            (1, 3),
            (slice(5, 7),),
            (slice(-7, -5),),
            (slice(7, 9),),
            (slice(-9, -7),),
        ):
            _assert_rwc_matches_brute_force(p_3x3_4x4n, *which)


def test_rwc_heterogeneous_extremes_via_h() -> None:
    r"""P.h(0, -1) on a heterogeneous pool agrees with the brute-force sum."""
    d4, d6, d8, d10, d12, d20 = (H(n) for n in (4, 6, 8, 10, 12, 20))
    p = P(d4, d6, d8, d10, d12, d20)
    from_brute = H.from_counts(
        (sum(roll), count)
        for roll, count in sort_and_select_from_rolls(
            enumerate_weighted_unsorted_rolls_multinomial_coefficient(p), 0, -1
        )
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
        for roll, count in sort_and_select_from_rolls(
            enumerate_weighted_unsorted_rolls_multinomial_coefficient(p), 0, -1
        )
    )
    assert p.h(0, -1) == from_brute


# ---- Helpers -------------------------------------------------------------------------


def _assert_rwc_matches_brute_force(p: P[_T], *which: GetItemT) -> None:
    r"""
    Validate `rolls_with_counts` against brute-force enumeration.
    """
    known_counts: Counter[RollT[_T]] = Counter()
    test_counts: Counter[RollT[_T]] = Counter()
    for (
        roll,
        count,
    ) in sort_and_select_from_rolls(
        enumerate_weighted_unsorted_rolls_multinomial_coefficient(p), *which
    ):
        known_counts[roll] += count
    for roll, count in p.rolls_with_counts(*which):
        test_counts[roll] += count
    assert test_counts == known_counts

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

import itertools
import math
import operator
import statistics
import warnings
from contextlib import suppress
from decimal import Decimal
from fractions import Fraction
from unittest.mock import patch

import pytest

from dyce import H, TruncationWarning, explode_n
from dyce.h import (
    _convolve_fast,
    _convolve_linear,
    _ConvolveFallbackWarning,
)
from dyce.lifecycle import ExperimentalWarning
from dyce.types import BeartypeCallHintViolation

__all__ = ()

_OUTCOME_TYPES: tuple[type, ...] = (
    int,
    float,
    Decimal,
    Fraction,
)

with suppress(ImportError):
    import numpy as np

    _OUTCOME_TYPES += (
        np.int64,
        np.float128,
    )

with suppress(ImportError):
    import sympy  # type: ignore[import-untyped]

    _OUTCOME_TYPES += (
        sympy.Integer,
        sympy.Number,
        sympy.Rational,
    )


class TestHInit:
    def test_empty(self) -> None:
        assert H(()) == H({})

    def test_int_zero_is_empty(self) -> None:
        assert H(0) == H({})
        assert H(False) == H({})  # noqa: FBT003

    def test_int_scalar_positive(self) -> None:
        for i in range(7, 1, -1):
            h = H(i)
            assert h == H(dict.fromkeys(range(1, i + 1), 1))
            assert list(h.keys()) == list(range(1, i + 1))
            assert h.total == i

    def test_int_scalar_negative(self) -> None:
        for i in range(-7, -1):
            h = H(i)
            assert h == H(dict.fromkeys(range(i, 0), 1))
            assert list(h.keys()) == list(range(i, 0))
            assert h.total == abs(i)

    def test_non_int_scalar_raises(self) -> None:
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            H(None)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            H(3.0)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            H(Fraction(3))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError, match=r"\bscalar\b.*\bmust be int\b"):
            H(Decimal(3))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    def test_iterable(self) -> None:
        assert H((0, 0, 1, 0, 1)) == H({0: 3, 1: 2})
        assert H((1, 2, 3, 1, 2, 1)) == H({1: 3, 2: 2, 3: 1})

    def test_preserves_counts(self) -> None:
        h = H({0: 0, 1: 2, 2: 2, 3: 0})
        assert dict(h) == {0: 0, 1: 2, 2: 2, 3: 0}
        assert h == H(2)

    def test_mapping_supportsint(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for i in range(7, 1, -1):
                h = H({o_type(o): o_type(1) for o in range(-i, i)})
                assert h == H(dict.fromkeys(range(-i, i), 1))
                assert all(isinstance(o, o_type) for o in h.outcomes())
                assert all(isinstance(c, int) for c in h.counts())
                assert h.total == 2 * i

    def test_outcome_order(self) -> None:
        from dyce import h as h_module

        with patch.object(
            h_module, "natural_key", side_effect=h_module.natural_key
        ) as mock:
            assert list(H(4)) == [1, 2, 3, 4]
            mock.assert_not_called()
        with patch.object(
            h_module, "natural_key", side_effect=h_module.natural_key
        ) as mock:
            assert list(H(-3)) == [-3, -2, -1]
            mock.assert_not_called()

    def test_outcome_natural_order(self) -> None:
        from dyce import h as h_module

        with patch.object(
            h_module, "natural_key", side_effect=h_module.natural_key
        ) as mock:
            # TODO(posita): # noqa: TD003 - This should not need any ignore comments
            h_of_hs = H((H(1), H(2), H(3), H(4))) ** 2  # type: ignore[operator] # pyrefly: ignore[unsupported-operation]
            mock.assert_called()
        assert list(h_of_hs) == [
            H({1: 1, 4: 1, 9: 1, 16: 1}),
            H({1: 1, 4: 1, 9: 1}),
            H({1: 1, 4: 1}),
            H({1: 1}),
        ]

    def test_negative_count_raises(self) -> None:
        with pytest.raises(
            ValueError, match=r"\bcount\b.*\bcannot\b.*\bbe\b.*\bnegative\b"
        ):
            H({0: 0, 1: -1, 2: 2})

    def test_mapping_with_lossy_counts_raises(self) -> None:
        with pytest.raises(ValueError, match=r"\bcannot\b.*\blosslessly\b.*\bcoerce\b"):
            H({1: 1.5, 2: 2.5})


class TestHFromCounts:
    def test_empty(self) -> None:
        assert H.from_counts() == H({})

    def test_single_mapping(self) -> None:
        assert H.from_counts({1: 2, 2: 3}) == H({1: 2, 2: 3})

    def test_single_pairs(self) -> None:
        assert H.from_counts([(1, 3), (2, 2), (1, 1)]) == H({1: 4, 2: 2})

    def test_multiple_sources(self) -> None:
        assert H.from_counts({1: 2, 2: 3}, [(1, 1), (3, 4)]) == H({1: 3, 2: 3, 3: 4})

    def test_accumulates_h_objects(self) -> None:
        assert H.from_counts(H(6), H(6)) == H({1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2})  # pyrefly: ignore[no-matching-overload]

    def test_non_int_outcomes(self) -> None:
        assert H.from_counts([("a", 2), ("b", 1), ("a", 3)]) == H({"a": 5, "b": 1})


class TestHRepr:
    def test_repr(self) -> None:
        assert repr(H(())) == "H({})"
        assert repr(H(0)) == "H({})"
        assert repr(H(-6)) == "H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})"
        assert repr(H(6)) == "H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})"
        assert repr(H((1, 2, 3, 0, 1, 2, 1))) == "H({0: 1, 1: 3, 2: 2, 3: 1})"


class TestHEq:
    def test_equal(self) -> None:
        assert H({3: 1}) == H({3: 1})
        assert H({1: 2, 2: 3}) == H({1: 2, 2: 3})

    def test_not_equal(self) -> None:
        assert H({3: 1}) != H({4: 1})
        assert H({1: 1, 2: 1}) != H({1: 2})

    def test_equal_to_raw_dict(self) -> None:
        assert H(6) == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}


class TestHMapping:
    def test_getitem(self) -> None:
        d6_2 = 2 @ H(6)
        assert d6_2[2] == 1
        assert d6_2[7] == 6
        assert d6_2[12] == 1

    def test_getitem_missing(self) -> None:
        with pytest.raises(KeyError):
            H({1: 4, 2: 5})[6]

    def test_iter_empty(self) -> None:
        assert list(H({})) == []

    def test_iter(self) -> None:
        assert list(H({1: 4, 2: 5, 3: 1})) == [1, 2, 3]

    def test_len_empty(self) -> None:
        assert len(H(())) == 0
        assert len(H({})) == 0
        assert len(H(0)) == 0
        assert len(H(False)) == 0  # noqa: FBT003

    def test_len(self) -> None:
        d6_d8 = H(6) + H(8)
        assert len(d6_d8) == len(list(d6_d8.outcomes()))
        assert len(d6_d8) == 13
        assert len(d6_d8 + d6_d8) == 25

    def test_contains(self) -> None:
        h = H({1: 4, 2: 5})
        assert 1 in h
        assert 6 not in h

    def test_dict_conversion(self) -> None:
        assert dict(H({3: 2})) == {3: 2}

    def test_counts_values(self) -> None:
        d0 = H(())
        assert list(d0.counts()) == list(d0.values())

        d6_d8 = H(6) + H(8)
        assert list(d6_d8.counts()) == list(d6_d8.values())

    def test_outcomes_keys(self) -> None:
        d0 = H({})
        assert list(d0.outcomes()) == []
        assert list(d0.outcomes()) == list(d0.keys())

        d6_d8 = H(6) + H(8)
        assert list(d6_d8.outcomes()) == list(range(2, 6 + 8 + 1))
        assert list(d6_d8.outcomes()) == list(d6_d8.keys())

    def test_as_bool(self) -> None:
        assert bool(H({})) is False
        assert bool(H({0: 1})) is True
        assert bool(H(dict.fromkeys(range(10), 0))) is False


class TestHMatmul:
    def test_fwd(self) -> None:
        # 3-fold convolution of {1:1, 2:1} (fair d2)
        result = H({1: 1, 2: 1}) @ 3
        assert result == H({3: 1, 4: 3, 5: 3, 6: 1})

    def test_ref(self) -> None:
        # n @ H delegates to H @ n
        result = 3 @ H({1: 1, 2: 1})
        assert result == H({3: 1, 4: 3, 5: 3, 6: 1})

    def test_commutativity(self) -> None:
        h = H({1: 1, 2: 1})
        assert h @ 3 == 3 @ h

    def test_zero(self) -> None:
        result = H({1: 1, 2: 1}) @ 0
        assert result == H({})

    def test_one(self) -> None:
        result = H({1: 1, 2: 1}) @ 1
        assert result == H({1: 1, 2: 1})

    def test_two(self) -> None:
        result = H({1: 1, 2: 1}) @ 2
        assert result == H({2: 1, 3: 2, 4: 1})

    def test_lossless_float_rhs(self) -> None:
        # Integer results only, even with floats
        assert H({1: 1, 2: 1}) @ 3.0 == H({1: 1, 2: 1}) @ 3  # noqa: RUF069
        assert 3.0 @ H({1: 1, 2: 1}) == 3 @ H({1: 1, 2: 1})  # noqa: RUF069


class TestHAdd:
    def test_scalar_fwd(self) -> None:
        result = H({2: 3, 4: 1}) + 10
        assert result == H({12: 3, 14: 1})

        # TODO(posita): # noqa: TD003 - This should not need any ignore comments
        frac_int_result = H({Fraction(1, 2): 2, Fraction(3, 2): 1}) + 1  # type: ignore[operator]
        assert frac_int_result == H({Fraction(3, 2): 2, Fraction(5, 2): 1})

        # TODO(posita): # noqa: TD003 - This should not need any ignore comments
        frac_float_result = H({Fraction(1, 2): 2, Fraction(3, 2): 1}) + 1.5  # type: ignore[operator] # pyrefly: ignore[unsupported-operation]
        assert frac_float_result == H({Fraction(2): 2, Fraction(3): 1})

    def test_scalar_ref(self) -> None:
        result = 10 + H({2: 3, 4: 1})
        assert result == H({12: 3, 14: 1})

        dec_result = Decimal("2.0") + H(
            {
                Decimal("1.0"): 2,
                Decimal("3.0"): 1,
            }
        )
        assert dec_result == H({Decimal("3.0"): 2, Decimal("5.0"): 1})

    def test_histogram(self) -> None:
        result = H({1: 1, 2: 1, 3: 1}) + H({4: 2, 5: 3})
        assert result == H({5: 2, 6: 5, 7: 5, 8: 3})


class TestHSub:
    def test_scalar_fwd(self) -> None:
        result = H({5: 2, 8: 1}) - 3
        assert result == H({2: 2, 5: 1})

    def test_scalar_ref(self) -> None:
        result = 10 - H({3: 1, 4: 2})
        assert result == H({7: 1, 6: 2})

    def test_histogram(self) -> None:
        result = H({1.0: 1, 2.0: 1}) - H({0.5: 1, 1.5: 1})
        # (1.0-0.5)=0.5, (1.0-1.5)=-0.5, (2.0-0.5)=1.5, (2.0-1.5)=0.5
        assert result == H({0.5: 2, -0.5: 1, 1.5: 1})

        frac_result = H({Fraction(3, 2): 1, Fraction(5, 2): 1}) - H({Fraction(1, 2): 1})
        assert frac_result == H({Fraction(1, 1): 1, Fraction(2, 1): 1})


class TestHMul:
    def test_scalar_fwd(self) -> None:
        result = H({1: 4, 2: 5, 3: 1}) * 3
        assert result == H({3: 4, 6: 5, 9: 1})

    def test_scalar_ref(self) -> None:
        result = Fraction(1, 2) * H({1: 4, 2: 5, 3: 1})
        assert result == H({Fraction(1, 2): 4, Fraction(1, 1): 5, Fraction(3, 2): 1})

    def test_histogram(self) -> None:
        result = H({2: 1, 3: 1}) * H({4: 1, 5: 1})
        assert result == H({8: 1, 10: 1, 12: 1, 15: 1})


class TestHTruediv:
    def test_scalar_fwd(self) -> None:
        result = H({30: 1, 60: 2}) / 2
        assert result == H({15.0: 1, 30.0: 2})

        frac_result = H({3: 1, 6: 1}) / Fraction(2, 5)
        assert frac_result == H({Fraction(15, 2): 1, Fraction(15, 1): 1})

    def test_scalar_ref(self) -> None:
        result = 30 / H({2: 1, 3: 1})
        assert result == H({15.0: 1, 10.0: 1})

    def test_histogram(self) -> None:
        result = H({3: 1, 6: 1}) / H({2: 1, 3: 1})
        assert result == H({1.5: 1, 1.0: 1, 3.0: 1, 2.0: 1})


class TestHFloordiv:
    def test_scalar_fwd(self) -> None:
        result = H({7: 1, 9: 2}) // 2
        assert result == H({3: 1, 4: 2})

        frac_result = H({3: 1, 6: 1}) // Fraction(1, 2)
        assert frac_result == H({6: 1, 12: 1})

    def test_scalar_ref(self) -> None:
        result = 7 // H({2: 1, 3: 1})
        assert result == H({3: 1, 2: 1})

    def test_histogram(self) -> None:
        result = H({7: 1, 9: 1}) // H({2: 1, 3: 1})
        # 7//2=3, 7//3=2, 9//2=4, 9//3=3
        assert result == H({3: 2, 2: 1, 4: 1})


class TestHMod:
    def test_scalar_fwd(self) -> None:
        result = H({7: 1, 9: 2}) % 4
        assert result == H({3: 1, 1: 2})

    def test_scalar_ref(self) -> None:
        result = 10 % H({3: 1, 4: 1})
        assert result == H({1: 1, 2: 1})

    def test_histogram(self) -> None:
        result = H({7: 1, 9: 1}) % H({3: 1, 4: 1})
        # 7%3=1, 7%4=3, 9%3=0, 9%4=1
        assert result == H({1: 2, 3: 1, 0: 1})


class TestHPow:
    def test_scalar_fwd(self) -> None:
        result = H({2: 1, 3: 2}) ** 3
        assert result == H({8: 1, 27: 2})

    def test_scalar_ref(self) -> None:
        result = 2.0 ** H({3: 1, 4: 1})
        assert result == H({8.0: 1, 16.0: 1})

    def test_histogram(self) -> None:
        result = H({2: 1, 3: 1}) ** H({2: 1, 3: 1})
        # 2**2=4, 2**3=8, 3**2=9, 3**3=27
        assert result == H({4: 1, 8: 1, 9: 1, 27: 1})


class TestHLshift:
    def test_scalar_fwd(self) -> None:
        result = H({1: 1, 2: 2}) << 3
        assert result == H({8: 1, 16: 2})

    def test_scalar_ref(self) -> None:
        result = 1 << H({2: 1, 3: 1})
        assert result == H({4: 1, 8: 1})

    def test_histogram(self) -> None:
        result = H({1: 1, 2: 1}) << H({2: 1, 3: 1})
        # 1<<2=4, 1<<3=8, 2<<2=8, 2<<3=16
        assert result == H({4: 1, 8: 2, 16: 1})


class TestHRshift:
    def test_scalar_fwd(self) -> None:
        result = H({16: 2, 32: 1}) >> 2
        assert result == H({4: 2, 8: 1})

    def test_scalar_ref(self) -> None:
        result = 64 >> H({2: 1, 3: 1})
        assert result == H({16: 1, 8: 1})

    def test_histogram(self) -> None:
        result = H({16: 1, 32: 1}) >> H({2: 1, 3: 1})
        # 16>>2=4, 16>>3=2, 32>>2=8, 32>>3=4
        assert result == H({4: 2, 2: 1, 8: 1})


class TestHAnd:
    def test_scalar_fwd(self) -> None:
        result = H({5: 1, 6: 2}) & 3
        # 5&3=1, 6&3=2
        assert result == H({1: 1, 2: 2})

    def test_scalar_ref(self) -> None:
        result = 7 & H({5: 1, 6: 1})
        # 7&5=5, 7&6=6
        assert result == H({5: 1, 6: 1})

    def test_histogram(self) -> None:
        result = H({5: 1, 6: 1}) & H({3: 1, 4: 1})
        # 5&3=1, 5&4=4, 6&3=2, 6&4=4
        assert result == H({1: 1, 4: 2, 2: 1})


class TestHOr:
    def test_scalar_fwd(self) -> None:
        result = H({4: 1, 2: 2}) | 1
        # 4|1=5, 2|1=3
        assert result == H({5: 1, 3: 2})

    def test_scalar_ref(self) -> None:
        result = 8 | H({1: 1, 2: 1})
        # 8|1=9, 8|2=10
        assert result == H({9: 1, 10: 1})

    def test_histogram(self) -> None:
        result = H({4: 1, 2: 1}) | H({1: 1, 2: 1})
        # 4|1=5, 4|2=6, 2|1=3, 2|2=2
        assert result == H({5: 1, 6: 1, 3: 1, 2: 1})


class TestHXor:
    def test_scalar_fwd(self) -> None:
        result = H({5: 1, 6: 2}) ^ 3
        # 5^3=6, 6^3=5
        assert result == H({6: 1, 5: 2})

    def test_scalar_ref(self) -> None:
        result = 7 ^ H({5: 1, 6: 1})
        # 7^5=2, 7^6=1
        assert result == H({2: 1, 1: 1})

    def test_histogram(self) -> None:
        result = H({5: 1, 6: 1}) ^ H({3: 1, 4: 1})
        # 5^3=6, 5^4=1, 6^3=5, 6^4=2
        assert result == H({6: 1, 1: 1, 5: 1, 2: 1})


class TestHUnary:
    def test_neg(self) -> None:
        result = -H({1: 3, 2: 2})
        assert result == H({-1: 3, -2: 2})

    def test_neg_fraction(self) -> None:
        result = -H({Fraction(1, 2): 2, Fraction(3, 2): 1})
        assert result == H({Fraction(-1, 2): 2, Fraction(-3, 2): 1})

    def test_pos(self) -> None:
        result = +H({-1: 3, 2: 2})
        assert result == H({-1: 3, 2: 2})

    def test_abs(self) -> None:
        result = abs(H({-2: 1, 3: 2}))
        assert result == H({2: 1, 3: 2})

    def test_invert(self) -> None:
        result = ~H({1: 1, 2: 1})
        # ~1=-2, ~2=-3
        assert result == H({-2: 1, -3: 1})


class TestHUnsupportedOperations:
    def test_matmul_negative_rhs(self) -> None:
        result = H({1: 1}).__matmul__(-1)
        assert result is NotImplemented
        with pytest.raises(TypeError):
            _ = -1 @ H({1: 1})

    def test_rmatmul_non_int_rhs(self) -> None:
        result = H({1: 1}).__rmatmul__(1.5)
        assert result is NotImplemented
        with pytest.raises(TypeError):
            _ = 1.5 @ H({1: 1})

    @pytest.mark.filterwarnings(r"ignore")  # constrain warnings to test
    def test_matmul_on_non_addable_outcomes(self) -> None:
        # Use catch_warnings directly because pytest.warns will fail if short-circuited
        # by call to __matmul__ raising BeartypeCallHintViolation when beartype is
        # enabled
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", category=_ConvolveFallbackWarning)
            try:
                result = H({frozenset({"incompatible"}): 1}).__matmul__(2)  # type: ignore[operator] # ty: ignore[no-matching-overload]
                assert result is NotImplemented
                assert any(
                    issubclass(w.category, _ConvolveFallbackWarning) for w in caught
                )
            except BeartypeCallHintViolation:
                # beartype pre-check preempts __matmul__ before it can warn or return
                # NotImplemented
                pass
        # Call to __rmatmul__ raises one of BeartypeCallHintViolation and TypeError
        # (from NotImplemented), depending on whether beartype is enabled
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            _ = 2 @ H({frozenset({"incompatible"}): 1})  # type: ignore[operator] # ty: ignore[unsupported-operator]

    def test_add_unsupported(self) -> None:
        assert H({3: 1}).__add__("incompatible") is NotImplemented  # type: ignore[operator] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError):
            H({3: 1}) + "incompatible"  # type: ignore[operator] # ty: ignore[unsupported-operator]

    def test_radd_unsupported(self) -> None:
        assert H({3: 1}).__radd__(frozenset({"incompatible"})) is NotImplemented  # type: ignore[operator] # ty: ignore[no-matching-overload]
        with pytest.raises(TypeError):
            frozenset({"incompatible"}) + H({3: 1})  # type: ignore[operator] # ty: ignore[unsupported-operator]

    def test_mul_unsupported(self) -> None:
        result = H({3.0: 1}).__mul__(Decimal("3.0"))  # type: ignore[operator,var-annotated] # ty: ignore[no-matching-overload]
        assert result is NotImplemented
        with pytest.raises(TypeError):
            H({3.0: 1}) * Decimal("3.0")  # type: ignore[operator] # ty: ignore[unsupported-operator]

    def test_pos_unsupported(self) -> None:
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            H({"hello": 1}).__pos__()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            +H({"hello": 1})  # type: ignore[misc] # ty: ignore[unsupported-operator]

    def test_neg_unsupported(self) -> None:
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            H({"hello": 1}).__neg__()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            -H({"hello": 1})  # type: ignore[misc] # ty: ignore[unsupported-operator]

    def test_abs_unsupported(self) -> None:
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            H({"hello": 1}).__abs__()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            abs(H({"hello": 1}))  # pyrefly: ignore[no-matching-overload] # pyright: ignore[reportArgumentType]

    def test_invert_unsupported(self) -> None:
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            H({1.5: 1}).__invert__()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        with pytest.raises((TypeError, BeartypeCallHintViolation)):
            ~H({1.5: 1})  # type: ignore[misc] # ty: ignore[unsupported-operator]


class TestHTotal:
    def test_sum_of_counts(self) -> None:
        d6_d8 = H(6) + H(8)
        assert d6_d8.total == sum(d6_d8.counts())
        assert d6_d8.total == 48
        assert (d6_d8 + d6_d8).total == 2_304

    def test_empty(self) -> None:
        assert H({}).total == 0

    def test_memoized(self) -> None:
        h = H({1: 2, 2: 3})
        assert h.total is h._total  # noqa: SLF001


class TestHApply:
    def test_scalar_empty(self) -> None:
        assert H({}).apply(operator.add, 1) == H({})

    def test_scalar_basic(self) -> None:
        assert H(6).apply(operator.pow, 2) == H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1})

    def test_scalar_collision(self) -> None:
        assert H({1: 2, 2: 3, 3: 1}).apply(operator.mod, 2) == H({1: 3, 0: 3})
        assert H(6).apply(operator.ge, 3) == H({False: 2, True: 4})

    def test_h_empty(self) -> None:
        assert H({}).apply(operator.add, H(1)) == H({})
        assert H(1).apply(operator.add, H({})) == H({})

    def test_h_basic(self) -> None:
        assert H({10: 1, 20: 1}).apply(operator.sub, H(2)) == H(
            {9: 1, 19: 1, 8: 1, 18: 1}
        )

    def test_h_collision(self) -> None:
        # (1+2)=3 and (2+1)=3 collide; (1+1)=2, (2+2)=4
        assert H(2).apply(operator.add, H(2)) == H({2: 1, 3: 2, 4: 1})


class TestHExactlyKTimesInN:
    def test_exactly_k_times_in_n(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            for h in (
                H(20),
                H(20).merge(H(20)).merge(H(20)),
                H({i: i for i in range(10)}),
                H({9 - i: i for i in range(10)}),
                H({i: i for i in range(1, 6)}).merge(
                    H({i: 11 - i for i in range(6, 11)})
                ),
            ):
                for n in range(10, 0, -1):
                    for outcome in h:
                        counts = n @ h.eq(outcome)
                        for k in range(n + 1):
                            assert h.exactly_k_times_in_n(outcome, n, k) == counts[k]

    def test_exactly_k_times_in_n_k_exceeds_n_raises(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            with pytest.raises(
                ValueError, match=r"\bk\b.*\bmust be less than or equal to n\b"
            ):
                H(6).exactly_k_times_in_n(outcome=1, n=2, k=3)

    def test_exactly_k_times_in_n_k_warns_experimental(self) -> None:
        with pytest.warns(ExperimentalWarning, match=r"\bexperimental\b"):
            H(6).exactly_k_times_in_n(outcome=1, n=3, k=2)


class TestHFormat:
    def test_format_short_empty(self) -> None:
        with pytest.warns(UserWarning, match=r"^mean of empty histogram is undefined$"):
            assert H(0).format_short() == "{}"

    def test_format(self) -> None:
        with pytest.warns(UserWarning, match=r"^mean of empty histogram is undefined$"):
            assert H(0).format() == ""

    def test_format_natural_order(self) -> None:
        h_of_hs = H((H(1), H(2), H(3), H(4))) ** 2  # type: ignore[operator]
        with pytest.warns(
            UserWarning,
            match=r"\bargument must be a string or a\b.*\bnumber, not\b|\bviolates type hint\b",
        ):
            assert (
                h_of_hs.format(width=65)
                == r"""
H({1: 1, 4: 1, 9: 1, 16: 1}) |  25.00% |######
       H({1: 1, 4: 1, 9: 1}) |  25.00% |######
             H({1: 1, 4: 1}) |  25.00% |######
                   H({1: 1}) |  25.00% |######
        """.strip()
            )


class TestHLowestTerms:
    def test_already_lowest(self) -> None:
        assert H({1: 1, 2: 3}).lowest_terms() == H({1: 1, 2: 3})

    def test_reduces_counts(self) -> None:
        assert H({1: 2, 2: 4, 3: 6}).lowest_terms() == H({1: 1, 2: 2, 3: 3})

    def test_empty(self) -> None:
        assert H({}).lowest_terms() == H({})

    def test_removes_zero_counts(self) -> None:
        assert H({1: 3, 2: 0, 3: 6}).lowest_terms() == H({1: 1, 3: 2})

    def test_all_zero_counts_is_empty(self) -> None:
        assert H({1: 0, 2: 0}).lowest_terms() == H({})

    def test_equality_uses_lowest_terms(self) -> None:
        base = H(range(10))
        assert base == base.merge(base)
        assert base == base.merge(base).merge(base)
        assert hash(base) == hash(base.merge(base).merge(base).lowest_terms())


class TestHMean:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match=r"^mean of empty histogram is undefined$"):
            H({}).mean()

    def test_mean(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = 2 @ H(o_type(i) for i in range(10))  # pyrefly: ignore[unsupported-operation]
            h_mean = h.mean()
            stat_mean = statistics.mean(
                itertools.chain(
                    *(  # type: ignore[var-annotated]
                        itertools.repeat(float(outcome), count)
                        for outcome, count in h.items()
                    )
                )
            )
            assert math.isclose(
                h_mean,
                stat_mean,
            ), f"o_type: {o_type}"


class TestHMerge:
    def test_merge_does_not_invoke_lowest_terms(self) -> None:
        base = H(range(10))
        assert base == base.merge(base)
        assert dict(base) != dict(base.merge(base))


class TestHOrderStatForNAtPos:
    def test_order_stat_for_n_at_pos(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            for h in (
                H(6),
                H((2, 3, 3, 4, 4, 5)),
                H({i: i for i in range(1, 6)}),
            ):
                for n in range(1, 5):
                    for pos in range(n):
                        result = h.order_stat_for_n_at_pos(n, pos)
                        for outcome in h:
                            brute = sum(
                                count
                                for roll, count in (
                                    (sorted(r), c)
                                    for r, c in (
                                        (list(combo), math.prod(h[v] for v in combo))
                                        for combo in itertools.product(
                                            h.outcomes(), repeat=n
                                        )
                                    )
                                )
                                if roll[pos] == outcome
                            )
                            assert result.get(outcome, 0) == brute  # pyright: ignore[reportArgumentType,reportCallIssue]

    def test_order_stat_for_n_at_pos_negative_index(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            h = H(6)
            for n in range(1, 7):
                for pos in range(n):
                    assert h.order_stat_for_n_at_pos(
                        n, pos
                    ) == h.order_stat_for_n_at_pos(n, pos - n)

    def test_order_stat_for_n_at_pos_out_of_bounds_raises(self) -> None:
        h = H(6)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            with pytest.raises(ValueError, match=r"\bpos\b.*\bmust be in range\b"):  # noqa: PT012
                result = h.order_stat_for_n_at_pos(3, 5)
                assert all(count == 0 for count in result.counts())

    def test_order_stat_for_n_at_pos_caches_by_n(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            h = H(6)
            _ = h.order_stat_for_n_at_pos(4, 0)
            _ = h.order_stat_for_n_at_pos(4, 3)
            assert len(h._order_stat_funcs_by_n) == 1  # noqa: SLF001
            _ = h.order_stat_for_n_at_pos(5, 0)
            assert len(h._order_stat_funcs_by_n) == 2  # noqa: SLF001

    def test_order_stat_for_n_at_pos_warns_experimental(self) -> None:
        with pytest.warns(ExperimentalWarning, match=r"\bexperimental\b"):
            H(6).order_stat_for_n_at_pos(2, 0)


class TestHProbabilityItems:
    def test_basic(self) -> None:
        assert list(H({1: 1, 2: 2, 3: 1}).probability_items()) == [
            (1, Fraction(1, 4)),
            (2, Fraction(1, 2)),
            (3, Fraction(1, 4)),
        ]

    def test_empty(self) -> None:
        assert list(H({}).probability_items()) == []

    def test_sums_to_one(self) -> None:
        total = sum(p for _, p in H({1: 1, 2: 2, 3: 1}).probability_items())
        assert total == Fraction(1)


class TestHRoll:
    def test_roll_empty_raises(self) -> None:
        with pytest.raises(
            ValueError, match=r"^no outcomes from which to select in empty histogram$"
        ):
            H({}).roll()

    def test_roll(self) -> None:
        d6 = H(6)
        assert all(d6.roll() in d6 for _ in range(100))


class TestHStdev:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match=r"^mean of empty histogram is undefined$"):
            H({}).stdev()

    def test_stdev(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = 2 @ H(o_type(i) for i in range(10))  # pyrefly: ignore[unsupported-operation]
            h_stdev = h.stdev()
            stat_stdev = statistics.pstdev(
                itertools.chain(
                    *(  # type: ignore[var-annotated]
                        itertools.repeat(float(outcome), count)
                        for outcome, count in h.items()
                    )
                )
            )
            assert math.isclose(
                h_stdev,
                stat_stdev,
            ), f"o_type: {o_type}"

    def test_sqrt_of_variance(self) -> None:
        h = 2 @ H(6)
        assert math.isclose(h.stdev(), math.sqrt(h.variance()))


class TestHVariance:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match=r"^mean of empty histogram is undefined$"):
            H({}).variance()

    def test_variance(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(i) for i in range(10))
            h_variance = h.variance()
            stat_variance = statistics.pvariance(
                itertools.chain(
                    *(
                        itertools.repeat(float(outcome), count)
                        for outcome, count in h.items()
                    )
                )
            )
            assert math.isclose(
                h_variance,
                stat_variance,
            ), f"o_type: {o_type}"

    def test_variance_overflow(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            warnings.filterwarnings("ignore", category=TruncationWarning)
            assert math.isclose(
                explode_n(H(6), n=800, precision=Fraction(0)).variance(), 10.64
            )
            assert math.isclose(
                explode_n(H(20), n=400, precision=Fraction(0)).variance(),
                52.16066481994455,
            )


class TestConvolveFast:
    def test_returns_dict_not_not_implemented(self) -> None:
        result = _convolve_fast({1: 1, 2: 1}, 3)
        assert result is not NotImplemented

    def test_matches_linear(self) -> None:
        mapping = {1: 1, 2: 1, 3: 1}
        for n in range(1, 8):
            assert _convolve_fast(mapping, n) == _convolve_linear(mapping, n)

    def test_fallback_warns(self) -> None:
        from dyce import h as h_module

        with (
            patch.object(h_module, "_convolve_fast", return_value=NotImplemented),
            pytest.warns(_ConvolveFallbackWarning, match=r"int"),
        ):
            H(2) @ 2  # pyright: ignore[reportUnusedExpression]

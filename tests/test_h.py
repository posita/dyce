# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations, generator_stop

import itertools
import math
import operator
import os
import statistics
from decimal import Decimal
from fractions import Fraction
from typing import Union

import numpy
import pytest
import sympy

from dyce import H
from dyce.h import _within

from .numberwang import Numberwang, Wangernumb

__all__ = ()


_INTEGRAL_TYPES = (
    int,
    Numberwang,
    numpy.int64,
    # sympy.Integer,  # See https://github.com/sympy/sympy/issues/19311
)
_COUNT_TYPES = _INTEGRAL_TYPES + (
    sympy.Integer,  # See https://github.com/sympy/sympy/issues/19311
)
_NUMERICAL_OUTCOME_TYPES = _COUNT_TYPES + (
    float,
    Decimal,
    Fraction,
    Wangernumb,
    numpy.float128,
    sympy.Float,
    sympy.Number,
    sympy.Rational,
    sympy.RealNumber,
)

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
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            d2 = H({o_type(o): c_type(1) for o in range(2, 0, -1)})
            d3 = H({o_type(o): c_type(1) for o in range(3, 0, -1)})
            sum_d2_d3 = {
                o_type(2): 1,
                o_type(3): 2,
                o_type(4): 2,
                o_type(5): 1,
            }
            assert d2 + d3 == sum_d2_d3, f"o_type: {o_type}; c_type: {c_type}"
            assert d3 + d2 == sum_d2_d3, f"o_type: {o_type}; c_type: {c_type}"
            assert d2 + d3 == d3 + d2, f"o_type: {o_type}; c_type: {c_type}"

            assert d2 + H({}) == d2, f"o_type: {o_type}; c_type: {c_type}"
            assert H({}) + d3 == d3, f"o_type: {o_type}; c_type: {c_type}"

    def test_op_add_sym(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            d3 = H({o_type(o): c_type(1) for o in range(3, 0, -1)})
            x = sympy.symbols("x")
            sum_d3_x = {o_type(o) + x: c_type(1) for o in range(3, 0, -1)}
            assert d3 + x == sum_d3_x, f"o_type: {o_type}; c_type: {c_type}"
            sum_x_d3 = {x + o_type(o): c_type(1) for o in range(3, 0, -1)}
            assert x + d3 == sum_x_d3, f"o_type: {o_type}; c_type: {c_type}"

    def test_op_add_num(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h1 = H({o_type(i): c_type(1) for i in range(10, 20)})
            h2 = H({o_type(i): c_type(1) for i in range(11, 21)})
            assert h2 == h1 + 1, f"o_type: {o_type}; c_type: {c_type}"
            assert 1 + h1 == h2, f"o_type: {o_type}; c_type: {c_type}"

    def test_op_sub_h(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            d2 = H({o_type(o): c_type(1) for o in range(2, 0, -1)})
            d3 = H({o_type(o): c_type(1) for o in range(3, 0, -1)})
            assert d2 - d3 == {
                o_type(-2): 1,
                o_type(-1): 2,
                # See https://github.com/sympy/sympy/issues/6545
                o_type(0) + o_type(0): 2,
                o_type(1): 1,
            }, f"o_type: {o_type}; c_type: {c_type}"
            assert d3 - d2 == {
                o_type(-1): 1,
                # See https://github.com/sympy/sympy/issues/6545
                o_type(0) + o_type(0): 2,
                o_type(1): 2,
                o_type(2): 1,
            }, f"o_type: {o_type}; c_type: {c_type}"
            assert d2 - H({}) == d2
            assert H({}) - d3 == -d3

    def test_wn(self) -> None:
        pass

    def test_op_sub_sym(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            d3 = H({o_type(o): c_type(1) for o in range(3, 0, -1)})
            x = sympy.symbols("x")
            diff_d3_x = {o_type(o) - x: c_type(1) for o in range(3, 0, -1)}
            assert d3 - x == diff_d3_x, f"o_type: {o_type}; c_type: {c_type}"
            diff_x_d3 = {x - o_type(o): c_type(1) for o in range(3, 0, -1)}
            assert x - d3 == diff_x_d3, f"o_type: {o_type}; c_type: {c_type}"

    def test_op_sub_num(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h1 = H({o_type(i): c_type(1) for i in range(10, 20)})
            h2 = H({o_type(i): c_type(1) for i in range(9, 19)})
            h3 = H({o_type(i): c_type(1) for i in range(-8, -18, -1)})
            assert h2 == h1 - 1, f"o_type: {o_type}; c_type: {c_type}"
            assert 1 - h2 == h3, f"o_type: {o_type}; c_type: {c_type}"

    def test_op_matmul(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            try:
                d6 = H(o_type(6))
            except ValueError:
                d6 = H((o_type(i) for i in range(6, 0, -1)))

            d6_2 = d6 + d6
            d6_3 = d6_2 + d6
            assert 0 @ d6 == H({}), f"o_type: {o_type}; c_type: {c_type}"
            assert H({}) == d6 @ 0, f"o_type: {o_type}; c_type: {c_type}"
            assert 2 @ d6 == d6_2, f"o_type: {o_type}; c_type: {c_type}"
            assert d6_2 == d6 @ 2, f"o_type: {o_type}; c_type: {c_type}"
            assert d6_3 == 3 @ d6, f"o_type: {o_type}; c_type: {c_type}"
            assert 4 @ d6 == d6 @ 2 @ 2, f"o_type: {o_type}; c_type: {c_type}"

    def test_map(self) -> None:
        within_1_filter = _within(-1, 1)
        d8_v_d6 = {
            -1: 10,
            0: 17,
            1: 21,
        }

        within_7_9_filter = _within(7, 9)
        d6_2_v_7_9 = {
            -1: 15,
            0: 15,
            1: 6,
        }

        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            d6 = H({o_type(i): c_type(1) for i in range(6, 0, -1)})
            d8 = H({o_type(i): c_type(1) for i in range(8, 0, -1)})

            assert (
                d8.map(within_1_filter, d6) == d8_v_d6
            ), f"o_type: {o_type}; c_type: {c_type}"

            assert (2 @ d6).map(
                within_7_9_filter, 0
            ) == d6_2_v_7_9, f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_eq(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.eq(0) == H(
                (False, True, False)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.eq(h) == H(
                (True, False, False, False, True, False, False, False, True)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_ne(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.ne(0) == H(
                (True, False, True)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.ne(h) == H(
                (False, True, True, True, False, True, True, True, False)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_lt(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.lt(0) == H(
                (True, False, False)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.lt(h) == H(
                (False, True, True, False, False, True, False, False, False)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_le(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.le(0) == H(
                (True, True, False)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.le(h) == H(
                (True, True, True, False, True, True, False, False, True)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_gt(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.gt(0) == H(
                (False, False, True)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.gt(h) == H(
                (False, False, False, True, False, False, True, True, False)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_cmp_ge(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H({o_type(i): c_type(1) for i in range(-1, 2)})
            assert h.ge(0) == H(
                (False, True, True)
            ), f"o_type: {o_type}; c_type: {c_type}"
            assert h.ge(h) == H(
                (True, False, False, True, True, False, True, True, True)
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_even(self) -> None:
        for o_type in _INTEGRAL_TYPES:
            assert H(o_type(7)).even() == {
                False: 4,
                True: 3,
            }, f"o_type: {o_type}"

    def test_even_wrong_type(self) -> None:
        with pytest.raises(TypeError):
            _ = H((float(i) for i in range(7, 0, -1))).even()

    def test_odd(self) -> None:
        for o_type in _INTEGRAL_TYPES:
            assert H(o_type(7)).odd() == {
                False: 3,
                True: 4,
            }, f"o_type: {o_type}"

    def test_odd_wrong_type(self) -> None:
        with pytest.raises(TypeError):
            _ = H((float(i) for i in range(7, 0, -1))).odd()

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
            outcome: float,
        ) -> Union[float, H]:
            return outcome * 2 if outcome % 2 != 0 else outcome

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
            outcome: float,
        ) -> Union[float, H]:
            return outcome

        d20 = H(20)
        assert d20.substitute(never_expand) == d20
        assert d20.substitute(never_expand, operator.add, 20) == d20

    def test_substitute_reroll_d4_threes(self) -> None:
        def reroll_d4_threes(h: H, outcome: float) -> Union[float, H]:
            return h if max(h) == 4 and outcome == 3 else outcome

        h = H(4)
        assert h.substitute(reroll_d4_threes) == H({4: 5, 3: 1, 2: 5, 1: 5})
        assert h.substitute(reroll_d4_threes, operator.add) == H(
            {7: 1, 6: 1, 5: 1, 4: 5, 2: 4, 1: 4}
        )
        assert h.substitute(reroll_d4_threes, operator.mul, max_depth=2) == H(
            {36: 1, 27: 1, 18: 1, 12: 4, 9: 1, 6: 4, 4: 16, 3: 4, 2: 16, 1: 16}
        )

    def test_format(self) -> None:
        h = H({3: 1, 2: 2, 1: 3})
        assert h.format(width=115) == os.linesep.join(
            (
                "avg |    1.67",
                "std |    0.75",
                "var |    0.56",
                "  1 |  50.00% |##################################################",
                "  2 |  33.33% |#################################",
                "  3 |  16.67% |################",
            )
        )
        assert h.format(width=0) == "{avg: 1.67, 1: 50.00%, 2: 33.33%, 3: 16.67%}"

    def test_mean(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H((o_type(i), c_type(i)) for i in range(10))
            h_mean = h.mean()
            stat_mean = statistics.mean(
                itertools.chain(
                    *(
                        itertools.repeat(float(outcome), count)
                        for outcome, count in h.items()
                    )
                )
            )
            assert math.isclose(
                h_mean,
                stat_mean,
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_stdev(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H((o_type(i), c_type(i)) for i in range(10))
            h_stdev = h.stdev()
            stat_stdev = statistics.pstdev(
                itertools.chain(
                    *(
                        itertools.repeat(float(outcome), count)
                        for outcome, count in h.items()
                    )
                )
            )
            assert math.isclose(
                h_stdev,
                stat_stdev,
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_variance(self) -> None:
        for o_type, c_type in itertools.product(_NUMERICAL_OUTCOME_TYPES, _COUNT_TYPES):
            h = H((o_type(i), c_type(i)) for i in range(10))
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
            ), f"o_type: {o_type}; c_type: {c_type}"

    def test_roll(self) -> None:
        d6 = H(6)
        assert all(d6.roll() in d6 for _ in range(1000))


def test_within() -> None:
    within_filter = _within(0, 2)
    assert getattr(within_filter, "lo") == 0
    assert getattr(within_filter, "hi") == 2
    assert within_filter(5, 2) > 0
    assert within_filter(5, 3) == 0
    assert within_filter(5, 4) == 0
    assert within_filter(5, 5) == 0
    assert within_filter(5, 6) < 0

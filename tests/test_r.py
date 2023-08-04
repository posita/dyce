# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import operator
import re

from dyce import H, P, R
from dyce.r import (
    CoalesceMode,
    PoolRoller,
    RollOutcome,
    SubstitutionRoller,
    ValueRoller,
)

from .test_h import _INTEGRAL_OUTCOME_TYPES, _OUTCOME_TYPES

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


class TestValueRoller:
    def test_init_outcome(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                annotation = f"{o_type}({v})"
                r = R.from_value(o, annotation=annotation)
                assert r.value == o, r
                assert r.annotation == annotation, r

    def test_init_h(self) -> None:
        d6 = H(6)
        r_d6 = R.from_value(d6, annotation="d6")
        assert r_d6.value == d6
        assert r_d6.annotation == "d6"

    def test_init_p(self) -> None:
        p_3d6 = 3 @ P(6)
        r_3d6 = R.from_value(p_3d6, annotation="3d6")
        assert r_3d6.value == p_3d6
        assert r_3d6.annotation == "3d6"

    def test_repr(self) -> None:
        assert repr(R.from_value(42)) == "ValueRoller(value=42, annotation='')"
        assert (
            repr(R.from_value(H(6), annotation={"one": 1}))
            == "ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation={'one': 1})"
        )
        assert (
            repr(R.from_value(3 @ P(6), annotation={"two": 2}))
            == "ValueRoller(value=3@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})), annotation={'two': 2})"
        )

    def test_op_eq(self) -> None:
        r_42 = R.from_value(42)
        assert isinstance(r_42, ValueRoller)

        r_42_annotated = R.from_value(42, annotation="42")
        assert r_42 == r_42
        assert r_42 != r_42_annotated
        assert r_42_annotated == r_42_annotated

        assert r_42 != -r_42
        assert -r_42 == -r_42
        assert -r_42 != R.from_value(-42)

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(v) for v in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")

            for _ in range(10):
                r_roll = r.roll()
                (roll_outcome,) = r_roll
                assert roll_outcome.r == r
                assert r_roll.total() in h, r


class TestRepeatRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_3 = r_42 @ 3
        assert (
            repr(r_42_3)
            == """RepeatRoller(
  n=3,
  source=ValueRoller(value=42, annotation=''),
  annotation='',
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_2 = 2 @ r_d6
        assert (
            repr(r_d6_2)
            == """RepeatRoller(
  n=2,
  source=ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation='d6'),
  annotation='',
)"""
        )

    def test_op_eq(self) -> None:
        r_42 = R.from_value(42)
        r_42_annotated = r_42.annotate("42")
        assert 3 @ r_42 == 3 @ r_42
        assert 3 @ r_42 != 3 @ r_42_annotated
        assert 3 @ r_42_annotated == 3 @ r_42.annotate("42")

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for i_type in _INTEGRAL_OUTCOME_TYPES:
                h = H(o_type(v) for v in range(-2, 3))
                r = R.from_value(h, annotation=f"{o_type}")
                r_100 = (i_type(100) @ r).annotate(f"{i_type}")
                r_100_roll = r_100.roll()
                assert len(r_100_roll) == 100

                for outcome in r_100_roll.outcomes():
                    assert outcome in h, r_100_roll


class TestBinarySumOpRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_squared = r_42 * r_42
        assert (
            repr(r_42_squared)
            == """BinarySumOpRoller(
  bin_op=<built-in function mul>,
  left_source=ValueRoller(value=42, annotation=''),
  right_source=ValueRoller(value=42, annotation=''),
  annotation='',
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_2 = r_d6 + r_d6
        assert (
            repr(r_d6_2)
            == """BinarySumOpRoller(
  bin_op=<built-in function add>,
  left_source=ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation='d6'),
  right_source=ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation='d6'),
  annotation='',
)"""
        )

    def test_op_eq(self) -> None:
        r_42 = R.from_value(42)
        r_42_annotated = R.from_value(42, annotation="42")
        r_42_add_r_42 = r_42 + r_42
        r_42_add_r_42_annotated = r_42 + r_42_annotated
        r_42_annotated_add_r_42 = r_42_annotated + r_42
        r_42_annotated_add_r_42_annotated = r_42_annotated + r_42_annotated
        r_42_mul_r_42 = r_42 * r_42
        r_42_mul_r_42_annotated = r_42 * r_42_annotated
        r_42_annotated_mul_r_42 = r_42_annotated * r_42
        assert r_42_add_r_42 == r_42 + r_42
        assert r_42_add_r_42_annotated == r_42 + r_42.annotate("42")
        assert r_42_annotated_add_r_42 == r_42.annotate("42") + r_42
        assert r_42_annotated_add_r_42_annotated == r_42_annotated + r_42.annotate("42")
        assert r_42_add_r_42 != r_42_add_r_42_annotated
        assert r_42_add_r_42 != r_42_annotated_add_r_42
        assert r_42_add_r_42 != r_42_annotated_add_r_42_annotated
        assert r_42_add_r_42 != r_42_mul_r_42
        assert r_42_add_r_42_annotated != r_42_mul_r_42_annotated
        assert r_42_annotated_add_r_42 != r_42_annotated_mul_r_42

    def test_op_add(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                one_add_r = 1 + r
                assert one_add_r.bin_op == operator.__add__
                left, right = one_add_r.sources
                assert left == ValueRoller(1)
                assert right == r
                assert tuple(one_add_r.roll().outcomes()) == (1 + o,), one_add_r

                r_add_one = r + 1
                assert r_add_one.bin_op == operator.__add__
                left, right = r_add_one.sources
                assert left == r
                assert right == ValueRoller(1)
                assert tuple(r_add_one.roll().outcomes()) == (o + 1,), r_add_one

    def test_op_sub(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                one_sub_r = 1 - r
                assert one_sub_r.bin_op == operator.__sub__
                left, right = one_sub_r.sources
                assert left == ValueRoller(1)
                assert right == r
                assert tuple(one_sub_r.roll().outcomes()) == (1 - o,), one_sub_r

                r_sub_one = r - 1
                assert r_sub_one.bin_op == operator.__sub__
                left, right = r_sub_one.sources
                assert left == r
                assert right == ValueRoller(1)
                assert tuple(r_sub_one.roll().outcomes()) == (o - 1,), r_sub_one

    def test_op_mul(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_mul_r = 2 * r
                assert two_mul_r.bin_op == operator.__mul__
                left, right = two_mul_r.sources
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_mul_r.roll().outcomes()) == (2 * o,), two_mul_r

                r_mul_two = r * 2
                assert r_mul_two.bin_op == operator.__mul__
                left, right = r_mul_two.sources
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_mul_two.roll().outcomes()) == (o * 2,), r_mul_two

    def test_op_truediv(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                if v == 0:
                    continue

                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_truediv_r = 2 / r
                assert two_truediv_r.bin_op == operator.__truediv__
                left, right = two_truediv_r.sources
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_truediv_r.roll().outcomes()) == (2 / o,), two_truediv_r

                r_truediv_two = r / 2
                assert r_truediv_two.bin_op == operator.__truediv__
                left, right = r_truediv_two.sources
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_truediv_two.roll().outcomes()) == (o / 2,), r_truediv_two

    def test_op_floordiv(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                if v == 0:
                    continue

                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_floordiv_r = 2 // r
                assert two_floordiv_r.bin_op == operator.__floordiv__
                left, right = two_floordiv_r.sources
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_floordiv_r.roll().outcomes()) == (
                    2 // o,
                ), two_floordiv_r

                r_floordiv_two = r // 2
                assert r_floordiv_two.bin_op == operator.__floordiv__
                left, right = r_floordiv_two.sources
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_floordiv_two.roll().outcomes()) == (
                    o // 2,
                ), r_floordiv_two

    def test_op_mod(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                if v == 0:
                    continue

                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_mod_r = 2 % r
                assert two_mod_r.bin_op == operator.__mod__
                left, right = two_mod_r.sources
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_mod_r.roll().outcomes()) == (2 % o,), two_mod_r

                r_mod_two = r % 2
                assert r_mod_two.bin_op == operator.__mod__
                left, right = r_mod_two.sources
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_mod_two.roll().outcomes()) == (o % 2,), r_mod_two

    def test_op_pow(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(4, 0, -1):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_pow_r = 2**r
                assert two_pow_r.bin_op == operator.__pow__
                left, right = two_pow_r.sources
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_pow_r.roll().outcomes()) == (2**o,), two_pow_r

                r_pow_two = r**2
                assert r_pow_two.bin_op == operator.__pow__
                left, right = r_pow_two.sources
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_pow_two.roll().outcomes()) == (o**2,), r_pow_two

    def test_op_and(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_and_r = 0xA5 & r
                assert a5_and_r.bin_op == operator.__and__
                left, right = a5_and_r.sources
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_and_r.roll().outcomes()) == (0xA5 & o,), a5_and_r

                r_and_a5 = r & 0xA5
                assert r_and_a5.bin_op == operator.__and__
                left, right = r_and_a5.sources
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_and_a5.roll().outcomes()) == (o & 0xA5,), r_and_a5

    def test_op_xor(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_xor_r = 0xA5 ^ r
                assert a5_xor_r.bin_op == operator.__xor__
                left, right = a5_xor_r.sources
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_xor_r.roll().outcomes()) == (0xA5 ^ o,), a5_xor_r

                r_xor_a5 = r ^ 0xA5
                assert r_xor_a5.bin_op == operator.__xor__
                left, right = r_xor_a5.sources
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_xor_a5.roll().outcomes()) == (o ^ 0xA5,), r_xor_a5

    def test_op_or(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_or_r = 0xA5 | r
                assert a5_or_r.bin_op == operator.__or__
                left, right = a5_or_r.sources
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_or_r.roll().outcomes()) == (0xA5 | o,), a5_or_r

                r_or_a5 = r | 0xA5
                assert r_or_a5.bin_op == operator.__or__
                left, right = r_or_a5.sources
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_or_a5.roll().outcomes()) == (o | 0xA5,), r_or_a5

    def _test_cmp_op_helper(
        self,
        op_name: str,
    ) -> None:
        import operator

        __op__ = getattr(operator, f"__{op_name}__")

        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")
                r_do_op = getattr(r, op_name)
                r_op_r = r_do_op(r)
                left_source, right_source = r_op_r.sources
                assert left_source == r
                assert right_source == r
                assert tuple(r_op_r.roll().outcomes()) == (bool(__op__(o, o)),), r_op_r

                r_neg = -r
                r_op_r_neg = r_do_op(r_neg)
                left_source, right_source = r_op_r_neg.sources
                assert left_source == r
                assert right_source == r_neg
                assert tuple(r_op_r_neg.roll().outcomes()) == (
                    bool(__op__(o, -o)),
                ), r_op_r_neg

    def test_cmp_lt(self) -> None:
        self._test_cmp_op_helper(op_name="lt")

    def test_cmp_le(self) -> None:
        self._test_cmp_op_helper(op_name="le")

    def test_cmp_eq(self) -> None:
        self._test_cmp_op_helper(op_name="eq")

    def test_cmp_ne(self) -> None:
        self._test_cmp_op_helper(op_name="ne")

    def test_cmp_gt(self) -> None:
        self._test_cmp_op_helper(op_name="gt")

    def test_cmp_ge(self) -> None:
        self._test_cmp_op_helper(op_name="ge")

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(v) for v in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            h_mul_h = h * h
            r_mul_r = r * r

            for _ in range(10):
                r_mul_r_roll = r_mul_r.roll()
                (roll_outcome,) = r_mul_r_roll
                assert roll_outcome.r == r_mul_r
                assert roll_outcome.value is not None
                assert roll_outcome.value in h_mul_h
                assert r_mul_r_roll.total() in h_mul_h, r_mul_r

                for o in h:
                    h_mul_o = h * o_type(o)
                    r_mul_o = r * o_type(o)
                    r_mul_o_roll = r_mul_o.roll()
                    (roll_outcome,) = r_mul_o_roll
                    assert roll_outcome.r == r_mul_o
                    assert roll_outcome.value is not None
                    assert roll_outcome.value in h_mul_o
                    assert r_mul_o_roll.total() in h_mul_o, r_mul_o


class TestUnarySumOpRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_neg = -r_42
        assert (
            repr(r_42_neg)
            == """UnarySumOpRoller(
  un_op=<built-in function neg>,
  source=ValueRoller(value=42, annotation=''),
  annotation='',
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_neg = -r_d6
        assert (
            repr(r_d6_neg)
            == """UnarySumOpRoller(
  un_op=<built-in function neg>,
  source=ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation='d6'),
  annotation='',
)"""
        )

    def test_op_eq(self) -> None:
        r_42 = R.from_value(42)
        r_42_annotated = r_42.annotate("42")
        r_42_pos = +r_42
        r_42_annotated_pos = +r_42_annotated
        r_42_abs = abs(r_42)
        r_42_annotated_abs = abs(r_42_annotated)
        assert r_42_pos == +r_42
        assert r_42_annotated_pos == +r_42.annotate("42")
        assert r_42_pos != r_42_annotated_pos
        assert r_42_pos != r_42_abs
        assert r_42_annotated_pos != r_42_annotated_abs

    def test_op_neg(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_neg = -r
                assert r_neg.un_op == operator.__neg__
                (source,) = r_neg.sources
                assert source == r, r_neg
                assert tuple(r_neg.roll().outcomes()) == (-o,), r_neg

    def test_op_pos(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_pos = +r
                assert r_pos.un_op == operator.__pos__
                (source,) = r_pos.sources
                assert source == r, r_pos
                assert tuple(r_pos.roll().outcomes()) == (+o,), r_pos

    def test_op_abs(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_abs = abs(r)
                assert r_abs.un_op == operator.__abs__
                (source,) = r_abs.sources
                assert source == r, r_abs
                assert tuple(r_abs.roll().outcomes()) == (abs(o),), r_abs

    def test_op_invert(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_inv = ~r
                assert r_inv.un_op == operator.__invert__
                (source,) = r_inv.sources
                assert source == r, r_inv
                assert tuple(r_inv.roll().outcomes()) == (~o,), r_inv

    def test_even(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_even = r.is_even()
                assert r_even.un_op.__name__ == "_is_even"
                (source,) = r_even.sources
                assert source == r, r_even
                assert tuple(r_even.roll().outcomes()) == (o_type(o) % 2 == 0,), r_even

    def test_odd(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_odd = r.is_odd()
                assert r_odd.un_op.__name__ == "_is_odd"
                (source,) = r_odd.sources
                assert source == r, r_odd
                assert tuple(r_odd.roll().outcomes()) == (o_type(o) % 2 != 0,), r_odd

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(v) for v in range(-2, 3))
            h_neg = -h
            r = R.from_value(h, annotation=f"{o_type}")
            r_neg = -r

            for _ in range(10):
                r_neg_roll = r_neg.roll()
                (roll_outcome,) = r_neg_roll
                assert roll_outcome.r == r_neg
                assert r_neg_roll.total() in h_neg, r_neg


class TestPoolRoller:
    def test_repr(self) -> None:
        r_4_6_8 = R.from_values(4, 6, 8)
        assert (
            repr(r_4_6_8)
            == """PoolRoller(
  sources=(
    ValueRoller(value=4, annotation=''),
    ValueRoller(value=6, annotation=''),
    ValueRoller(value=8, annotation=''),
  ),
  annotation='',
)"""
        )

        r_d4_d6_d8 = R.from_values(H(4), H(6), H(8), annotation="d4d6d8")
        assert (
            repr(r_d4_d6_d8)
            == """PoolRoller(
  sources=(
    ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1}), annotation=''),
    ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), annotation=''),
    ValueRoller(value=H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}), annotation=''),
  ),
  annotation='d4d6d8',
)"""
        )

    def test_op_eq(self) -> None:
        r_4_6_8 = R.from_values(4, 6, 8)
        assert isinstance(r_4_6_8, PoolRoller)
        r_4_6_8_annotated = r_4_6_8.annotate("4-6-8")
        assert r_4_6_8 == R.from_values(4, 6, 8)
        assert r_4_6_8 != r_4_6_8_annotated
        assert r_4_6_8_annotated == R.from_values(4, 6, 8, annotation="4-6-8")

    def test_getitem(self) -> None:
        r_d4_d6_d8 = R.from_values(H(4), H(6), H(8))
        assert len(r_d4_d6_d8.sources) == 3, r_d4_d6_d8
        assert isinstance(r_d4_d6_d8.sources[0], ValueRoller)
        assert r_d4_d6_d8.sources[0].value == H(4)
        assert isinstance(r_d4_d6_d8.sources[1], ValueRoller)
        assert r_d4_d6_d8.sources[1].value == H(6)
        assert isinstance(r_d4_d6_d8.sources[2], ValueRoller)
        assert r_d4_d6_d8.sources[2].value == H(8)

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(v) for v in range(-2, 3))
            h_3 = 3 @ h
            r = R.from_value(h, annotation=f"{o_type}")
            r_3 = R.from_sources(r, r, r)

            for _ in range(10):
                r_3_roll = r_3.roll()
                assert len(r_3_roll) == 3, r_3_roll

                for roll_outcome in r_3_roll:
                    assert roll_outcome.r == r

                assert r_3_roll.total() in h_3, r_3_roll


class TestFilterRoller:
    def test_repr(self) -> None:
        def evens_filter(outcome: RollOutcome) -> bool:
            return bool(outcome.is_even().value)

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_filter = r_squares.filter(evens_filter)
        pattern = (
            re.escape(
                """FilterRoller(
  predicate=<function TestFilterRoller.test_repr.<locals>.evens_filter at """
            )
            + r"(?:0x)?([0-9A-Fa-f]+)"
            + re.escape(
                """>,
  sources=(
    PoolRoller(
      sources=(
        ValueRoller(value=36, annotation=''),
        ValueRoller(value=25, annotation=''),
        ValueRoller(value=16, annotation=''),
        ValueRoller(value=9, annotation=''),
        ValueRoller(value=4, annotation=''),
        ValueRoller(value=1, annotation=''),
      ),
      annotation='',
    ),
  ),
  annotation='',
)"""
            )
        )
        assert re.search(
            pattern,
            repr(r_squares_filter),
        )

    def test_op_eq(self) -> None:
        def evens_filter(outcome: RollOutcome) -> bool:
            return bool(outcome.is_even().value)

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_filter = r_squares.filter(evens_filter)
        r_squares_filter_annotated = r_squares_filter.annotate("even squares")
        assert r_squares_filter == r_squares.filter(evens_filter)
        assert r_squares_filter != r_squares_filter_annotated
        assert r_squares_filter_annotated == r_squares_filter.annotate("even squares")

    def test_roll(self) -> None:
        def evens_filter(outcome: RollOutcome) -> bool:
            return bool(outcome.is_even().value)

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_filter = r_squares.filter(evens_filter)
        r_squares_filter_roll = r_squares_filter.roll()
        assert tuple(r_squares_filter_roll.outcomes()) == (36, 16, 4)

        for roll_outcome in r_squares_filter_roll:
            if roll_outcome.value is None:
                assert roll_outcome.r is r_squares_filter
            else:
                assert roll_outcome.r in r_squares.sources


class TestSelectionRoller:
    def test_repr(self) -> None:
        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_select = r_squares.select(0, -1)
        assert (
            repr(r_squares_select)
            == """SelectionRoller(
  which=(0, -1),
  sources=(
    PoolRoller(
      sources=(
        ValueRoller(value=36, annotation=''),
        ValueRoller(value=25, annotation=''),
        ValueRoller(value=16, annotation=''),
        ValueRoller(value=9, annotation=''),
        ValueRoller(value=4, annotation=''),
        ValueRoller(value=1, annotation=''),
      ),
      annotation='',
    ),
  ),
  annotation='',
)"""
        )

    def test_op_eq(self) -> None:
        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_select = r_squares.select(0, -1, 1, -2)
        r_squares_select_annotated = r_squares_select.annotate("0, -1, 1, 2")
        assert r_squares_select == r_squares.select(0, -1, 1, -2)
        assert r_squares_select != r_squares_select_annotated
        assert r_squares_select_annotated == r_squares_select.annotate("0, -1, 1, 2")

    def test_roll(self) -> None:
        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_squares_select = r_squares.select(0, -1, 1, -2)
        r_squares_select_roll = r_squares_select.roll()
        assert tuple(r_squares_select_roll.outcomes()) == (1, 36, 4, 25)

        for roll_outcome in r_squares_select_roll:
            if roll_outcome.value is None:
                assert roll_outcome.r is r_squares_select
            else:
                assert roll_outcome.r in r_squares.sources


class TestSubstitutionRoller:
    def test_repr(self) -> None:
        def odd_doubler(outcome: RollOutcome) -> RollOutcome:
            return outcome * 2 if bool(outcome.is_odd().value) else outcome

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_double_odd_squares = SubstitutionRoller(odd_doubler, r_squares)
        pattern = (
            re.escape(
                """SubstitutionRoller(
  expansion_op=<function TestSubstitutionRoller.test_repr.<locals>.odd_doubler at """
            )
            + r"(?:0x)?([0-9A-Fa-f]+)"
            + re.escape(
                """>,
  source=PoolRoller(
    sources=(
      ValueRoller(value=36, annotation=''),
      ValueRoller(value=25, annotation=''),
      ValueRoller(value=16, annotation=''),
      ValueRoller(value=9, annotation=''),
      ValueRoller(value=4, annotation=''),
      ValueRoller(value=1, annotation=''),
    ),
    annotation='',
  ),
  coalesce_mode=<CoalesceMode.REPLACE: 1>,
  max_depth=1,
  annotation='',
)"""
            )
        )
        assert re.search(
            pattern,
            repr(r_double_odd_squares),
        )

    def test_op_eq(self) -> None:
        def odd_doubler(outcome: RollOutcome) -> RollOutcome:
            return outcome * 2 if bool(outcome.is_odd().value) else outcome

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_double_odd_squares = SubstitutionRoller(odd_doubler, r_squares)
        r_double_odd_squares_annotated = r_double_odd_squares.annotate(
            "doubled odd squares"
        )
        assert r_double_odd_squares == SubstitutionRoller(odd_doubler, r_squares)
        assert r_double_odd_squares != r_double_odd_squares_annotated
        assert r_double_odd_squares_annotated == r_double_odd_squares.annotate(
            "doubled odd squares"
        )

    def test_roll(self) -> None:
        def odd_doubler(outcome: RollOutcome) -> RollOutcome:
            return outcome * 2 if bool(outcome.is_odd().value) else outcome

        r_squares = R.from_values_iterable(v**2 for v in range(6, 0, -1))
        r_double_odd_squares = SubstitutionRoller(odd_doubler, r_squares)
        r_double_odd_squares_roll = r_double_odd_squares.roll()
        assert tuple(r_double_odd_squares_roll.outcomes()) == (36, 50, 16, 18, 4, 2)


class TestRoll:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_neg = -r_42
        r_42_neg_roll = r_42_neg.roll()
        assert (
            repr(r_42_neg_roll)
            == """Roll(
  r=UnarySumOpRoller(
    un_op=<built-in function neg>,
    source=ValueRoller(value=42, annotation=''),
    annotation='',
  ),
  roll_outcomes=(
    RollOutcome(
      value=-42,
      sources=(
        RollOutcome(
          value=42,
          sources=(),
        ),
      ),
    ),
  ),
  source_rolls=(
    Roll(
      r=ValueRoller(value=42, annotation=''),
      roll_outcomes=(
        RollOutcome(
          value=42,
          sources=(),
        ),
      ),
      source_rolls=(),
    ),
  ),
)"""
        )

    def test_getitem(self) -> None:
        r_123 = R.from_values(1, 2, 3)
        r_123_roll = r_123.roll()
        assert len(r_123_roll) == 3, r_123_roll
        assert (
            r_123_roll[:]
            == tuple(r_123_roll[i] for i in range(len(r_123_roll)))
            == tuple(r_123_roll)
        )

    def test_adopt_append(self) -> None:
        r_567 = R.from_values(1, 2, 3) + 4
        roll = r_567.roll()
        one = RollOutcome(1)
        assert not any(one in roll_outcome.sources for roll_outcome in roll)

        adopted_roll = roll.adopt((one,), CoalesceMode.APPEND)

        for roll_outcome in adopted_roll:
            assert len(roll_outcome.sources) > 1
            assert one in roll_outcome.sources

    def test_adopt_replace(self) -> None:
        r_567 = R.from_values(1, 2, 3) + 4
        roll = r_567.roll()
        one = RollOutcome(1)
        assert not any(one in roll_outcome.sources for roll_outcome in roll)

        adopted_roll = roll.adopt((one,), CoalesceMode.REPLACE)

        for roll_outcome in adopted_roll:
            assert len(roll_outcome.sources) == 1
            assert one in roll_outcome.sources

    def test_hierarchy(self) -> None:
        d6 = H(6)
        r_d6 = R.from_value(d6)
        d6_mul2 = 2 * d6
        r_d6_mul2 = 2 * r_d6
        d6_mul2_neg = -d6_mul2
        r_d6_mul2_neg = -r_d6_mul2
        d6_mul2_neg_add4 = d6_mul2_neg + 4
        r_d6_mul2_neg_add4 = r_d6_mul2_neg + 4
        d6_mul2_neg_add4_3 = 3 @ d6_mul2_neg_add4
        r_d6_mul2_neg_add4_3 = 3 @ r_d6_mul2_neg_add4

        r_d6_mul2_neg_add4_3_roll = r_d6_mul2_neg_add4_3.roll()
        assert r_d6_mul2_neg_add4_3_roll.total() in d6_mul2_neg_add4_3
        assert len(r_d6_mul2_neg_add4_3_roll) == 3, r_d6_mul2_neg_add4_3_roll

        for r_d6_mul2_neg_add4_roll in r_d6_mul2_neg_add4_3_roll.source_rolls:
            (r_d6_mul2_neg_add4_ro,) = r_d6_mul2_neg_add4_roll
            assert r_d6_mul2_neg_add4_ro.value is not None
            assert r_d6_mul2_neg_add4_ro.value in d6_mul2_neg_add4

            (r_d6_mul2_neg_roll, _) = r_d6_mul2_neg_add4_roll.source_rolls
            (r_d6_mul2_neg_ro,) = r_d6_mul2_neg_roll
            assert r_d6_mul2_neg_ro.value is not None
            assert r_d6_mul2_neg_ro.value in d6_mul2_neg

            (r_d6_mul2_roll,) = r_d6_mul2_neg_roll.source_rolls
            (r_d6_mul2_ro,) = r_d6_mul2_roll
            assert r_d6_mul2_ro.value is not None
            assert r_d6_mul2_ro.value in d6_mul2

            (r_d6_roll, _) = r_d6_mul2_roll.source_rolls
            (r_d6_ro,) = r_d6_roll
            assert r_d6_ro.value is not None
            assert r_d6_ro.value in d6

        for r_d6_mul2_neg_add4_3_ro in r_d6_mul2_neg_add4_3_roll:
            assert r_d6_mul2_neg_add4_3_ro.r == r_d6_mul2_neg_add4

            (r_d6_mul2_neg_ro, _) = r_d6_mul2_neg_add4_3_ro.sources
            assert r_d6_mul2_neg_ro.r == r_d6_mul2_neg

            (r_d6_mul2_ro,) = r_d6_mul2_neg_ro.sources
            assert r_d6_mul2_ro.r == r_d6_mul2

            (_, r_d6_ro) = r_d6_mul2_ro.sources
            assert r_d6_ro.r == r_d6


class TestRollOutcome:
    def test_is_even(self) -> None:
        six = RollOutcome(6)
        six_even = six.is_even()
        assert six_even.value is True
        assert six_even.sources == (six,)

    def test_is_odd(self) -> None:
        six = RollOutcome(6)
        six_odd = six.is_odd()
        assert six_odd.value is False
        assert six_odd.sources == (six,)

    def test_adopt_append(self) -> None:
        six = RollOutcome(6)
        four_from_six = RollOutcome(4, sources=(six,))
        five = RollOutcome(5)
        four_from_six_five = four_from_six.adopt(
            sources=(five,),
            coalesce_mode=CoalesceMode.APPEND,
        )
        assert four_from_six_five.value == four_from_six.value
        assert four_from_six_five.sources == (six, five)

    def test_adopt_replace(self) -> None:
        six = RollOutcome(6)
        four_from_six = RollOutcome(4, sources=(six,))
        five = RollOutcome(5)
        four_from_five = four_from_six.adopt(
            sources=(five,),
            coalesce_mode=CoalesceMode.REPLACE,
        )
        assert four_from_five.value == four_from_six.value
        assert four_from_five.sources == (five,)

    def test_euthanize(self) -> None:
        six = RollOutcome(6)
        rip_six = six.euthanize()
        assert rip_six.value is None
        assert rip_six.sources == (six,)

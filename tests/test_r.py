# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import operator

from dyce import H, P, R
from dyce.r import ValueRoller

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
        assert repr(R.from_value(42)) == "ValueRoller(value=42, annotation=None)"
        assert (
            repr(R.from_value(H(6), annotation={"one": 1}))
            == "ValueRoller(value=H(6), annotation={'one': 1})"
        )
        assert (
            repr(R.from_value(3 @ P(6), annotation={"two": 2}))
            == "ValueRoller(value=P(6, 6, 6), annotation={'two': 2})"
        )

    def test_op_eq(self) -> None:
        r_42 = R.from_value(42)
        r_42_annotated = R.from_value(42, annotation="42")
        assert r_42 == r_42
        assert r_42 != r_42_annotated
        assert r_42_annotated == r_42_annotated

        assert r_42 != -r_42
        assert -r_42 == -r_42
        assert -r_42 != R.from_value(-42)

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")

            for _ in range(1000):
                r_roll = r.roll()
                assert r_roll.r == r
                assert r_roll.total in h, r


class TestBinaryOperationRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_squared = r_42 * r_42
        assert (
            repr(r_42_squared)
            == """BinaryOperationRoller(
  op=<built-in function mul>,
  left_child=ValueRoller(value=42, annotation=None),
  right_child=ValueRoller(value=42, annotation=None),
  annotation=None,
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_2 = r_d6 + r_d6
        assert (
            repr(r_d6_2)
            == """BinaryOperationRoller(
  op=<built-in function add>,
  left_child=ValueRoller(value=H(6), annotation='d6'),
  right_child=ValueRoller(value=H(6), annotation='d6'),
  annotation=None,
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
                assert one_add_r.op == operator.__add__
                left, right = one_add_r.children
                assert left == ValueRoller(1)
                assert right == r
                assert tuple(one_add_r.roll().outcomes()) == (1 + o,), one_add_r

                r_add_one = r + 1
                assert r_add_one.op == operator.__add__
                left, right = r_add_one.children
                assert left == r
                assert right == ValueRoller(1)
                assert tuple(r_add_one.roll().outcomes()) == (o + 1,), r_add_one

    def test_op_sub(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                one_sub_r = 1 - r
                assert one_sub_r.op == operator.__sub__
                left, right = one_sub_r.children
                assert left == ValueRoller(1)
                assert right == r
                assert tuple(one_sub_r.roll().outcomes()) == (1 - o,), one_sub_r

                r_sub_one = r - 1
                assert r_sub_one.op == operator.__sub__
                left, right = r_sub_one.children
                assert left == r
                assert right == ValueRoller(1)
                assert tuple(r_sub_one.roll().outcomes()) == (o - 1,), r_sub_one

    def test_op_mul(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_mul_r = 2 * r
                assert two_mul_r.op == operator.__mul__
                left, right = two_mul_r.children
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_mul_r.roll().outcomes()) == (2 * o,), two_mul_r

                r_mul_two = r * 2
                assert r_mul_two.op == operator.__mul__
                left, right = r_mul_two.children
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
                assert two_truediv_r.op == operator.__truediv__
                left, right = two_truediv_r.children
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_truediv_r.roll().outcomes()) == (2 / o,), two_truediv_r

                r_truediv_two = r / 2
                assert r_truediv_two.op == operator.__truediv__
                left, right = r_truediv_two.children
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
                assert two_floordiv_r.op == operator.__floordiv__
                left, right = two_floordiv_r.children
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_floordiv_r.roll().outcomes()) == 2 // o, two_floordiv_r

                r_floordiv_two = r // 2
                assert r_floordiv_two.op == operator.__floordiv__
                left, right = r_floordiv_two.children
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_floordiv_two.roll().outcomes()) == o // 2, r_floordiv_two

    def test_op_mod(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                if v == 0:
                    continue

                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_mod_r = 2 % r
                assert two_mod_r.op == operator.__mod__
                left, right = two_mod_r.children
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_mod_r.roll().outcomes()) == (2 % o,), two_mod_r

                r_mod_two = r % 2
                assert r_mod_two.op == operator.__mod__
                left, right = r_mod_two.children
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_mod_two.roll().outcomes()) == (o % 2,), r_mod_two

    def test_op_pow(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(4, 0, -1):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                two_pow_r = 2 ** r
                assert two_pow_r.op == operator.__pow__
                left, right = two_pow_r.children
                assert left == ValueRoller(2)
                assert right == r
                assert tuple(two_pow_r.roll().outcomes()) == (2 ** o,), two_pow_r

                r_pow_two = r ** 2
                assert r_pow_two.op == operator.__pow__
                left, right = r_pow_two.children
                assert left == r
                assert right == ValueRoller(2)
                assert tuple(r_pow_two.roll().outcomes()) == (o ** 2,), r_pow_two

    def test_op_and(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_and_r = 0xA5 & r
                assert a5_and_r.op == operator.__and__
                left, right = a5_and_r.children
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_and_r.roll().outcomes()) == (0xA5 & o,), a5_and_r

                r_and_a5 = r & 0xA5
                assert r_and_a5.op == operator.__and__
                left, right = r_and_a5.children
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_and_a5.roll().outcomes()) == (o & 0xA5,), r_and_a5

    def test_op_xor(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_xor_r = 0xA5 ^ r
                assert a5_xor_r.op == operator.__xor__
                left, right = a5_xor_r.children
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_xor_r.roll().outcomes()) == (0xA5 ^ o,), a5_xor_r

                r_xor_a5 = r ^ 0xA5
                assert r_xor_a5.op == operator.__xor__
                left, right = r_xor_a5.children
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_xor_a5.roll().outcomes()) == (o ^ 0xA5,), r_xor_a5

    def test_op_or(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o, annotation=f"{o_type}({v})")

                a5_or_r = 0xA5 | r
                assert a5_or_r.op == operator.__or__
                left, right = a5_or_r.children
                assert left == ValueRoller(0xA5)
                assert right == r
                assert tuple(a5_or_r.roll().outcomes()) == (0xA5 | o,), a5_or_r

                r_or_a5 = r | 0xA5
                assert r_or_a5.op == operator.__or__
                left, right = r_or_a5.children
                assert left == r
                assert right == ValueRoller(0xA5)
                assert tuple(r_or_a5.roll().outcomes()) == (o | 0xA5,), r_or_a5

    def _test_cmp_op(
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
                left_child, right_child = r_op_r.children
                assert left_child == r
                assert right_child == r
                assert tuple(r_op_r.roll().outcomes()) == (bool(__op__(o, o)),), r_op_r

                r_neg = -r
                r_op_r_neg = r_do_op(r_neg)
                left_child, right_child = r_op_r_neg.children
                assert left_child == r
                assert right_child == r_neg
                assert tuple(r_op_r_neg.roll().outcomes()) == (
                    bool(__op__(o, -o)),
                ), r_op_r_neg

    def test_cmp_lt(self) -> None:
        self._test_cmp_op(op_name="lt")

    def test_cmp_le(self) -> None:
        self._test_cmp_op(op_name="le")

    def test_cmp_eq(self) -> None:
        self._test_cmp_op(op_name="eq")

    def test_cmp_ne(self) -> None:
        self._test_cmp_op(op_name="ne")

    def test_cmp_gt(self) -> None:
        self._test_cmp_op(op_name="gt")

    def test_cmp_ge(self) -> None:
        self._test_cmp_op(op_name="ge")

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            h_mul_h = h * h
            r = R.from_value(h, annotation=f"{o_type}")
            r_mul_r = r * r

            for _ in range(1000):
                r_mul_r_roll = r_mul_r.roll()
                assert r_mul_r_roll.r == r_mul_r
                assert r_mul_r_roll.total in h_mul_h, r_mul_r


class TestUnaryOperationRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_neg = -r_42
        assert (
            repr(r_42_neg)
            == """UnaryOperationRoller(
  op=<built-in function neg>,
  child=ValueRoller(value=42, annotation=None),
  annotation=None,
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_neg = -r_d6
        assert (
            repr(r_d6_neg)
            == """UnaryOperationRoller(
  op=<built-in function neg>,
  child=ValueRoller(value=H(6), annotation='d6'),
  annotation=None,
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
                (child,) = r_neg.children
                assert child == r, r_neg
                assert tuple(r_neg.roll().outcomes()) == (-o,), r_neg

    def test_op_pos(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_pos = +r
                (child,) = r_pos.children
                assert child == r, r_pos
                assert tuple(r_pos.roll().outcomes()) == (+o,), r_pos

    def test_op_abs(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_abs = abs(r)
                (child,) = r_abs.children
                assert child == r, r_abs
                assert tuple(r_abs.roll().outcomes()) == (abs(o),), r_abs

    def test_even(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_even = r.is_even()
                (child,) = r_even.children
                assert child == r, r_even
                assert tuple(r_even.roll().outcomes()) == (o_type(o) % 2 == 0,), r_even

    def test_odd(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_odd = r.is_odd()
                (child,) = r_odd.children
                assert child == r, r_odd
                assert tuple(r_odd.roll().outcomes()) == (o_type(o) % 2 != 0,), r_odd

    def test_inverse(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for v in range(-2, 3):
                o = o_type(v)
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_inv = ~r
                (child,) = r_inv.children
                assert child == r, r_inv
                assert tuple(r_inv.roll().outcomes()) == (~o,), r_inv

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            h_neg = -h
            r = R.from_value(h, annotation=f"{o_type}")
            r_neg = -r

            for _ in range(1000):
                r_neg_roll = r_neg.roll()
                assert r_neg_roll.r == r_neg
                assert r_neg_roll.total in h_neg, r_neg


class TestRepeatRoller:
    def test_repr(self) -> None:
        r_42 = R.from_value(42)
        r_42_3 = r_42 @ 3
        assert (
            repr(r_42_3)
            == """RepeatRoller(
  n=3,
  child=ValueRoller(value=42, annotation=None),
  annotation=None,
)"""
        )

        r_d6 = R.from_value(H(6), annotation="d6")
        r_d6_2 = 2 @ r_d6
        assert (
            repr(r_d6_2)
            == """RepeatRoller(
  n=2,
  child=ValueRoller(value=H(6), annotation='d6'),
  annotation=None,
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
                h = H(o_type(o) for o in range(-2, 3))
                r = R.from_value(h, annotation=f"{o_type}")
                r_1000 = (i_type(1000) @ r).annotate(f"{i_type}")
                r_1000_roll = r_1000.roll()
                assert len(r_1000_roll) == 1000

                for outcome in r_1000_roll.outcomes():
                    assert outcome in h, r_1000_roll


class TestPoolRoller:
    def test_repr(self) -> None:
        r_4_6_8 = R.from_rs_iterable(R.from_value(i) for i in (4, 6, 8))
        assert (
            repr(r_4_6_8)
            == """PoolRoller(
  children=(
    ValueRoller(value=4, annotation=None),
    ValueRoller(value=6, annotation=None),
    ValueRoller(value=8, annotation=None),
  ),
  annotation=None,
)"""
        )

        r_d4_d6_d8 = R.from_values(H(4), H(6), H(8), annotation="d4d6d8")
        assert (
            repr(r_d4_d6_d8)
            == """PoolRoller(
  children=(
    ValueRoller(value=H(4), annotation=None),
    ValueRoller(value=H(6), annotation=None),
    ValueRoller(value=H(8), annotation=None),
  ),
  annotation='d4d6d8',
)"""
        )

    def test_op_eq(self) -> None:
        r_4_6_8 = R.from_rs_iterable(R.from_value(i) for i in (4, 6, 8))
        r_4_6_8_annotated = r_4_6_8.annotate("4-6-8")
        assert r_4_6_8 == r_4_6_8
        assert r_4_6_8 != r_4_6_8_annotated
        assert r_4_6_8_annotated == r_4_6_8.annotate("4-6-8")

    def test_getitem(self) -> None:
        r_d4_d6_d8 = R.from_values(H(4), H(6), H(8))
        assert len(r_d4_d6_d8) == 3
        assert isinstance(r_d4_d6_d8[0], ValueRoller)
        assert r_d4_d6_d8[0].value == H(4)
        assert isinstance(r_d4_d6_d8[1], ValueRoller)
        assert r_d4_d6_d8[1].value == H(6)
        assert isinstance(r_d4_d6_d8[2], ValueRoller)
        assert r_d4_d6_d8[2].value == H(8)

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            h_3 = 3 @ h
            r = R.from_value(h, annotation=f"{o_type}")
            r_3 = R.from_rs(r, r, r)

            for _ in range(1000):
                r_3_roll = r_3.roll()
                assert r_3_roll.r == r_3
                assert r_3_roll.total in h_3, r_3_roll


class TestRoll:
    def test_hierarchy(self) -> None:
        d6 = H(6)
        r_d6 = R.from_value(d6)
        d6_mul_2 = d6 * 2
        r_d6_mul_2 = r_d6 * 2
        d6_mul_2_neg = -d6_mul_2
        r_d6_mul_2_neg = -r_d6_mul_2
        d6_mul_2_neg_add_4 = d6_mul_2_neg + 4
        r_d6_mul_2_neg_add_4 = r_d6_mul_2_neg + 4
        d6_mul_2_neg_add_4_3 = 3 @ d6_mul_2_neg_add_4
        r_d6_mul_2_neg_add_4_3 = 3 @ r_d6_mul_2_neg_add_4

        r_d6_mul_2_neg_add_4_3_roll = r_d6_mul_2_neg_add_4_3.roll()
        assert r_d6_mul_2_neg_add_4_3_roll.total in d6_mul_2_neg_add_4_3

        assert (
            r_d6_mul_2_neg_add_4_3_roll.r == r_d6_mul_2_neg_add_4_3
        ), r_d6_mul_2_neg_add_4_3_roll
        assert len(r_d6_mul_2_neg_add_4_3_roll) == 3, r_d6_mul_2_neg_add_4_3_roll
        assert all(
            outcome in d6_mul_2_neg_add_4
            for outcome in r_d6_mul_2_neg_add_4_3_roll.outcomes()
        ), r_d6_mul_2_neg_add_4_3_roll

        for _, n_rolls in r_d6_mul_2_neg_add_4_3_roll:
            assert len(n_rolls) == 1
            (r_d6_mul_2_neg_add_4_roll,) = n_rolls
            assert r_d6_mul_2_neg_add_4_roll.r == r_d6_mul_2_neg_add_4
            assert len(r_d6_mul_2_neg_add_4_roll) == 1, r_d6_mul_2_neg_add_4_roll
            assert all(
                outcome in d6_mul_2_neg_add_4
                for outcome in r_d6_mul_2_neg_add_4_roll.outcomes()
            ), r_d6_mul_2_neg_add_4_roll

            ((_, add_rolls),) = tuple(r_d6_mul_2_neg_add_4_roll)
            assert len(add_rolls) == 2
            r_d6_mul_2_neg_roll, _ = add_rolls  # look at the left side
            assert r_d6_mul_2_neg_roll.r == r_d6_mul_2_neg, r_d6_mul_2_neg_roll
            assert len(r_d6_mul_2_neg_roll) == 1, r_d6_mul_2_neg_roll
            assert all(
                outcome in d6_mul_2_neg for outcome in r_d6_mul_2_neg_roll.outcomes()
            ), r_d6_mul_2_neg_roll

            ((_, neg_rolls),) = tuple(r_d6_mul_2_neg_roll)
            assert len(neg_rolls) == 1
            (r_d6_mul_2_roll,) = neg_rolls
            assert r_d6_mul_2_roll.r == r_d6_mul_2, r_d6_mul_2_roll
            assert len(r_d6_mul_2_roll) == 1, r_d6_mul_2_roll
            assert all(
                outcome in d6_mul_2 for outcome in r_d6_mul_2_roll.outcomes()
            ), r_d6_mul_2_roll

            ((_, mul_rolls),) = tuple(r_d6_mul_2_roll)
            assert len(mul_rolls) == 2
            r_d6_roll, _ = mul_rolls  # look at the left side
            assert r_d6_roll.r == r_d6, r_d6_roll
            assert len(r_d6_roll) == 1, r_d6_roll
            assert all(outcome in d6 for outcome in r_d6_roll.outcomes()), r_d6_roll

    def test_getitem(self) -> None:
        r_123 = R.from_values(1, 2, 3)
        r_123_roll = r_123.roll()
        assert len(r_123_roll) == 3
        assert (
            r_123_roll[:]
            == tuple(r_123_roll[i] for i in range(len(r_123_roll)))
            == tuple(r_123_roll)
        )

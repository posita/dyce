# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H, P, R
from dyce.r import ValueRoller

from .test_h import _INTEGRAL_OUTCOME_TYPES, _OUTCOME_TYPES

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


class TestValueRoller:
    def test_init_outcome(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for o in range(-2, 3):
                annotation = f"{o_type}({o})"
                r = R.from_value(o_type(o), annotation=annotation)
                assert r.value == o, r
                assert r.annotation == annotation, r

    def test_init_h(self) -> None:
        d6 = H(6)
        r_d6 = R.from_value(d6, annotation="d6")
        assert r_d6.value == d6
        assert r_d6.annotation == "d6"

    def test_init_p(self) -> None:
        p_3d6 = 3@P(6)
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
            repr(R.from_value(3@P(6), annotation={"two": 2}))
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

    def test_h(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))

            for o in h:
                r = R.from_value(o_type(o), annotation=f"{o_type}")
                assert r.h() == {o_type(o): 1}, r

            r = R.from_value(h, annotation=f"{o_type}")
            assert r.h() == h, r

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            assert r.h() == h, r

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
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            one_add_r = 1 + r
            assert one_add_r.h() == 1 + r.h(), one_add_r
            r_add_one = r + 1
            assert r_add_one.h() == r.h() + 1, r_add_one
            r_add_r = r + r
            assert r_add_r.h() == r.h() + r.h(), r_add_r

    def test_op_sub(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            one_sub_r = 1 - r
            assert one_sub_r.h() == 1 - r.h(), one_sub_r
            r_sub_one = r - 1
            assert r_sub_one.h() == r.h() - 1, r_sub_one
            r_sub_r = r - r
            assert r_sub_r.h() == r.h() - r.h(), r_sub_r

    def test_op_mul(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            two_mul_r = 2 * r
            assert two_mul_r.h() == 2 * r.h(), two_mul_r
            r_mul_two = r * 2
            assert r_mul_two.h() == r.h() * 2, r_mul_two
            r_mul_r = r * r
            assert r_mul_r.h() == r.h() * r.h(), r_mul_r

    def test_op_truediv(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3) if o != 0)
            r = R.from_value(h, annotation=f"{o_type}")
            two_truediv_r = 2 / r
            assert two_truediv_r.h() == 2 / r.h(), two_truediv_r
            r_truediv_two = r / 2
            assert r_truediv_two.h() == r.h() / 2, r_truediv_two
            r_truediv_r = r / r
            assert r_truediv_r.h() == r.h() / r.h(), r_truediv_r

    def test_op_floordiv(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3) if o != 0)
            r = R.from_value(h, annotation=f"{o_type}")
            two_floordiv_r = 2 // r
            assert two_floordiv_r.h() == 2 // r.h(), two_floordiv_r
            r_floordiv_two = r // 2
            assert r_floordiv_two.h() == r.h() // 2, r_floordiv_two
            r_floordiv_r = r // r
            assert r_floordiv_r.h() == r.h() // r.h(), r_floordiv_r

    def test_op_mod(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3) if o != 0)
            r = R.from_value(h, annotation=f"{o_type}")
            two_mod_r = 2 % r
            assert two_mod_r.h() == 2 % r.h(), two_mod_r
            r_mod_two = r % 2
            assert r_mod_two.h() == r.h() % 2, r_mod_two
            r_mod_r = r % r
            assert r_mod_r.h() == r.h() % r.h(), r_mod_r

    def test_op_pow(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(4, 0, -1))
            r = R.from_value(h, annotation=f"{o_type}")
            two_pow_r = 2 ** r
            assert two_pow_r.h() == 2 ** r.h(), two_pow_r
            r_pow_two = r ** 2
            assert r_pow_two.h() == r.h() ** 2, r_pow_two
            r_pow_r = r ** r
            assert r_pow_r.h() == r.h() ** r.h(), r_pow_r

    def test_op_and(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            two_and_r = 2 & r
            assert two_and_r.h() == 2 & r.h(), two_and_r
            r_and_two = r & 2
            assert r_and_two.h() == r.h() & 2, r_and_two
            r_and_r = r & r
            assert r_and_r.h() == r.h() & r.h(), r_and_r

    def test_op_xor(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            two_xor_r = 2 ^ r
            assert two_xor_r.h() == 2 ^ r.h(), two_xor_r
            r_xor_two = r ^ 2
            assert r_xor_two.h() == r.h() ^ 2, r_xor_two
            r_xor_r = r ^ r
            assert r_xor_r.h() == r.h() ^ r.h(), r_xor_r

    def test_op_or(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            two_or_r = 2 | r
            assert two_or_r.h() == 2 | r.h(), two_or_r
            r_or_two = r | 2
            assert r_or_two.h() == r.h() | 2, r_or_two
            r_or_r = r | r
            assert r_or_r.h() == r.h() | r.h(), r_or_r

    def _test_cmp_op(
        self,
        op_name: str,
    ) -> None:
        import operator

        __op__ = getattr(operator, f"__{op_name}__")

        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))

            for o in h:
                annotation = f"{o_type}"
                r = R.from_value(o_type(o), annotation=annotation)
                r_do_op = getattr(r, op_name)
                r_op_r = r_do_op(r)
                left_child, right_child = r_op_r.children
                assert left_child == r
                assert right_child == r
                assert r_op_r.h() == H({bool(__op__(o, o)): 1}), r_op_r
                assert tuple(r_op_r.roll().outcomes()) == (bool(__op__(o, o)),), r_op_r

                r_neg = -r
                r_op_r_neg = r_do_op(r_neg)
                left_child, right_child = r_op_r_neg.children
                assert left_child == r
                assert right_child == r_neg
                assert r_op_r_neg.h() == H({bool(__op__(o, -o)): 1}), r_op_r_neg
                assert tuple(r_op_r_neg.roll().outcomes()) == (
                    bool(__op__(o, -o)),
                ), r_op_r_neg

            zero = R.from_value(o_type(0))
            r = R.from_value(h, annotation=f"{o_type}")
            zero_do_op = getattr(zero, op_name)
            zero_op_r = zero_do_op(r)
            zero_h_do_op = getattr(zero.h(), op_name)
            assert zero_op_r.h() == zero_h_do_op(h), zero_op_r
            r_op_zero = getattr(r, op_name)(zero)
            h_do_op = getattr(h, op_name)
            assert r_op_zero.h() == h_do_op(0), r_op_zero
            r_op_r = getattr(r, op_name)(r)
            assert r_op_r.h() == h_do_op(h), r_op_r

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

    def test_h(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))

            for o in h:
                r = R.from_value(o_type(o), annotation=f"{o_type}")
                r_doubled = r + r
                assert r_doubled.h() == r.h() + r.h(), r_doubled

            r = R.from_value(h, annotation=f"{o_type}")
            r_add_r = r + r
            assert r_add_r.h() == h + h, r_add_r

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            r_mul_r = r * r
            r_mul_r_h = r_mul_r.h()
            assert r_mul_r_h == r.h() * r.h(), r_mul_r

            for _ in range(1000):
                r_mul_r_roll = r_mul_r.roll()
                assert r_mul_r_roll.r == r_mul_r
                assert r_mul_r_roll.total in r_mul_r_h, r_mul_r


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
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_neg = -r
                (child,) = r_neg.children
                assert child == r, r_neg
                assert r_neg.h() == -(r.h()), r_neg
                assert tuple(r_neg.roll().outcomes()) == (-o,), r_neg

    def test_op_pos(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_pos = +r
                (child,) = r_pos.children
                assert child == r, r_pos
                assert r_pos.h() == +(r.h()), r_pos
                assert tuple(r_pos.roll().outcomes()) == (+o,), r_pos

    def test_op_abs(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_abs = abs(r)
                (child,) = r_abs.children
                assert child == r, r_abs
                assert r_abs.h() == abs(r.h()), r_abs
                assert tuple(r_abs.roll().outcomes()) == (abs(o),), r_abs

    def test_even(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_even = r.is_even()
                (child,) = r_even.children
                assert child == r, r_even
                assert r_even.h() == r.h().is_even(), r_even
                assert tuple(r_even.roll().outcomes()) == (o % 2 == 0,), r_even

    def test_odd(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_odd = r.is_odd()
                (child,) = r_odd.children
                assert child == r, r_odd
                assert r_odd.h() == r.h().is_odd(), r_odd
                assert tuple(r_odd.roll().outcomes()) == (o % 2 != 0,), r_odd

    def test_inverse(self) -> None:
        for o_type in _INTEGRAL_OUTCOME_TYPES:
            for o in range(-2, 3):
                r = R.from_value(o_type(o), annotation=f"{o_type}({o})")
                r_inv = ~r
                (child,) = r_inv.children
                assert child == r, r_inv
                assert r_inv.h() == ~(r.h()), r_inv
                assert tuple(r_inv.roll().outcomes()) == (~o,), r_inv

    def test_h(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))

            for o in h:
                r_neg = -R.from_value(o_type(o), annotation=f"{o_type}")
                assert r_neg.h() == {-o_type(o): 1}, r_neg

            r_neg = -R.from_value(h, annotation=f"{o_type}")
            assert r_neg.h() == -h, r_neg

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            r_neg = -r
            r_neg_h = r_neg.h()
            assert r_neg_h == -(r.h()), r_neg

            for _ in range(1000):
                r_neg_roll = r_neg.roll()
                assert r_neg_roll.r == r_neg
                assert r_neg_roll.total in r_neg_h, r_neg


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

    def test_h(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for i_type in _INTEGRAL_OUTCOME_TYPES:
                h = H(o_type(o) for o in range(-2, 3))

                for o in h:
                    r_3 = (i_type(3) @ R.from_value(o_type(o))).annotate(
                        f"{o_type}, {i_type}"
                    )
                    assert r_3.h() == i_type(3) @ H({o_type(o): 1}), r_3

                r_3 = (i_type(3) @ R.from_value(h, annotation=f"{o_type}")).annotate(
                    f"{i_type}"
                )
                assert r_3.h() == i_type(3) @ h, r_3

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            for i_type in _INTEGRAL_OUTCOME_TYPES:
                h = H(o_type(o) for o in range(-2, 3))
                r = R.from_value(h, annotation=f"{o_type}")
                r_1000 = (i_type(1000) @ r).annotate(f"{i_type}")
                r_1000_roll = r_1000.roll()
                assert len(r_1000_roll) == 1000

                for outcome in r_1000_roll.outcomes():
                    assert outcome in r.h()

                assert all(
                    outcome in r.h() for outcome in r_1000_roll.outcomes()
                ), r_1000_roll


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

    def test_h(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))

            for o in h:
                r_3 = R.from_values(
                    o_type(o), o_type(o), o_type(o), annotation=f"{o_type}"
                )
                assert r_3.h() == 3 @ H({o_type(o): 1}), r_3

            r_3 = R.from_values(h, h, h, annotation=f"{o_type}")
            assert r_3.h() == 3 @ h, r_3

    def test_roll(self) -> None:
        for o_type in _OUTCOME_TYPES:
            h = H(o_type(o) for o in range(-2, 3))
            r = R.from_value(h, annotation=f"{o_type}")
            r_3 = R.from_rs(r, r, r)
            r_3_h = r_3.h()
            assert r_3_h == 3 @ (r.h()), r_3

            for _ in range(1000):
                r_3_roll = r_3.roll()
                assert r_3_roll.r == r_3
                assert r_3_roll.total in r_3_h, r_3_roll


class TestRoll:
    def test_hierarchy(self) -> None:
        h = H(6)
        r_d6 = R.from_value(h)
        r_d6_mul_2 = r_d6 * 2
        r_d6_mul_2_neg = -r_d6_mul_2
        r_d6_mul_2_neg_add_4 = r_d6_mul_2_neg + 4
        r_d6_mul_2_neg_add_4_3 = 3 @ r_d6_mul_2_neg_add_4
        assert r_d6_mul_2_neg_add_4_3.h() == 3 @ (-(2 * h) + 4)

        r_d6_mul_2_neg_add_4_3_roll = r_d6_mul_2_neg_add_4_3.roll()
        assert (
            r_d6_mul_2_neg_add_4_3_roll.r == r_d6_mul_2_neg_add_4_3
        ), r_d6_mul_2_neg_add_4_3_roll
        assert len(r_d6_mul_2_neg_add_4_3_roll) == 3, r_d6_mul_2_neg_add_4_3_roll
        assert all(
            outcome in r_d6_mul_2_neg_add_4.h()
            for outcome in r_d6_mul_2_neg_add_4_3_roll.outcomes()
        ), r_d6_mul_2_neg_add_4_3_roll

        for _, n_rolls in r_d6_mul_2_neg_add_4_3_roll:
            assert len(n_rolls) == 1
            (r_d6_mul_2_neg_add_4_roll,) = n_rolls
            assert r_d6_mul_2_neg_add_4_roll.r == r_d6_mul_2_neg_add_4
            assert len(r_d6_mul_2_neg_add_4_roll) == 1, r_d6_mul_2_neg_add_4_roll
            assert all(
                outcome in r_d6_mul_2_neg_add_4.h()
                for outcome in r_d6_mul_2_neg_add_4_roll.outcomes()
            ), r_d6_mul_2_neg_add_4_roll

            ((_, add_rolls),) = tuple(r_d6_mul_2_neg_add_4_roll)
            assert len(add_rolls) == 2
            r_d6_mul_2_neg_roll, _ = add_rolls  # look at the left side
            assert r_d6_mul_2_neg_roll.r == r_d6_mul_2_neg, r_d6_mul_2_neg_roll
            assert len(r_d6_mul_2_neg_roll) == 1, r_d6_mul_2_neg_roll
            assert all(
                outcome in r_d6_mul_2_neg.h()
                for outcome in r_d6_mul_2_neg_roll.outcomes()
            ), r_d6_mul_2_neg_roll

            ((_, neg_rolls),) = tuple(r_d6_mul_2_neg_roll)
            assert len(neg_rolls) == 1
            (r_d6_mul_2_roll,) = neg_rolls
            assert r_d6_mul_2_roll.r == r_d6_mul_2, r_d6_mul_2_roll
            assert len(r_d6_mul_2_roll) == 1, r_d6_mul_2_roll
            assert all(
                outcome in r_d6_mul_2.h() for outcome in r_d6_mul_2_roll.outcomes()
            ), r_d6_mul_2_roll

            ((_, mul_rolls),) = tuple(r_d6_mul_2_roll)
            assert len(mul_rolls) == 2
            r_d6_roll, _ = mul_rolls  # look at the left side
            assert r_d6_roll.r == r_d6, r_d6_roll
            assert len(r_d6_roll) == 1, r_d6_roll
            assert all(
                outcome in r_d6.h() for outcome in r_d6_roll.outcomes()
            ), r_d6_roll

    def test_getitem(self) -> None:
        r_123 = R.from_values(1, 2, 3)
        r_123_roll = r_123.roll()
        assert len(r_123_roll) == 3
        assert (
            r_123_roll[:]
            == tuple(r_123_roll[i] for i in range(len(r_123_roll)))
            == tuple(r_123_roll)
        )

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
from collections.abc import Callable
from typing import Any, assert_type

import pytest

from dyce import H, HableOpsMixin, HableT, P

__all__ = ()

_BINARY_OPERATORS: tuple[Callable[[Any, Any], Any], ...] = (
    operator.add,
    operator.sub,
    operator.mul,
    operator.truediv,
    operator.floordiv,
    operator.mod,
    operator.pow,
    operator.lshift,
    operator.rshift,
    operator.and_,
    operator.or_,
    operator.xor,
)

_COMMUTATIVE_OPERATORS: tuple[Callable[[Any, Any], Any], ...] = (
    operator.add,
    operator.mul,
    operator.and_,
    operator.or_,
    operator.xor,
)


class _HableImplementationWithOps(HableOpsMixin[int]):
    r"""Minimal concrete HableOpsMixin for testing."""

    def __init__(self, h: H[int]) -> None:
        self._h = h

    def h(self) -> H[int]:
        return self._h


class _HableImplementation(HableT[int]):
    r"""Minimal concrete HableT without operator support."""

    __slots__ = ("_h",)

    def __init__(self, h: H[int]) -> None:
        self._h = h

    def h(self) -> H[int]:
        return self._h


class _StructuralHableImplementation:
    r"""Implements the shape of HableT without deriving from it."""

    __slots__ = ("_h",)

    def __init__(self, h: H[int]) -> None:
        self._h = h

    def h(self) -> H[int]:
        return self._h


class TestHableT:
    def test_does_not_imply_operator_support(self) -> None:
        h = H({1: 1})
        hable = _HableImplementation(H({2: 1}))

        assert not isinstance(hable, HableOpsMixin)
        assert h != hable
        assert h.__add__(hable) is NotImplemented  # type: ignore[operator] # ty: ignore[no-matching-overload]
        assert h + hable.h() == H({3: 1})

    def test_requires_explicit_inheritance(self) -> None:
        assert not isinstance(_StructuralHableImplementation(H({1: 1})), HableT)


class TestHableOpsMixin:
    def test_binary_operator_types_flatten_operator_owning_operands(self) -> None:
        p = P(2)
        hp = H({p: 1})

        assert_type(p + p, H[int])
        assert_type(p - p, H[int])
        assert_type(p * p, H[int])
        assert_type(p / p, H[float])
        assert_type(p // p, H[int])
        assert_type(p % p, H[int])
        assert_type(p**p, H[Any])
        assert_type(p << p, H[int])
        assert_type(p >> p, H[int])
        assert_type(p & p, H[int])
        assert_type(p | p, H[int])
        assert_type(p ^ p, H[int])

        assert_type(hp + hp, H[H[int]])
        assert_type(hp - hp, H[H[int]])
        assert_type(hp * hp, H[H[int]])
        assert_type(hp / hp, H[H[float]])
        assert_type(hp // hp, H[H[int]])
        assert_type(hp % hp, H[H[int]])
        assert_type(hp << hp, H[H[int]])
        assert_type(hp >> hp, H[H[int]])
        assert_type(hp & hp, H[H[int]])
        assert_type(hp | hp, H[H[int]])
        assert_type(hp ^ hp, H[H[int]])

    def test_satisfies_hable_t(self) -> None:
        assert isinstance(_HableImplementationWithOps(H({1: 1})), HableT)

    def test_scalar_fwd(self) -> None:
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) + 10 == H({11: 1, 12: 1})
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) - 10 == H({-9: 1, -8: 1})
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) * 10 == H({10: 1, 20: 1})
        # Integer results only, even with truediv
        assert _HableImplementationWithOps(H({10: 1, 20: 1})) / 10 == H(  # ruff: ignore[float-equality-comparison]
            {1.0: 1, 2.0: 1}
        )
        assert _HableImplementationWithOps(H({10: 1, 20: 1})) // 10 == H({1: 1, 2: 1})
        assert _HableImplementationWithOps(H({1: 1, 2: 2})) % 2 == H({0: 2, 1: 1})
        assert _HableImplementationWithOps(H({1: 2, 2: 1})) ** 2 == H({1: 2, 4: 1})
        assert _HableImplementationWithOps(H({6: 2, 7: 1})) << 1 == H({12: 2, 14: 1})
        assert _HableImplementationWithOps(H({6: 2, 7: 1})) >> 1 == H({3: 3})
        assert _HableImplementationWithOps(H({6: 2, 7: 1})) & 5 == H({4: 2, 5: 1})
        assert _HableImplementationWithOps(H({4: 2, 5: 1})) | 3 == H({7: 3})
        assert _HableImplementationWithOps(H({3: 3, 4: 2, 5: 1})) ^ 7 == H(
            {2: 1, 3: 2, 4: 3}
        )

    def test_scalar_ref(self) -> None:
        assert 10 + _HableImplementationWithOps(H({1: 1, 2: 1})) == H({11: 1, 12: 1})
        assert 10 - _HableImplementationWithOps(H({1: 1, 2: 1})) == H({9: 1, 8: 1})
        assert 10 * _HableImplementationWithOps(H({1: 1, 2: 1})) == H({10: 1, 20: 1})
        # Integer results only, even with truediv
        assert 10 / _HableImplementationWithOps(H({1: 1, 2: 1})) == H({10.0: 1, 5.0: 1})  # ruff: ignore[float-equality-comparison]
        assert 10 // _HableImplementationWithOps(H({1: 1, 2: 1})) == H({10: 1, 5: 1})
        assert 3 % _HableImplementationWithOps(H({2: 1, 3: 2})) % 2 == H({0: 2, 1: 1})
        assert 2 ** _HableImplementationWithOps(H({1: 2, 2: 1})) == H({2: 2, 4: 1})
        assert 5 << _HableImplementationWithOps(H({1: 2, 2: 1})) == H({10: 2, 20: 1})
        assert 5 >> _HableImplementationWithOps(H({1: 2, 2: 1})) == H({2: 2, 1: 1})
        assert 5 & _HableImplementationWithOps(H({6: 2, 7: 1})) == H({4: 2, 5: 1})
        assert 3 | _HableImplementationWithOps(H({4: 2, 5: 1})) == H({7: 3})
        assert 7 ^ _HableImplementationWithOps(H({3: 3, 4: 2, 5: 1})) == H(
            {2: 1, 3: 2, 4: 3}
        )

    def test_histogram(self) -> None:
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) + H({3: 1}) == H(
            {4: 1, 5: 1}
        )

    def test_unary(self) -> None:
        assert -_HableImplementationWithOps(H({1: 2, 2: 1})) == H({-1: 2, -2: 1})
        assert +_HableImplementationWithOps(H({1: 2, 2: 1})) == H({1: 2, 2: 1})
        assert abs(_HableImplementationWithOps(H({-1: 2, -2: 1}))) == H({1: 2, 2: 1})
        assert ~_HableImplementationWithOps(H({1: 2, 2: 1})) == H({-3: 1, -2: 2})

    def test_not_implemented(self) -> None:
        assert (
            _HableImplementationWithOps(H({1: 1})).__add__("incompatible")  # type: ignore[operator]  # ty: ignore[no-matching-overload]
            is NotImplemented
        )
        with pytest.raises(TypeError):
            _HableImplementationWithOps(H({1: 1})) + "incompatible"  # type: ignore[operator]  # ty: ignore[unsupported-operator]

    def test_hable_ops_mixin_rhs(self) -> None:
        w1 = _HableImplementationWithOps(H({1: 1, 2: 1}))
        w2 = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert w1 + w2 == H({4: 1, 5: 2, 6: 1})
        assert w1 - w2 == H({-3: 1, -2: 2, -1: 1})
        assert w1 * w2 == H({3: 1, 4: 1, 6: 1, 8: 1})


class TestHableH:
    def test_does_not_use_hable_ops_mixin(self) -> None:
        assert not isinstance(H({1: 1}), HableOpsMixin)

    def test_satisfies_hable_t(self) -> None:
        assert isinstance(H({1: 1}), HableT)

    def test_hable_t_does_not_add_instance_dict(self) -> None:
        assert not hasattr(H({1: 1}), "__dict__")

    def test_h_returns_self(self) -> None:
        h = H({1: 1})

        assert h.h() is h


class TestHForwardOpsWithHableOpsMixin:
    r"""H forward operators coerce HableOpsMixin operands via _flatten_to_h."""

    def test_h_add_hable_ops_mixin(self) -> None:
        w = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert H({1: 1, 2: 1}) + w == H({4: 1, 5: 2, 6: 1})

    def test_h_sub_hable_ops_mixin(self) -> None:
        w = _HableImplementationWithOps(H({1: 1, 2: 1}))
        assert H({3: 1, 4: 1}) - w == H({1: 1, 2: 2, 3: 1})

    def test_h_mul_hable_ops_mixin(self) -> None:
        w = _HableImplementationWithOps(H({2: 1, 3: 1}))
        assert H({1: 1, 2: 1}) * w == H({2: 1, 3: 1, 4: 1, 6: 1})

    def test_h_forward_ops_accept_hable_ops_mixin(self) -> None:
        # Spot-check each forward operator returns a valid H (not NotImplemented or
        # an H with H-objects as keys)
        h = H({2: 1, 4: 1})
        w = _HableImplementationWithOps(H({1: 1, 2: 1}))
        result_add = h + w
        result_sub = h - w
        result_mul = h * w
        result_floordiv = h // w
        result_mod = h % w
        for result in (result_add, result_sub, result_mul, result_floordiv, result_mod):
            assert isinstance(result, H)
            assert all(isinstance(k, int) for k in result)

    def test_h_op_mixin_commutes_with_mixin_op_h(self) -> None:
        h = H({1: 1, 2: 1})
        w = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert h + w == w + h
        assert h * w == w * h


class TestHableOpsMixinOperatorEquivalence:
    @pytest.mark.parametrize("op", _BINARY_OPERATORS)
    def test_mixin_operands_match_explicit_normalization(
        self, op: Callable[[Any, Any], Any]
    ) -> None:
        h = H({4: 1, 6: 2})
        w = _HableImplementationWithOps(H({1: 2, 2: 1}))

        assert op(h, w) == op(h, w.h())
        assert op(w, h) == op(w.h(), h)

    @pytest.mark.parametrize("op", _BINARY_OPERATORS)
    def test_scalar_operands_match_explicit_normalization(
        self, op: Callable[[Any, Any], Any]
    ) -> None:
        w = _HableImplementationWithOps(H({1: 2, 2: 1}))

        assert op(w, 2) == op(w.h(), 2)
        assert op(8, w) == op(8, w.h())

    @pytest.mark.parametrize("op", _COMMUTATIVE_OPERATORS)
    def test_commutative_operators_remain_commutative(
        self, op: Callable[[Any, Any], Any]
    ) -> None:
        h = H({4: 1, 6: 2})
        w = _HableImplementationWithOps(H({1: 2, 2: 1}))

        assert op(h, w) == op(w, h)

    def test_noncommutative_operators_preserve_operand_order(self) -> None:
        h = H({4: 1, 6: 2})
        w = _HableImplementationWithOps(H({1: 2, 2: 1}))

        assert h - w == h - w.h()
        assert w - h == w.h() - h
        assert h - w != w - h

    def test_nested_hable_outcomes_are_not_recursively_normalized(self) -> None:
        p4 = P(4)
        p3 = P(3)
        outer = H({p4: 1, p3: 2})

        assert outer + 3 == H({p4 + 3: 1, p3 + 3: 2})  # type: ignore[operator]

    def test_nested_hable_outcomes_preserve_commutative_equivalence(self) -> None:
        p4 = P(4)
        p3 = P(3)
        p2 = P(2)
        outer = H({p4: 1, p3: 2})
        expected = H(
            {
                p4 + 1: 1,
                p4 + 2: 1,
                p3 + 1: 2,
                p3 + 2: 2,
            }
        )

        assert outer + p2 == outer + p2.h() == expected
        assert p2 + outer == p2.h() + outer == expected

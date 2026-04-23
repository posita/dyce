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

import pytest

from dyce import H
from dyce.h import HableT
from dyce.hable import HableOpsMixin

__all__ = ()


class _HableImplementationWithOps(HableOpsMixin[int]):
    r"""Minimal concrete HableOpsMixin for testing."""

    def __init__(self, h: H[int]) -> None:
        self._h = h

    def h(self) -> H[int]:
        return self._h


class TestHableOpsMixin:
    def test_satisfies_hable_t(self) -> None:
        assert isinstance(_HableImplementationWithOps(H({1: 1})), HableT)

    def test_scalar_fwd(self) -> None:
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) + 10 == H({11: 1, 12: 1})
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) - 10 == H({-9: 1, -8: 1})
        assert _HableImplementationWithOps(H({1: 1, 2: 1})) * 10 == H({10: 1, 20: 1})
        # Integer results only, even with truediv
        assert _HableImplementationWithOps(H({10: 1, 20: 1})) / 10 == H(  # noqa: RUF069
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
        assert 10 / _HableImplementationWithOps(H({1: 1, 2: 1})) == H({10.0: 1, 5.0: 1})  # noqa: RUF069
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

    def test_hable_rhs(self) -> None:
        # HableOpsMixin forward ops accept another HableT as rhs (via _flatten_to_h)
        w1 = _HableImplementationWithOps(H({1: 1, 2: 1}))
        w2 = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert w1 + w2 == H({4: 1, 5: 2, 6: 1})
        assert w1 - w2 == H({-3: 1, -2: 2, -1: 1})
        assert w1 * w2 == H({3: 1, 4: 1, 6: 1, 8: 1})


class TestHForwardOpsWithHableT:
    r"""H forward operators coerce non-H HableT rhs via _flatten_to_h."""

    def test_h_add_hable(self) -> None:
        w = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert H({1: 1, 2: 1}) + w == H({4: 1, 5: 2, 6: 1})

    def test_h_sub_hable(self) -> None:
        w = _HableImplementationWithOps(H({1: 1, 2: 1}))
        assert H({3: 1, 4: 1}) - w == H({1: 1, 2: 2, 3: 1})

    def test_h_mul_hable(self) -> None:
        w = _HableImplementationWithOps(H({2: 1, 3: 1}))
        assert H({1: 1, 2: 1}) * w == H({2: 1, 3: 1, 4: 1, 6: 1})

    def test_h_all_forward_ops_accept_hable(self) -> None:
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

    def test_h_op_hable_commutes_with_hable_op_h(self) -> None:
        h = H({1: 1, 2: 1})
        w = _HableImplementationWithOps(H({3: 1, 4: 1}))
        assert h + w == w + h
        assert h * w == w * h

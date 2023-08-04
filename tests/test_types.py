# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import pytest

from dyce.types import is_even, is_odd

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_is_even() -> None:
    assert is_even(0)
    assert not is_even(1)


def test_is_even_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert is_even(numpy.int64(0))
    assert not is_even(numpy.int64(1))


def test_is_even_sympy() -> None:
    sympy = pytest.importorskip("sympy", reason="requires sympy")
    assert is_even(sympy.sympify(0))
    assert not is_even(sympy.sympify(1))


def test_is_odd() -> None:
    assert is_odd(1)
    assert not is_odd(0)


def test_is_odd_numpy() -> None:
    numpy = pytest.importorskip("numpy", reason="requires numpy")
    assert is_odd(numpy.int64(1))
    assert not is_odd(numpy.int64(0))


def test_is_odd_sympy() -> None:
    sympy = pytest.importorskip("sympy", reason="requires sympy")
    assert is_odd(sympy.sympify(1))
    assert not is_odd(sympy.sympify(0))

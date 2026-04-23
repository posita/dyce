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

from dyce.types import lossless_int, natural_key

__all__ = ()


class TestLosslessInt:
    def test_int_passthrough(self) -> None:
        assert lossless_int(3) == 3

    def test_float_integer_value(self) -> None:
        assert lossless_int(3.0) == 3

    def test_float_non_integer_raises(self) -> None:
        with pytest.raises(ValueError, match=r"\bcannot\b.*\blosslessly\b.*\bcoerce\b"):
            lossless_int(3.5)

    def test_negative(self) -> None:
        assert lossless_int(-5) == -5

    def test_zero(self) -> None:
        assert lossless_int(0) == 0

    def test_returns_int_type(self) -> None:
        assert isinstance(lossless_int(3.0), int)


class TestNaturalKey:
    def test_mixed(self) -> None:
        assert natural_key("abc10def") == ("abc", 10, "def")

    def test_leading_digits(self) -> None:
        assert natural_key("42") == ("", 42, "")

    def test_trailing_digits(self) -> None:
        assert natural_key("item2") == ("item", 2, "")

    def test_no_digits(self) -> None:
        assert natural_key("abc") == ("abc",)

    def test_all_digits(self) -> None:
        assert natural_key("123") == ("", 123, "")

    def test_multiple_runs(self) -> None:
        assert natural_key("a1b2c3") == ("a", 1, "b", 2, "c", 3, "")

    def test_fallback_uses_natural_key(self) -> None:
        assert [
            str(v)
            for v in sorted(
                (
                    _NoCompare("item10"),
                    _NoCompare("item2"),
                    _NoCompare("item1"),
                ),
                key=natural_key,
            )
        ] == [
            "item1",
            "item2",
            "item10",
        ]


# ---- Helpers -------------------------------------------------------------------------


class _NoCompare:
    r"""
    For testing natural_key sorting and other places where outcomes ignorant of mathematical operations is required.
    """

    def __init__(self, val: str) -> None:
        self.val = val

    def __lt__(self, other: object) -> bool:
        raise TypeError

    def __str__(self) -> str:
        return self.val

    def __repr__(self) -> str:
        return f"_NoCompare({self.val!r})"

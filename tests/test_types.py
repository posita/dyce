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

from itertools import chain

import pytest

from dyce.types import getitems, lossless_int, natural_key

from ._helpers import NoCompare

__all__ = ()


class TestGetItems:
    def test_index(self) -> None:
        seq = tuple(range(-4, 5))
        for i in range(len(seq)):
            assert tuple(getitems(seq, (i,))) == seq[i : i + 1]
        assert tuple(getitems(seq, range(len(seq)))) == seq
        assert tuple(getitems(seq, range(len(seq) - 1, -1, -1))) == seq[::-1]

    def test_overlapping_indexes(self) -> None:
        seq = tuple(range(-4, 5))
        assert (
            tuple(getitems(seq, chain(range(len(seq) - 1), range(1, len(seq)))))
            == seq[:-1] + seq[1:]
        )

    def test_slice(self) -> None:
        seq = tuple(range(-4, 5))
        for i in range(len(seq)):
            assert tuple(getitems(seq, (slice(i, i + 1),))) == seq[i : i + 1]
        assert tuple(getitems(seq, (slice(None),))) == seq

    def test_overlapping_slices(self) -> None:
        seq = tuple(range(-4, 5))
        assert tuple(getitems(seq, (slice(None), slice(1, -1)))) == seq + seq[1:-1]

    def test_mixed(self) -> None:
        seq = tuple(range(-4, 5))
        assert (
            tuple(
                getitems(
                    seq,
                    (
                        8,
                        6,
                        4,
                        2,
                        0,
                        slice(1, None, 2),
                        slice(None, None, 2),
                        7,
                        5,
                        3,
                        1,
                    ),
                )
            )
            == seq[::-2] + seq[1::2] + seq[::2] + seq[-2::-2]
        )

    def test_out_of_bounds_index_raises(self) -> None:
        seq = tuple(range(-4, 0))
        with pytest.raises(IndexError):
            tuple(getitems(seq, (0, len(seq))))
        with pytest.raises(IndexError):
            tuple(getitems(seq, (-len(seq) - 1,)))

    def test_out_of_bounds_slice(self) -> None:
        seq = tuple(range(-4, 0))
        assert tuple(getitems(seq, (slice(len(seq), len(seq) + 1),))) == ()
        assert tuple(getitems(seq, (slice(-len(seq) - 1, -len(seq)),))) == ()


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
                    NoCompare("item10"),
                    NoCompare("item2"),
                    NoCompare("item1"),
                ),
                key=natural_key,
            )
        ] == [
            "item1",
            "item2",
            "item10",
        ]

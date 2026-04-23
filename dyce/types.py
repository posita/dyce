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
import re
from collections.abc import Iterable, Iterator, Sequence
from types import NotImplementedType  # noqa: TC003
from typing import SupportsIndex, SupportsInt, TypeVar

__all__ = (
    "GetItemT",
    "getitems",
    "lossless_int",
    "natural_key",
)

try:
    from beartype.roar import (
        BeartypeCallHintViolation,  # pyright: ignore[reportAssignmentType]
    )
except ImportError:  # pragma: no cover

    class BeartypeCallHintViolation(Exception):  # type: ignore[no-redef] # noqa: N818
        pass


_T = TypeVar("_T")

try:
    from beartype import BeartypeConf, BeartypeStrategy, beartype

    nobeartype = beartype(
        conf=BeartypeConf(
            strategy=BeartypeStrategy.O0,
        )
    )  # pyright: ignore[reportAssignmentType]
except ImportError:  # pragma: no cover

    def nobeartype(arg: _T) -> _T:
        return arg


GetItemT = SupportsIndex | slice


def getitems(seq: Sequence[_T], keys: Iterable[GetItemT]) -> Iterator[_T]:
    r"""
    Yield items from *seq* selected by *keys*, where each key is either a [`SupportsIndex`][typing.SupportsIndex] or a `#!python slice`.

        >>> from dyce.types import getitems
        >>> list(getitems([10, 20, 30, 40], [0, -1, slice(1, 3)]))
        [10, 40, 20, 30]
    """
    for key in keys:
        if isinstance(key, slice):
            yield from seq[key]
        else:
            yield seq[operator.index(key)]


def lossless_int(candidate: SupportsInt) -> int:
    r"""
    Calls `#!python int(candidate)`, but raises a `#!python ValueError` if the result does not compare equally to the original value.

        >>> from dyce.types import lossless_int
        >>> lossless_int(3)
        3
        >>> lossless_int(3.0)
        3
        >>> lossless_int(3.5)
        Traceback (most recent call last):
          ...
        ValueError: cannot (losslessly) coerce float(3.5) to an int
    """
    result = lossless_int_or_not_implemented(candidate)
    if result is NotImplemented:
        raise ValueError(
            f"cannot (losslessly) coerce {type(candidate).__qualname__}({candidate}) to an int"
        )
    return result


def lossless_int_or_not_implemented(
    candidate: SupportsInt,
) -> "int | NotImplementedType":
    r"""
    Like [`lossless_int`][dyce.types.lossless_int], but returns `#!python NotImplemented` instead of raising `#!python ValueError` when the conversion is lossy.
    """
    int_val = int(candidate)
    if int_val != candidate:
        return NotImplemented
    return int_val


def natural_key(val: object) -> tuple[int | str, ...]:
    r"""
    Return a sort key for *val* that orders embedded digit runs numerically.

    Splits `#!python str(val)` on digit boundaries and converts each run of digits to an `#!python int`, so that `#!python "a10"` sorts after `#!python "a2"`.

        >>> from dyce.types import natural_key
        >>> natural_key("abc10def")
        ('abc', 10, 'def')
        >>> natural_key("item2")
        ('item', 2, '')
        >>> natural_key("42")
        ('', 42, '')
        >>> natural_key({10: 1, 20: 1})
        ('{', 10, ': ', 1, ', ', 20, ': ', 1, '}')
        >>> sorted(["12b179", "12aone", "12b17c"], key=natural_key)
        ['12aone', '12b17c', '12b179']
    """
    return tuple(int(s) if s.isdigit() else s for s in re.split(r"(\d+)", str(val)))

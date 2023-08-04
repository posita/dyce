# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import re
from operator import __getitem__, __index__
from typing import Any, Callable, Iterable, Iterator, Sequence, TypeVar, Union

from numerary.bt import beartype
from numerary.types import SupportsIndex, SupportsInt

__all__ = (
    "as_int",
    "is_even",
    "is_odd",
)


# ---- Types ---------------------------------------------------------------------------


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_UnaryOperatorT = Callable[[_T_co], _T_co]
_BinaryOperatorT = Callable[[_T_co, _T_co], _T_co]
_GetItemT = Union[SupportsIndex, slice]


# ---- Functions -----------------------------------------------------------------------


@beartype
def as_int(val: SupportsInt) -> int:
    r"""
    Helper function to losslessly coerce *val* into an ``#!python int``. Raises
    ``#!python TypeError`` if that cannot be done.
    """
    int_val = int(val)

    if int_val != val:
        raise TypeError(f"cannot (losslessly) coerce {val} to an int")

    return int_val


@beartype
def getitems(seq: Sequence[_T], keys: Iterable[_GetItemT]) -> Iterator[_T]:
    for key in keys:
        if isinstance(key, slice):
            yield from __getitem__(seq, key)
        else:
            yield __getitem__(seq, __index__(key))


@beartype
def is_even(outcome: SupportsInt) -> bool:
    return as_int(outcome) % 2 == 0


@beartype
def is_odd(outcome: SupportsInt) -> bool:
    return as_int(outcome) % 2 != 0


@beartype
def natural_key(val: Any) -> tuple[Union[int, str], ...]:
    return tuple(int(s) if s.isdigit() else s for s in re.split(r"(\d+)", str(val)))


@beartype
def sorted_outcomes(vals: Iterable[_T]) -> list[_T]:
    vals = list(vals)

    try:
        vals.sort()
    except TypeError:
        # This is for outcomes that don't support direct comparisons, like symbolic
        # representations
        vals.sort(key=natural_key)

    return vals

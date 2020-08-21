# -*- encoding: utf-8; test-case-name: tests.test_main -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before viewing or using
this software in any capacity.
"""
# ======================================================================================

from __future__ import generator_stop
from typing import (
    Callable,
    DefaultDict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Tuple,
    Union,
    cast,
)
from typing_extensions import Protocol, runtime_checkable


# ---- Imports -------------------------------------------------------------------------


import collections.abc
import functools
import itertools
import logging
import math
import operator
import os


# ---- Data ----------------------------------------------------------------------------


__all__ = ("D", "H", "explode", "within")

_LOGGER = logging.getLogger(__name__)

_LOG_FMT_ENV = "LOG_FMT"
_LOG_FMT_DFLT = "%(message)s"
_LOG_LVL_ENV = "LOG_LVL"
_LOG_LVL_DFLT = logging.getLevelName(logging.WARNING)

_IntOperatorT = Callable[[int, int], int]
_IntPredicateT = Callable[[int, int], bool]
_ExplodeOnT = Callable[["H", int, int], bool]
_SubstituteT = Callable[["H", int, int], "H"]

try:
    _ROW_WIDTH = os.get_terminal_size().columns
except OSError:
    try:
        _ROW_WIDTH = int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        _ROW_WIDTH = 88


# ---- Classes -------------------------------------------------------------------------


class H(Mapping[int, int]):
    """A histogram supporting arithmetic operations. If `values` is an `int`, it is
    shorthand for creating a sequential range.

    >>> h6 = H(6)  # like a six-sided die (1d6)
    >>> h6 == H(range(1, 7))
    True

    >>> h6 + h6  # like 2d6
    H({12: 1, 11: 2, 10: 3, 9: 4, 8: 5, 7: 6, 6: 5, 5: 4, 4: 3, 3: 2, 2: 1})
    >>> print(_.format(width=65))
    avg |    7.00
     12 |   2.78% |#
     11 |   5.56% |##
     10 |   8.33% |####
      9 |  11.11% |#####
      8 |  13.89% |######
      7 |  16.67% |########
      6 |  13.89% |######
      5 |  11.11% |#####
      4 |   8.33% |####
      3 |   5.56% |##
      2 |   2.78% |#
    >>> 2@h6 == h6 + h6
    True

    >>> len(2@h6)  # number of distinct values
    11
    >>> sum((2@h6).counts())  # total number of combinations
    36

    >>> h6.ne(h6)  # where a first d6 shows a different value than a second d6
    H({1: 30, 0: 6})
    >>> print(_.format(width=65))
    avg |    0.83
      1 |  83.33% |#########################################
      0 |  16.67% |########

    >>> h6.lt(h6)  # where a first d6 shows less than a second
    H({1: 15, 0: 21})
    >>> print(_.format(width=65))
    avg |    0.42
      1 |  41.67% |####################
      0 |  58.33% |#############################

    Some esoteric things can be captured through careful enumeration. For example,
    re-rolling a 1 that appears on a first d20 roll could be captured by:

    >>> H(itertools.chain(((n, 20) for n in range(2, 21)), range(1, 21)))
    H({20: 21, 19: 21, 18: 21, 17: 21, 16: 21, 15: 21, 14: 21, 13: 21, 12: 21, 11: 21, 10: 21, 9: 21, 8: 21, 7: 21, 6: 21, 5: 21, 4: 21, 3: 21, 2: 21, 1: 1})
    """

    # ---- Types -----------------------------------------------------------------------

    @runtime_checkable
    class AbleT(Protocol):
        def h(self) -> "H":
            ...

    OperandT = Union[int, "H", AbleT]
    OperatorLT = Callable[[int, "H"], "H"]
    OperatorRT = Callable[["H", int], "H"]
    SourceT = Union[
        int, Iterable[int], Iterable[Tuple[int, int]], Mapping[int, int], AbleT
    ]

    # ---- Constructor -----------------------------------------------------------------

    def __init__(self, values: SourceT) -> None:
        super().__init__()
        self._simple_init = None

        if isinstance(values, int):
            self._simple_init = values

            if values < 0:
                values = range(-1, values - 1, -1)
            elif values > 0:
                values = range(1, values + 1)
            else:
                values = (0,)
        elif isinstance(values, H.AbleT):
            values = values.h()

        if not isinstance(values, collections.abc.Mapping):
            h = collections.defaultdict(int)  # type: DefaultDict[int, int]

            for value in values:
                if isinstance(value, tuple):
                    face, count = value  # pylint: disable=unpacking-non-sequence
                    h[face] += count
                else:
                    h[value] += 1

            values = h

        self._h = collections.OrderedDict(
            (face, values[face]) for face in sorted(values, reverse=True)
        )

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        arg = (
            self._simple_init
            if self._simple_init is not None
            else dict.__repr__(self._h)
        )
        return "{}({})".format(self.__class__.__name__, arg)

    def __eq__(self, other) -> bool:
        if isinstance(other, H.AbleT):
            return operator.eq(self, other.h())
        else:
            return super().__eq__(other)

    def __ne__(self, other) -> bool:
        if isinstance(other, H.AbleT):
            return operator.ne(self, other.h())
        else:
            return super().__ne__(other)

    def __len__(self) -> int:
        return len(self._h)

    def __getitem__(self, key: int) -> int:
        return operator.getitem(self._h, key)

    def __iter__(self) -> Iterator[int]:
        return iter(self._h)

    def __add__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.mul, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.mul, other)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: int) -> "H":
        if not isinstance(other, int):
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")

        return cast(H, sum(itertools.repeat(self, other)))

    def __rmatmul__(self, other: int) -> "H":
        return self.__matmul__(other)

    def __floordiv__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __rand__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __xor__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __or__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.or_, other)
        except NotImplementedError:
            return NotImplemented

    def __ror__(self, other: OperandT) -> "H":
        try:
            return self.rapply(operator.or_, other)
        except NotImplementedError:
            return NotImplemented

    def __neg__(self) -> "H":
        h = H((operator.neg(face), count) for face, count in self.items())

        if self._simple_init is not None:
            h._simple_init = operator.neg(self._simple_init)

        return h

    def __pos__(self) -> "H":
        h = H((operator.pos(face), count) for face, count in self.items())

        if self._simple_init is not None:
            h._simple_init = operator.pos(self._simple_init)

        return h

    def __abs__(self) -> "H":
        h = H((operator.abs(face), count) for face, count in self.items())

        if self._simple_init is not None:
            h._simple_init = operator.abs(self._simple_init)

        return h

    def items(self):
        return self._h.items()

    def keys(self):
        return self._h.keys()

    def values(self):
        return self._h.values()

    # ---- Methods ---------------------------------------------------------------------

    def apply(self, oper: _IntOperatorT, other: OperandT) -> "H":
        """
        TODO
        """
        if isinstance(other, int):
            return H((int(oper(face, other)), count) for face, count in self.items())

        if isinstance(other, H.AbleT):
            other = other.h()

        if isinstance(other, H):
            return H(
                (int(oper(a, b)), self[a] * other[b])
                for a, b in itertools.product(self, other)
            )

        raise NotImplementedError

    def rapply(self, oper: _IntOperatorT, other: OperandT) -> "H":
        if isinstance(other, int):
            return H((int(oper(other, face)), count) for face, count in self.items())

        if isinstance(other, H.AbleT):
            other = other.h()

        if isinstance(other, H):
            return H(
                (int(oper(b, a)), other[b] * self[a])
                for b, a in itertools.product(other, self)
            )

        raise NotImplementedError

    def filter(
        self,
        predicate: _IntPredicateT,
        other: OperandT,
        t_val: Optional[int] = None,
        f_val: Optional[int] = None,
    ) -> "H":
        """
        TODO
        """

        def _resolve(a: int, b: int):
            if predicate(a, b):
                return a if t_val is None else t_val
            else:
                return b if f_val is None else f_val

        return self.apply(_resolve, other)

    def lt(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.lt, other, t_val, f_val)

    def le(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.le, other, t_val, f_val)

    def eq(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.eq, other, t_val, f_val)

    def ne(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.ne, other, t_val, f_val)

    def gt(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.gt, other, t_val, f_val)

    def ge(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.ge, other, t_val, f_val)

    def even(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        >>> H((-4, -2, 0, 1, 2, 3)).even()
        H({1: 4, 0: 2})
        """

        def is_even(a, _):
            return a % 2 == 0

        return self.filter(is_even, 0, t_val, f_val)

    def odd(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        >>> H((-4, -2, 0, 1, 2, 3)).odd()
        H({1: 2, 0: 4})
        """

        def is_odd(a, _):
            return a % 2 != 0

        return self.filter(is_odd, 0, t_val, f_val)

    def concat(self, other: SourceT) -> "H":
        """
        TODO
        """
        if isinstance(other, int):
            other = (other,)
        elif isinstance(other, collections.abc.Mapping):
            other = other.items()

        return H(itertools.chain(self.items(), cast(Iterable, other)))

    def counts(self) -> Iterator[int]:
        "More descriptive synonym for :meth:`values`."
        return self.values()

    def faces(self) -> Iterator[int]:
        "More descriptive synonym for :meth:`keys`."
        return self.keys()

    def avg(self) -> float:
        numerator = 0
        denominator = 0

        for face, count in self.items():
            numerator += face * count
            denominator += count

        return numerator / (denominator if denominator else 1)

    def data(
        self, relative: bool = False, fill_values: Optional[Mapping[int, int]] = None
    ) -> Iterable[Tuple[int, float]]:
        """
        TODO
        """
        if fill_values is None:
            fill_values = {}

        total = sum(self.counts()) if relative else 1
        faces = sorted(set(itertools.chain(fill_values, self.faces())), reverse=True)

        return (
            (face, (self[face] if face in self else fill_values[face]) / (total or 1))
            for face in faces
        )

    def data_xy(
        self, relative: bool = False, fill_values: Optional[Mapping[int, int]] = None
    ) -> Tuple[Iterable[int], Iterable[float]]:
        """
        TODO
        """
        return cast(
            Tuple[Iterable[int], Iterable[float]],
            zip(*self.data(relative, fill_values)),
        )

    def format(
        self,
        fill_values: Optional[Mapping[int, int]] = None,
        width: int = 0,
        sep: str = os.linesep,
    ) -> str:
        """
        TODO
        """
        if width <= 0:
            return "{{avg: {:.2f}, {}}}".format(
                self.avg(),
                ", ".join(
                    "{}:{:7.2%}".format(val, pct)
                    for val, pct in self.data(relative=True)
                ),
            )
        else:
            w = width - 15

            def lines():
                yield "avg | {:7.2f}".format(self.avg())

                for face, percentage in self.data(
                    relative=True, fill_values=fill_values
                ):
                    ticks = int(w * percentage)
                    yield "{: 3} | {:7.2%} |{}".format(face, percentage, "#" * ticks)

            return sep.join(lines())

    def within(self, lo: int, hi: int, other: OperandT = 0) -> "H":
        """
        Shorthand for `self.apply(within(lo, hi), other)`.
        """
        return self.apply(within(lo, hi), other)


class D:
    """
    An immutable container of convenience for zero or more histograms supporting group
    operations. The vector can be de-normalized (flattened) to a single histogram,
    either explicitly via the :meth:`h` method, or by using binary arithmetic
    operations. Unary operators and the `@` operator result in new `D` objects. If one
    of `args` is an `int`, it is passed to the constructor for :class:`H`.

    >>> D(6)
    D(6)
    >>> d6 = _
    >>> D(d6, d6)  # 2d6
    D(6, 6)
    >>> 2@d6  # also 2d6
    D(6, 6)
    >>> -(2@d6)
    D(-6, -6)
    >>> 2@(2@d6)
    D(6, 6, 6, 6)
    >>> 2@(2@d6) == 4@d6
    True

    Arithmetic operators involving `D` objects result in a :class:`H`:

    >>> 2 * D(8) - 1
    H({15: 1, 13: 1, 11: 1, 9: 1, 7: 1, 5: 1, 3: 1, 1: 1})
    >>> d6 + d6
    H({12: 1, 11: 2, 10: 3, 9: 4, 8: 5, 7: 6, 6: 5, 5: 4, 4: 3, 3: 2, 2: 1})

    Comparisons between `D`s and :class:`H`s still work:

    >>> 3@d6 == H(6) + H(6) + H(6)
    True

    For objects containing more than one :class:`H`, slicing grabs a subset of dice
    from highest values to lowest.

    >>> (3@d6)[:2]  # best two dice of 3d6
    H({12: 16, 11: 27, 10: 34, 9: 36, 8: 34, 7: 27, 6: 19, 5: 12, 4: 7, 3: 3, 2: 1})
    >>> print(_.format(width=65))
    avg |    8.46
     12 |   7.41% |###
     11 |  12.50% |######
     10 |  15.74% |#######
      9 |  16.67% |########
      8 |  15.74% |#######
      7 |  12.50% |######
      6 |   8.80% |####
      5 |   5.56% |##
      4 |   3.24% |#
      3 |   1.39% |
      2 |   0.46% |

    >>> (3@d6)[-2:]  # worst two dice of 3d6
    H({12: 1, 11: 3, 10: 7, 9: 12, 8: 19, 7: 27, 6: 34, 5: 36, 4: 34, 3: 27, 2: 16})
    >>> print(_.format(width=65))
    avg |    5.54
     12 |   0.46% |
     11 |   1.39% |
     10 |   3.24% |#
      9 |   5.56% |##
      8 |   8.80% |####
      7 |  12.50% |######
      6 |  15.74% |#######
      5 |  16.67% |########
      4 |  15.74% |#######
      3 |  12.50% |######
      2 |   7.41% |###
    """

    # ---- Types -----------------------------------------------------------------------

    OperandT = Union[int, "D"]

    # ---- Constructor -----------------------------------------------------------------

    def __init__(self, *args: Union[int, "D", "H"]) -> None:
        super().__init__()

        def _gen_hs():
            for a in args:
                if isinstance(a, int):
                    yield H(a)
                elif isinstance(a, H):
                    yield a
                elif isinstance(a, D):
                    for h in a._hs:  # pylint: disable=protected-access
                        yield h
                else:
                    raise TypeError(
                        "type {} incompatible initializer for {}".format(
                            type(a), type(self)
                        )
                    )

        hs = list(h for h in _gen_hs() if h)
        hs.sort(key=lambda h: tuple(h.items()))
        self._hs = tuple(hs)

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(
                str(h._simple_init) if h._simple_init is not None else repr(h)
                for h in self._hs
            ),
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, D):
            return operator.eq(self._hs, other._hs)
        else:
            return NotImplemented

    def __ne__(self, other) -> bool:
        if isinstance(other, D):
            return operator.ne(self._hs, other._hs)
        else:
            return NotImplemented

    def __len__(self) -> int:
        return len(self._hs)

    def __getitem__(self, key: Union[int, slice]) -> "H":
        if isinstance(key, int):
            return self._hs[key]
        elif isinstance(key, slice):
            groups = tuple(
                (h, sum(1 for _ in hs)) for h, hs in itertools.groupby(self._hs)
            )

            if len(groups) <= 1:
                return H(
                    (sum(operator.getitem(faces, key)), count)
                    for h, n in groups
                    for faces, count in _combinations_with_counts(h, n)
                )
            else:
                return H(
                    (
                        sum(
                            operator.getitem(
                                sorted(itertools.chain(*faces), reverse=True), key
                            )
                        ),
                        functools.reduce(operator.mul, counts),
                    )
                    for faces, counts in (
                        zip(*v)
                        for v in itertools.product(
                            *(_combinations_with_counts(h, n) for h, n in groups)
                        )
                    )
                )
        else:
            return NotImplemented

    def __iter__(self) -> Iterator[H]:
        return iter(self._hs)

    def __add__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: int) -> "H":
        try:
            return self.rapply(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: int) -> "H":
        try:
            return self.rapply(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.mul, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: int) -> "H":
        try:
            return self.rapply(operator.mul, other)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: int) -> "D":
        if not isinstance(other, int):
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")

        return D(*itertools.chain.from_iterable(itertools.repeat(self._hs, other)))

    def __rmatmul__(self, other: int) -> "D":
        return self.__matmul__(other)

    def __floordiv__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: int) -> "H":
        try:
            return self.rapply(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: int) -> "H":
        try:
            return self.rapply(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: int) -> "H":
        try:
            return self.rapply(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __rand__(self, other: int) -> "H":
        try:
            return self.rapply(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __xor__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: int) -> "H":
        try:
            return self.rapply(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __or__(self, other: OperandT) -> "H":
        try:
            return self.apply(operator.or_, other)
        except NotImplementedError:
            return NotImplemented

    def __ror__(self, other: int) -> "H":
        try:
            return self.rapply(operator.or_, other)
        except NotImplementedError:
            return NotImplemented

    def __neg__(self) -> "D":
        return D(*(operator.neg(h) for h in self._hs))

    def __pos__(self) -> "D":
        return D(*(operator.pos(h) for h in self._hs))

    def __abs__(self) -> "D":
        return D(*(operator.abs(h) for h in self._hs))

    # ---- Methods ---------------------------------------------------------------------

    def h(self) -> "H":
        """
        TODO
        """
        return cast(H, sum(self._hs) if self._hs else H(()))

    def apply(self, oper: Union[_IntOperatorT, H.OperatorLT], other: OperandT) -> "H":
        """
        TODO
        """
        oper = cast(Callable, oper)  # not sure why this is necessary?

        if isinstance(other, (int, D)):
            return self.h().apply(oper, other)
        else:
            raise NotImplementedError

    def rapply(self, oper: H.OperatorRT, other: int) -> "H":
        """
        TODO
        """
        oper = cast(Callable, oper)  # not sure why this is necessary?

        if isinstance(other, int):
            return self.h().rapply(oper, other)
        else:
            raise NotImplementedError

    def filter(
        self,
        predicate: _IntPredicateT,
        other: OperandT,
        t_val: Optional[int] = None,
        f_val: Optional[int] = None,
    ) -> "H":
        """
        TODO
        """
        return self.h().filter(predicate, other, t_val, f_val)

    def lt(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.lt, other, t_val, f_val)

    def le(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.le, other, t_val, f_val)

    def eq(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.eq, other, t_val, f_val)

    def ne(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.ne, other, t_val, f_val)

    def gt(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.gt, other, t_val, f_val)

    def ge(
        self, other: OperandT, t_val: Optional[int] = 1, f_val: Optional[int] = 0
    ) -> "H":
        """
        TODO
        """
        return self.filter(operator.ge, other, t_val, f_val)

    def even(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        TODO

        >>> D(H((-4, -2, 0, 1, 2, 3))).even()
        H({1: 4, 0: 2})
        """

        def is_even(a, _):
            return a % 2 == 0

        return self.filter(is_even, 0, t_val, f_val)

    def odd(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        TODO

        >>> D(H((-4, -2, 0, 1, 2, 3))).odd()
        H({1: 2, 0: 4})
        """

        def is_odd(a, _):
            return a % 2 != 0

        return self.filter(is_odd, 0, t_val, f_val)

    def within(self, lo: int, hi: int, other: OperandT = 0) -> "H":
        """
        Shorthand for `self.apply(within(lo, hi), other)`.
        """
        return self.apply(within(lo, hi), other)


# ---- Functions -----------------------------------------------------------------------


def config_logging() -> None:
    log_lvl_name = os.environ.get(_LOG_LVL_ENV) or _LOG_LVL_DFLT

    try:
        log_lvl = int(log_lvl_name, 0)
    except (TypeError, ValueError):
        log_lvl = 0
        log_lvl = logging.getLevelName(log_lvl_name)

    log_fmt = os.environ.get(_LOG_FMT_ENV, _LOG_FMT_DFLT)
    logging.basicConfig(format=log_fmt)
    logging.getLogger().setLevel(log_lvl)
    from . import LOGGER

    LOGGER.setLevel(log_lvl)


def substitute(h: Union[H, H.AbleT], explode_on: _ExplodeOnT) -> H:
    raise NotImplementedError


def explode(h: Union[H, H.AbleT], explode_on: _ExplodeOnT) -> H:
    """
    TODO

    >>> def explode_max(h: H, face: int, depth: int):
    ...   return depth < 2 and face == max(h)
    >>> d6 = D(6)
    >>> explode(d6, explode_max)
    H({18: 1, 17: 1, 16: 1, 15: 1, 14: 1, 13: 1, 11: 6, 10: 6, 9: 6, 8: 6, 7: 6, 5: 36, 4: 36, 3: 36, 2: 36, 1: 36})
    """
    if isinstance(h, H.AbleT):
        _h = h.h()
    else:
        _h = h

    def _explode(depth: int) -> H:
        exploding_faces = {face for face in _h if explode_on(_h, face, depth)}

        if exploding_faces:
            exploded_h = _explode(depth + 1)
            exploded_h_sum = sum(exploded_h.counts())
            values = collections.defaultdict(int)  # type: DefaultDict[int, int]

            for face, count in _h.items():
                if face in exploding_faces:
                    for exploded_face, exploded_count in (exploded_h * count).items():
                        values[face + exploded_face] += exploded_count
                else:
                    values[face] += exploded_h_sum * count

            return H(values)
        else:
            return _h

    return _explode(0)


def within(lo: int, hi: int) -> _IntOperatorT:
    """
    Returns a filter function that—given two `int`s—will compute the difference and
    return -1 if that difference is less than `lo`, 0 if it is between `lo` and `hi`
    (inclusive), and 1 if it is greater than `hi`. This can be used to compare a
    :class:`D` or :class:`H` to that range:

    >>> d6 = D(6)
    >>> (2@d6).within(7, 9, 0)  # 2d6 w/in 7-9
    H({1: 6, 0: 15, -1: 15})
    >>> print(_.format(width=65))
    avg |   -0.25
      1 |  16.67% |########
      0 |  41.67% |####################
     -1 |  41.67% |####################

    >>> (2@d6).within(0, 0, 2@d6)  # 2d6 vs. 2d6 identical rolls
    H({1: 575, 0: 146, -1: 575})
    >>> print(_.format(width=65))
    avg |    0.00
      1 |  44.37% |######################
      0 |  11.27% |#####
     -1 |  44.37% |######################

    >>> d6.within(-1, 1, d6)  # 1d6 vs. 1d6 w/in 1 of each other
    H({1: 10, 0: 16, -1: 10})
    >>> print(_.format(width=65))
    avg |    0.00
      1 |  27.78% |#############
      0 |  44.44% |######################
     -1 |  27.78% |#############
    """
    assert lo <= hi

    def _cmp(a: int, b: int):
        diff = a - b

        if diff < lo:
            return -1
        elif diff > hi:
            return 1
        else:
            return 0

    setattr(_cmp, "lo", lo)
    setattr(_cmp, "hi", hi)

    return _cmp


def _combinations_with_counts(h: H, n: int) -> Iterator[Tuple[Tuple[int, ...], int]]:
    for faces in itertools.combinations_with_replacement(h, n):
        total_count = 1

        for face in faces:
            total_count *= h[face]

        num_combinations_denominator = 1

        for _, g in itertools.groupby(faces):
            num_combinations_denominator *= math.factorial(sum(1 for _ in g))

        yield faces, total_count * math.factorial(
            len(faces)
        ) // num_combinations_denominator

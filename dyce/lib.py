# -*- encoding: utf-8; test-case-name: tests.test_main -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` files for rights and restrictions governing use of this software. All rights
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
    List,
    Mapping,
    Optional,
    TextIO,
    Tuple,
    Union,
    cast,
)
from typing_extensions import Protocol, runtime_checkable


# ---- Imports -------------------------------------------------------------------------


import collections.abc
import itertools
import logging
import operator
import os
import sys
import textwrap


# ---- Data ----------------------------------------------------------------------------


__all__ = ("D", "H", "print_in_rows", "within")

_LOGGER = logging.getLogger(__name__)

_LOG_FMT_ENV = "LOG_FMT"
_LOG_FMT_DFLT = "%(message)s"
_LOG_LVL_ENV = "LOG_LVL"
_LOG_LVL_DFLT = logging.getLevelName(logging.WARNING)

_IntOperatorT = Callable[[int, int], int]
_IntPredicateT = Callable[[int, int], bool]

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
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
    >>> print(_.format(width=65))
      2 |   2.78% |#
      3 |   5.56% |##
      4 |   8.33% |####
      5 |  11.11% |#####
      6 |  13.89% |######
      7 |  16.67% |########
      8 |  13.89% |######
      9 |  11.11% |#####
     10 |   8.33% |####
     11 |   5.56% |##
     12 |   2.78% |#
    >>> 2@h6 == h6 + h6
    True

    >>> len(2@h6)  # number of distinct values
    11
    >>> sum((2@h6).counts())  # total number of combinations
    36

    >>> h6.ne(h6)  # where a first d6 shows a different value than a second d6
    H({0: 6, 1: 30})
    >>> print(_.format(width=65))
      0 |  16.67% |########
      1 |  83.33% |#########################################

    >>> h6.lt(h6)  # where a first d6 shows less than a second
    H({0: 21, 1: 15})
    >>> print(_.format(width=65))
      0 |  58.33% |#############################
      1 |  41.67% |####################

    Some esoteric things can be captured through careful enumeration. For example,
    re-rolling a 1 that appears on a first d20 roll could be captured by:

    >>> H(itertools.chain(((n, 20) for n in range(2, 21)), range(1, 21)))
    H({1: 1, 2: 21, 3: 21, 4: 21, 5: 21, 6: 21, 7: 21, 8: 21, 9: 21, 10: 21, 11: 21, 12: 21, 13: 21, 14: 21, 15: 21, 16: 21, 17: 21, 18: 21, 19: 21, 20: 21})
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
                    val, num = value  # pylint: disable=unpacking-non-sequence
                    h[val] += num
                else:
                    h[value] += 1

            values = h

        self._h = collections.OrderedDict(
            (value, values[value]) for value in sorted(values)
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
        h = H((operator.neg(val), num) for val, num in self.items())

        if self._simple_init is not None:
            h._simple_init = operator.neg(self._simple_init)

        return h

    def __pos__(self) -> "H":
        h = H((operator.pos(val), num) for val, num in self.items())

        if self._simple_init is not None:
            h._simple_init = operator.pos(self._simple_init)

        return h

    def __abs__(self) -> "H":
        h = H((operator.abs(val), num) for val, num in self.items())

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
            return H((int(oper(val, other)), num) for val, num in self.items())

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
            return H((int(oper(other, val)), num) for val, num in self.items())

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

        for val, num in self.items():
            numerator += val * num
            denominator += num

        return numerator / (denominator if denominator else 1)

    def data(
        self, relative: bool = False, fillvalues: Optional[Mapping[int, int]] = None
    ) -> Iterable[Tuple[int, float]]:
        """
        TODO
        """
        if fillvalues is None:
            fillvalues = {}

        total = sum(self.counts()) if relative else 1
        faces = sorted(set(itertools.chain(fillvalues, self.faces())))

        return (
            (face, (self[face] if face in self else fillvalues[face]) / (total or 1))
            for face in faces
        )

    def data_xy(
        self, relative: bool = False, fillvalues: Optional[Mapping[int, int]] = None
    ) -> Tuple[Iterable[int], Iterable[float]]:
        """
        TODO
        """
        return cast(
            Tuple[Iterable[int], Iterable[float]], zip(*self.data(relative, fillvalues))
        )

    def format(
        self,
        fillvalues: Optional[Mapping[int, int]] = None,
        width: int = 115,
        sep: str = os.linesep,
    ) -> str:
        """
        TODO
        """
        w = width - 15
        fmt = "{: 3} | {:7.2%} |{}"

        def lines():
            for val, percentage in self.data(relative=True, fillvalues=fillvalues):
                ticks = int(w * percentage)
                yield fmt.format(val, percentage, "#" * ticks)

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
    H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})
    >>> d6 + d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    Comparisons between `D`s and :class:`H`s still work:

    >>> 3@d6 == H(6) + H(6) + H(6)
    True

    For objects containing more than one :class:`H`, slicing grabs a subset of dice
    from highest values to lowest.

    >>> (3@d6)[:2]  # best two dice of 3d6
    H({2: 1, 3: 3, 4: 7, 5: 12, 6: 19, 7: 27, 8: 34, 9: 36, 10: 34, 11: 27, 12: 16})
    >>> print(_.format(width=65))
      2 |   0.46% |
      3 |   1.39% |
      4 |   3.24% |#
      5 |   5.56% |##
      6 |   8.80% |####
      7 |  12.50% |######
      8 |  15.74% |#######
      9 |  16.67% |########
     10 |  15.74% |#######
     11 |  12.50% |######
     12 |   7.41% |###

    >>> (3@d6)[-2:]  # worst two dice of 3d6
    H({2: 16, 3: 27, 4: 34, 5: 36, 6: 34, 7: 27, 8: 19, 9: 12, 10: 7, 11: 3, 12: 1})
    >>> print(_.format(width=65))
      2 |   7.41% |###
      3 |  12.50% |######
      4 |  15.74% |#######
      5 |  16.67% |########
      6 |  15.74% |#######
      7 |  12.50% |######
      8 |   8.80% |####
      9 |   5.56% |##
     10 |   3.24% |#
     11 |   1.39% |
     12 |   0.46% |
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

        self._hs = tuple(h for h in _gen_hs() if h)

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
            return operator.getitem(self._hs, key)
        elif isinstance(key, slice):

            def gen_sums():
                if len(operator.getitem(self._hs, key)) > 0:
                    for rolls in itertools.product(*self._hs):
                        sub_rolls = operator.getitem(sorted(rolls, reverse=True), key)
                        yield sum(sub_rolls)

            return H(gen_sums())
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
        log_lvl = logging.getLevelName(log_lvl_name)  # type: ignore

    log_fmt = os.environ.get(_LOG_FMT_ENV, _LOG_FMT_DFLT)
    logging.basicConfig(format=log_fmt)
    logging.getLogger().setLevel(log_lvl)
    from . import LOGGER

    LOGGER.setLevel(log_lvl)


def print_in_rows(
    rolls: Iterable[Union[str, H, Tuple[H, Optional[str]]]],
    columns: int = 3,
    fillvalues: Optional[Mapping[int, int]] = None,
    out: TextIO = sys.stdout,
) -> None:
    """
    TODO
    """
    if fillvalues is None:
        fillvalues = {}

    col_width = _ROW_WIDTH // columns - 4
    paragraphs = []

    for roll in rolls:
        if isinstance(roll, str):
            paragraphs.append([roll])
            paragraphs.extend([" - - - "] for _ in range(columns - 1))
        else:
            if isinstance(roll, H):
                h, desc = roll, None
            else:
                h, desc = roll

            paragraph = []  # type: List[str]

            if desc is not None:
                if len(desc) > col_width:
                    paragraph.extend(textwrap.wrap(desc, col_width))
                else:
                    paragraph.append(desc)

                paragraph.append("- " * ((col_width - 1) // 2) + "-")

            paragraph.extend(
                h.format(fillvalues=fillvalues, width=col_width).split(os.linesep)
            )
            paragraphs.append(paragraph)

    num_paras = len(paragraphs)
    rows = num_paras // columns + int(bool(num_paras % columns))
    col_fmt = "{{: <{}}}".format(col_width)
    line_fmt = "| " + " | ".join(col_fmt for _ in range(columns)) + " |"
    sep = "+-" + "-+-".join("-" * col_width for _ in range(columns)) + "-+"
    print(sep, file=out)

    for row in range(rows):
        row_paras = paragraphs[row * columns : row * columns + columns]

        for row_paras_lines in itertools.zip_longest(*row_paras, fillvalue=""):
            row_paras_lines = list(row_paras_lines)
            row_paras_lines.extend("" for _ in range(columns - len(row_paras_lines)))
            print(line_fmt.format(*row_paras_lines), file=out)

        print(sep, file=out)


def within(lo: int, hi: int) -> _IntOperatorT:
    """
    Returns a filter function that—given two `int`s—will compute the difference and
    return -1 if that difference is less than `lo`, 0 if it is between `lo` and `hi`
    (inclusive), and 1 if it is greater than `hi`. This can be used to compare a
    :class:`D` or :class:`H` to that range:

    >>> d6 = D(6)
    >>> (2@d6).within(7, 9, 0)  # 2d6 w/in 7-9
    H({-1: 15, 0: 15, 1: 6})
    >>> print(_.format(width=65))
     -1 |  41.67% |####################
      0 |  41.67% |####################
      1 |  16.67% |########

    >>> (2@d6).within(0, 0, 2@d6)  # 2d6 vs. 2d6 identical rolls
    H({-1: 575, 0: 146, 1: 575})
    >>> print(_.format(width=65))
     -1 |  44.37% |######################
      0 |  11.27% |#####
      1 |  44.37% |######################

    >>> d6.within(-1, 1, d6)  # 1d6 vs. 1d6 w/in 1 of each other
    H({-1: 10, 0: 16, 1: 10})
    >>> print(_.format(width=65))
     -1 |  27.78% |#############
      0 |  44.44% |######################
      1 |  27.78% |#############
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

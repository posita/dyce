# -*- encoding: utf-8 -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If that file is missing or appears to be
modified from its original, then please contact the author before viewing or using this
software in any capacity.
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
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Protocol, runtime_checkable

import collections.abc
import functools
import itertools
import math
import operator
import os
import random

__all__ = ("D", "H")


# ---- Data ----------------------------------------------------------------------------


_T = TypeVar("_T")
_GetItemT = Union[int, slice]
_IntOperatorT = Callable[[int, int], int]
_IntPredicateT = Callable[[int, int], bool]
_ExpandT = Callable[["H", int], Optional["H"]]
_CoalesceT = Callable[["H", int], "H"]

try:
    _ROW_WIDTH = os.get_terminal_size().columns
except OSError:
    try:
        _ROW_WIDTH = int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        _ROW_WIDTH = 88


# ---- Classes -------------------------------------------------------------------------


class H(Mapping[int, int]):
    """
    A histogram supporting arithmetic operations. In its most explicit form, ``values``
    maps values to counts.

    Modeling a single six-sided die (1d6) can be expressed as:

    >>> h6 = H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    An iterable of pairs can also be used (similar to :obj:`dict`):

    >>> h6 == H(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)))
    True

    Two shorthands are provided. If an iterable of :obj:`int` s is given, counts of one
    will be assumed:

    >>> h6 == H((1, 2, 3, 4, 5, 6))
    True

    If an :obj:`int` is given, it is shorthand for creating a sequential range ``[1,
    values]`` (or ``[values, -1]`` if ``values`` is negative):

    >>> h6 == H(6)
    True

    Simple indexes can be used to look up a value’s count:

    >>> h6[5]
    1

    Most arithmetic operators are supported and do what one would expect. If the operand
    is an :obj:`int`, the operator applies to the values:

    >>> h6 + 4
    H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})
    >>> h6 * -1
    H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})
    >>> h6 * -1 == -h6
    True
    >>> h6 * -1 == H(-6)
    True

    If the operand is another histogram, combinations are computed. Modeling the sum of
    two six-sided dice (2d6) can be expressed as:

    >>> h6 + h6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
    >>> print(_.format(width=65))
    avg |    7.00
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

    To accumulate “multiples” of a histogram, use the matrix multiplication operator:

    >>> 3@h6 == h6 + h6 + h6
    True

    :func:`len` can be used to show the number of distinct values:

    >>> len(2@h6)
    11

    :meth:`counts` can be used to show the total number of combinations:

    >>> sum((2@h6).counts())
    36

    Histograms provide common comparators (e.g., :meth:`eq` :meth:`ne`, etc.). One way
    to count how often a first six-sided die shows a different value than a second is:

    >>> h6.ne(h6)
    H({0: 6, 1: 30})
    >>> print(_.format(width=65))
    avg |    0.83
      0 |  16.67% |########
      1 |  83.33% |#########################################

    Or how often a first six-sided die shows a value less than a second:

    >>> h6.lt(h6)
    H({0: 21, 1: 15})
    >>> print(_.format(width=65))
    avg |    0.42
      0 |  58.33% |#############################
      1 |  41.67% |####################

    Note, however, that parentheses might be necessary to enforce the desired order of
    operations:

    >>> 2@h6.le(7)  # probably not what was intended
    H({2: 36})
    >>> 2@h6.le(7) == 2@(h6.lt(7))
    True
    >>> (2@h6).le(7)
    H({0: 15, 1: 21})
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
            if values < 0:
                self._simple_init = values
                values = range(-1, values - 1, -1)
            elif values > 0:
                self._simple_init = values
                values = range(1, values + 1)
            else:
                values = {}
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
            (face, values[face]) for face in sorted(values)
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
            return self.map(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.add, other)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.sub, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.mul, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.mul, other)
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
            return self.map(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.mod, other)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.pow, other)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __rand__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.and_, other)
        except NotImplementedError:
            return NotImplemented

    def __xor__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.xor, other)
        except NotImplementedError:
            return NotImplemented

    def __or__(self, other: OperandT) -> "H":
        try:
            return self.map(operator.or_, other)
        except NotImplementedError:
            return NotImplemented

    def __ror__(self, other: OperandT) -> "H":
        try:
            return self.rmap(operator.or_, other)
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

    def filter(
        self,
        predicate: _IntPredicateT,
        other: OperandT,
        t_val: Optional[int] = None,
        f_val: Optional[int] = None,
    ) -> "H":
        """
        Applies *predicate* to each face of the histogram paired with *other*. If the result
        is ``True``, *t_val* is returned, if set. Otherwise the face is returned. If the
        result is ``False``, *f_val* is returned, if set. Otherwise, the other value is
        returned.

        >>> h6 = H(6)
        >>> h6.filter(operator.gt, 3)
        H({3: 3, 4: 1, 5: 1, 6: 1})

        >>> h6.filter(operator.gt, 3, f_val=0)
        H({0: 3, 4: 1, 5: 1, 6: 1})

        >>> h6.filter(operator.gt, 3, t_val=1, f_val=0)
        H({0: 3, 1: 3})

        Note that shorthands exist for many comparison operators:

        >>> h6.gt(h6) == h6.filter(operator.gt, h6, t_val=1, f_val=0)
        True
        >>> h6.le(h6, t_val=1, f_val=-1) == h6.filter(operator.le, h6, t_val=1, f_val=-1)
        True
        """

        def _resolve(a: int, b: int):
            if predicate(a, b):
                return a if t_val is None else t_val
            else:
                return b if f_val is None else f_val

        return self.map(_resolve, other)

    def map(self, oper: _IntOperatorT, other: OperandT) -> "H":
        """
        Applies *oper* to each face of the histogram paired with *other*:

        >>> h6 = H(6)
        >>> h6.map(operator.mul, -1)
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})

        >>> h6.map(operator.add, h6)
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        Note that shorthands exist for many arithmetic operators:

        >>> h6 * -1 == h6.map(operator.mul, -1)
        True
        >>> h6 + h6 == h6.map(operator.add, h6)
        True
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

    def rmap(self, oper: _IntOperatorT, other: OperandT) -> "H":
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

    def lt(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.lt, other, t_val, f_val)``:

        >>> H(6).lt(3)
        H({0: 4, 1: 2})
        """
        return self.filter(operator.lt, other, t_val, f_val)

    def le(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.le, other, t_val, f_val)``.

        >>> H(6).le(3)
        H({0: 3, 1: 3})
        """
        return self.filter(operator.le, other, t_val, f_val)

    def eq(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.eq, other, t_val, f_val)``.

        >>> H(6).eq(3)
        H({0: 5, 1: 1})
        """
        return self.filter(operator.eq, other, t_val, f_val)

    def ne(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.ne, other, t_val, f_val)``.

        >>> H(6).ne(3)
        H({0: 1, 1: 5})
        """
        return self.filter(operator.ne, other, t_val, f_val)

    def gt(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.gt, other, t_val, f_val)``.

        >>> H(6).gt(3)
        H({0: 3, 1: 3})
        """
        return self.filter(operator.gt, other, t_val, f_val)

    def ge(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.filter(operator.ge, other, t_val, f_val)``.

        >>> H(6).ge(3)
        H({0: 2, 1: 4})
        """
        return self.filter(operator.ge, other, t_val, f_val)

    def even(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        >>> H((-4, -2, 0, 1, 2, 3)).even()
        H({0: 2, 1: 4})
        """

        def is_even(a, _):
            return a % 2 == 0

        return self.filter(is_even, 0, t_val, f_val)

    def odd(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        >>> H((-4, -2, 0, 1, 2, 3)).odd()
        H({0: 4, 1: 2})
        """

        def is_odd(a, _):
            return a % 2 != 0

        return self.filter(is_odd, 0, t_val, f_val)

    def avg(self) -> float:
        numerator = 0
        denominator = 0

        for face, count in self.items():
            numerator += face * count
            denominator += count

        return numerator / (denominator if denominator else 1)

    def concat(self, other: SourceT) -> "H":
        """
        Accumulates counts:

        >>> H(4).concat(H(6))
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})
        """
        if isinstance(other, int):
            other = (other,)
        elif isinstance(other, collections.abc.Mapping):
            other = other.items()

        return H(itertools.chain(self.items(), cast(Iterable, other)))

    def counts(self) -> Iterator[int]:
        "More descriptive synonym for :meth:`values`."
        return self.values()

    def data(
        self,
        relative: bool = False,
        fill_values: Optional[Mapping[int, int]] = None,
    ) -> Iterator[Tuple[int, float]]:
        """
        Presentation helper function that returns an iterator for each face/frequency pair:

        >>> h6 = H(6)
        >>> list(h6.gt(3).data())
        [(0, 3.0), (1, 3.0)]
        >>> list(h6.gt(3).data(relative=True))
        [(0, 0.5), (1, 0.5)]

        If provided, *fill_values* supplies defaults for any missing face values:

        >>> list(h6.gt(7).data())
        [(0, 6.0)]
        >>> list(h6.gt(7).data(fill_values={1: 0, 0: 0}))
        [(0, 6.0), (1, 0.0)]
        """
        if fill_values is None:
            fill_values = {}

        total = sum(self.counts()) if relative else 1
        faces = sorted(set(itertools.chain(fill_values, self.faces())))

        return (
            (face, (self[face] if face in self else fill_values[face]) / (total or 1))
            for face in faces
        )

    def data_xy(
        self,
        relative: bool = False,
        fill_values: Optional[Mapping[int, int]] = None,
    ) -> Tuple[Tuple[int, ...], Tuple[float, ...]]:
        """
        Presentation helper function that returns an iterator for a “zipped” arrangement of
        :meth:`data`:

        >>> h6 = H(6)
        >>> list(h6.data())
        [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0)]
        >>> h6.data_xy()
        ((1, 2, 3, 4, 5, 6), (1.0, 1.0, 1.0, 1.0, 1.0, 1.0))
        """
        return cast(
            Tuple[Tuple[int, ...], Tuple[float, ...]],
            tuple(zip(*self.data(relative, fill_values))),
        )

    def faces(self) -> Iterator[int]:
        "More descriptive synonym for :meth:`keys`."
        return self.keys()

    def format(
        self,
        fill_values: Optional[Mapping[int, int]] = None,
        width: int = _ROW_WIDTH,
        tick: str = "#",
        sep: str = os.linesep,
    ) -> str:
        """
        Returns a formatted string representation of the histogram. If provided,
        *fill_values* supplies defaults for any missing face values. If *width* is
        greater than zero, a horizontal bar ASCII graph is printed using *tick* and
        *sep* (which are otherwise ignored if *width* is zero or less).

        >>> print(H(6).format(width=0))
        {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}
        >>> print((2@H(6)).format(fill_values={i: 0 for i in range(1, 21)}, width=65, tick="@"))
        avg |    7.00
          1 |   0.00% |
          2 |   2.78% |@
          3 |   5.56% |@@
          4 |   8.33% |@@@@
          5 |  11.11% |@@@@@
          6 |  13.89% |@@@@@@
          7 |  16.67% |@@@@@@@@
          8 |  13.89% |@@@@@@
          9 |  11.11% |@@@@@
         10 |   8.33% |@@@@
         11 |   5.56% |@@
         12 |   2.78% |@
         13 |   0.00% |
         14 |   0.00% |
         15 |   0.00% |
         16 |   0.00% |
         17 |   0.00% |
         18 |   0.00% |
         19 |   0.00% |
         20 |   0.00% |
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
                    yield "{: 3} | {:7.2%} |{}".format(face, percentage, tick * ticks)

            return sep.join(lines())

    def roll(self) -> int:
        """
        Returns a (weighted) random face.
        """
        val = random.randrange(0, sum(self.counts()))
        total = 0

        for face, count in self.items():
            total += count

            if val < total:
                return face

        assert False, "val ({}) ≥ total ({})".format(val, total)

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: Optional[_CoalesceT] = None,
        max_depth: int = 1,
    ) -> "H":
        """
        Calls :obj:`expand` on each face, recursively up to *max_depth* times. If *expand*
        returns non-``None``, *coalesce* is called on the face and the expanded value,
        and the return value is folded into result. The default behavior for *coalesce*
        is to replace the face with the expanded value.

        This can be used to model complex rules. The following models re-rolling a value of
        1 on the first roll:

        >>> def reroll_one(h: H, face: int) -> Optional[H]:
        ...   return h if face == 1 else None
        >>> D(6).substitute(reroll_one)
        H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

        The following approximates an exploding three-sided die (i.e., if the greatest
        value comes up, the die is rolled again and its value is added to the total):

        >>> def reroll_greatest(h: H, face: int) -> Optional[H]:
        ...   return h if face == max(h) else None
        >>> D(3).substitute(reroll_greatest, operator.add, max_depth=4)
        H({1: 81, 2: 81, 4: 27, 5: 27, 7: 9, 8: 9, 10: 3, 11: 3, 13: 1, 14: 1, 15: 1})

        Consider the following rules:

          1. Start with a total of zero.
          2. Roll a six-sided die. Add the value to the total. If the result is a six, go
             to step 3. Otherwise stop.
          3. Roll a four-sided die. Add the value to the total. If the result is a four, go
             to step 2. Otherwise stop.

        What is the likelihood of an even final tally? This can be approximated by:

        >>> h4, h6 = H(4), H(6)
        >>> def reroll_greatest_on_h6_h4(h: H, face: int) -> Optional[H]:
        ...   if face == max(h):
        ...     if h == h6: return h4
        ...     if h == h4: return h6
        ...   return None
        >>> h = h6.substitute(reroll_greatest_on_h6_h4, operator.add, max_depth=6)
        >>> h_even = h.even()
        >>> print("{:.3%}".format(h_even.get(1, 0) / sum(h_even.counts())))
        39.131%
        """
        _coalesce = _coalesce_replace if coalesce is None else coalesce

        def _substitute(
            h: H,
            depth: int = 0,
        ) -> H:
            if depth == max_depth:
                return h

            expanded_values = []  # type: List[Tuple[int, int]]
            expanded_histograms = []  # type: List[H]

            for face, count in h.items():
                expanded = expand(h, face)

                if expanded:
                    expanded = _substitute(expanded, depth + 1)
                    expanded = H((f, count * c) for f, c in expanded.items())
                    expanded = _coalesce(expanded, face)
                    expanded_histograms.append(expanded)
                else:
                    expanded_values.append((face, count))

            count_multiplier = (
                sum(itertools.chain(*(ah.counts() for ah in expanded_histograms))) or 1
            )

            return H(
                itertools.chain(
                    ((f, count_multiplier * c) for f, c in expanded_values),
                    *(ah.items() for ah in expanded_histograms)
                )
            )

        return _substitute(self)

    def within(self, lo: int, hi: int, other: OperandT = 0) -> "H":
        """
        Computes the difference between this histogram and *other*. -1 is represents where
        that difference is less than *lo*. 0 represents where that difference between
        *lo* and *hi* (inclusive). 1 represents where that difference is greater than
        *hi*.

        >>> (2@H(6)).within(7, 9)
        H({-1: 15, 0: 15, 1: 6})
        >>> print(_.format(width=65))
        avg |   -0.25
         -1 |  41.67% |####################
          0 |  41.67% |####################
          1 |  16.67% |########

        >>> (3@H(6)).within(-1, 1, 2@H(8))  # 3d6 w/in 1 of 2d8
        H({-1: 3500, 0: 3412, 1: 6912})
        >>> print(_.format(width=65))
        avg |    0.25
         -1 |  25.32% |############
          0 |  24.68% |############
          1 |  50.00% |#########################
        """
        return self.map(_within(lo, hi), other)


class D:
    """
    An immutable container of convenience for zero or more :class:`H` objects supporting
    group operations. The vector can be de-normalized (flattened) to a single histogram,
    either explicitly via the :meth:`h` method, or by using binary arithmetic
    operations. Unary operators and the ``@`` operator result in new :class:`D` objects.
    If one of *args* is an :obj:`int`, it is passed to the constructor for :class:`H`.

    >>> D(6)  # shorthand for D(H(6))
    D(6)
    >>> d6 = _
    >>> -d6
    D(-6)
    >>> D(d6, d6)  # 2d6
    D(6, 6)
    >>> 2@d6  # also 2d6
    D(6, 6)
    >>> 2@(2@d6) == 4@d6
    True
    >>> D(4, D(6, D(8, D(10, D(12, D(20))))))
    D(4, 6, 8, 10, 12, 20)
    >>> sum(_.roll()) in _.h()
    True

    Arithmetic operators involving an :obj:`int` or another :class:`D` object produces a
    :class:`H`:

    >>> d6 + d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
    >>> 2 * D(8) - 1
    H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})

    Comparisons between :class:`D` and :class:`H` still work:

    >>> 3@d6 == H(6) + H(6) + H(6)
    True

    For objects containing more than one :class:`H`, slicing grabs a subset of face
    values from least to greatest. Modeling the sum of the greatest two face values of
    three six-sided dice (3d6) can be expressed as:

    >>> (3@d6)[-2:]
    H({2: 1, 3: 3, 4: 7, 5: 12, 6: 19, 7: 27, 8: 34, 9: 36, 10: 34, 11: 27, 12: 16})
    >>> print(_.format(width=65))
    avg |    8.46
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

    Arbitrary iterables can be used for more flexible selections. Modeling the sum of
    the greatest two and least two face values of ten four-sided dice (10d4) can be
    expressed as:

    >>> (10@D(4))[:2,-2:]
    H({4: 1, 5: 10, 6: 1012, 7: 5030, 8: 51973, 9: 168760, 10: 595004, 11: 168760, 12: 51973, 13: 5030, 14: 1012, 15: 10, 16: 1})
    >>> print(_.format(width=65))
    avg |   10.00
      4 |   0.00% |
      5 |   0.00% |
      6 |   0.10% |
      7 |   0.48% |
      8 |   4.96% |##
      9 |  16.09% |########
     10 |  56.74% |############################
     11 |  16.09% |########
     12 |   4.96% |##
     13 |   0.48% |
     14 |   0.10% |
     15 |   0.00% |
     16 |   0.00% |
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

    def __getitem__(self, key: Union[_GetItemT, Iterable[_GetItemT]]) -> "H":
        if isinstance(key, int):
            return self._hs[key]
        elif isinstance(key, collections.abc.Iterable):
            keys = tuple(key)
        elif isinstance(key, slice):
            keys = (key,)
        else:
            return NotImplemented

        groups = tuple((h, sum(1 for _ in hs)) for h, hs in itertools.groupby(self._hs))

        if len(groups) > 1:
            return H(
                (
                    sum(_getitems(sorted(itertools.chain(*faces)), keys)),
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
            # Optimization: we don’t have to (re-)sort if we only have 0-1 groups, since
            # the return value of _combinations_with_counts is already sorted
            return H(
                (sum(_getitems(faces, keys)), count)
                for h, n in groups
                for faces, count in _combinations_with_counts(h, n)
            )

    def __iter__(self) -> Iterator[H]:
        return iter(self._hs)

    def __add__(self, other: OperandT) -> "H":
        return operator.add(self.h(), other)

    def __radd__(self, other: int) -> "H":
        return operator.add(other, self.h())

    def __sub__(self, other: OperandT) -> "H":
        return operator.sub(self.h(), other)

    def __rsub__(self, other: int) -> "H":
        return operator.sub(other, self.h())

    def __mul__(self, other: OperandT) -> "H":
        return operator.mul(self.h(), other)

    def __rmul__(self, other: int) -> "H":
        return operator.mul(other, self.h())

    def __matmul__(self, other: int) -> "D":
        if not isinstance(other, int):
            return NotImplemented
        elif other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return D(*itertools.chain.from_iterable(itertools.repeat(self._hs, other)))

    def __rmatmul__(self, other: int) -> "D":
        return self.__matmul__(other)

    def __floordiv__(self, other: OperandT) -> "H":
        return operator.floordiv(self.h(), other)

    def __rfloordiv__(self, other: int) -> "H":
        return operator.floordiv(other, self.h())

    def __mod__(self, other: OperandT) -> "H":
        return operator.mod(self.h(), other)

    def __rmod__(self, other: int) -> "H":
        return operator.mod(other, self.h())

    def __pow__(self, other: OperandT) -> "H":
        return operator.pow(self.h(), other)

    def __rpow__(self, other: int) -> "H":
        return operator.pow(other, self.h())

    def __and__(self, other: OperandT) -> "H":
        return operator.and_(self.h(), other)

    def __rand__(self, other: int) -> "H":
        return operator.and_(other, self.h())

    def __xor__(self, other: OperandT) -> "H":
        return operator.xor(self.h(), other)

    def __rxor__(self, other: int) -> "H":
        return operator.xor(other, self.h())

    def __or__(self, other: OperandT) -> "H":
        return operator.or_(self.h(), other)

    def __ror__(self, other: int) -> "H":
        return operator.or_(other, self.h())

    def __neg__(self) -> "D":
        return D(*(operator.neg(h) for h in self._hs))

    def __pos__(self) -> "D":
        return D(*(operator.pos(h) for h in self._hs))

    def __abs__(self) -> "D":
        return D(*(operator.abs(h) for h in self._hs))

    # ---- Methods ---------------------------------------------------------------------

    def h(self) -> "H":
        """
        Combines contained histograms:

        >>> (2@D(6)).h()
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
        """
        return cast(H, sum(self._hs) if self._hs else H(()))

    def lt(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().lt(other, t_val, f_val)``.
        """
        return self.h().lt(other, t_val, f_val)

    def le(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().le(other, t_val, f_val)``.
        """
        return self.h().le(other, t_val, f_val)

    def eq(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().eq(other, t_val, f_val)``.
        """
        return self.h().eq(other, t_val, f_val)

    def ne(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().ne(other, t_val, f_val)``.
        """
        return self.h().ne(other, t_val, f_val)

    def gt(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().gt(other, t_val, f_val)``.
        """
        return self.h().gt(other, t_val, f_val)

    def ge(
        self,
        other: OperandT,
        t_val: Optional[int] = 1,
        f_val: Optional[int] = 0,
    ) -> "H":
        """
        Shorthand for ``self.h().ge(other, t_val, f_val)``.
        """
        return self.h().ge(other, t_val, f_val)

    def even(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        Shorthand for ``self.h().even(t_val, f_val)``.
        """
        return self.h().even(t_val, f_val)

    def odd(self, t_val: Optional[int] = 1, f_val: Optional[int] = 0) -> "H":
        """
        Shorthand for ``self.h().odd(t_val, f_val)``.
        """
        return self.h().odd(t_val, f_val)

    def roll(self) -> Tuple[int, ...]:
        """
        Returns (weighted) random face values from contained histograms.
        """
        return tuple(h.roll() for h in self._hs)

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: Optional[_CoalesceT] = None,
        max_depth: int = 1,
    ) -> H:
        """
        Shorthand for ``self.h().substitute(expand, coalesce, max_depth)``.
        """
        return self.h().substitute(expand, coalesce, max_depth)

    def within(self, lo: int, hi: int, other: OperandT = 0) -> "H":
        """
        Shorthand for ``self.h().within(lo, hi, other)``.
        """
        return self.h().within(lo, hi, other)


# ---- Functions -----------------------------------------------------------------------


def _coalesce_replace(h: H, face: int) -> H:  # pylint: disable=unused-argument
    return h


def _combinations_with_counts(
    h: Mapping[int, int],
    n: int,
) -> Iterator[Tuple[Tuple[int, ...], int]]:
    """
    Given a group of *n* identical histograms *h*, return an iterator that yields
    2-tuples (pairs). The first item is an *n*-tuple with the distinct combination. The
    second item is the count for that combination.

    >>> list(_combinations_with_counts(H((-1, 0, 1)), 2))
    [((-1, -1), 1), ((-1, 0), 2), ((-1, 1), 2), ((0, 0), 1), ((0, 1), 2), ((1, 1), 1)]

    This implementation is intended to be more efficient than merely enumerating and
    Cartesian product. Instead, it enumerates combinations with replacements, then
    computes the number of permutations with repetitions, leveraging:

    :math:`{{P}_{{{n}_{1}}!,{{n}_{2}}!,\\ldots,{{n}_{k}}!}^{n}} = {\\frac {{n}!} {{{n}_{1}}! {{n}_{2}}! \\cdots {{n}_{k}}!}}`
    """
    # combinations_with_replacement preserves input ordering and Hs are sorted
    for faces in itertools.combinations_with_replacement(h, n):
        total_count = functools.reduce(operator.mul, (h[face] for face in faces))
        num_permutations_numerator = math.factorial(len(faces))
        num_permutations_denominator = functools.reduce(
            operator.mul,
            (math.factorial(sum(1 for _ in g)) for _, g in itertools.groupby(faces)),
        )

        yield faces, total_count * num_permutations_numerator // num_permutations_denominator


def _getitems(sequence: Sequence[_T], keys: Iterable[_GetItemT]) -> Iterator[_T]:
    for key in keys:
        if isinstance(key, int):
            yield operator.getitem(sequence, key)
        else:
            for val in operator.getitem(sequence, key):
                yield val


def _within(lo: int, hi: int) -> _IntOperatorT:
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

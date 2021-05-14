# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
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
    Tuple,
    Union,
    cast,
)
from typing_extensions import Protocol, runtime_checkable

from collections import OrderedDict, defaultdict
from collections.abc import Mapping as ABCMapping
from functools import reduce
from itertools import (
    chain,
    product,
    repeat,
)
from math import gcd
from operator import (
    abs as op_abs,
    add as op_add,
    and_ as op_and,
    eq as op_eq,
    floordiv as op_floordiv,
    ge as op_ge,
    getitem as op_getitem,
    gt as op_gt,
    or_ as op_or,
    le as op_le,
    lt as op_lt,
    mod as op_mod,
    mul as op_mul,
    ne as op_ne,
    neg as op_neg,
    pos as op_pos,
    pow as op_pow,
    sub as op_sub,
    xor as op_xor,
)
from os import environ, get_terminal_size, linesep
from random import randrange

__all__ = "H"


# ---- Data ----------------------------------------------------------------------------


_UnaryOperatorT = Callable[[int], int]
_BinaryOperatorT = Callable[[int, int], int]
_ExpandT = Callable[["H", int], Union["H", int]]
_CoalesceT = Callable[["H", int], "H"]

try:
    _ROW_WIDTH = get_terminal_size().columns
except OSError:
    try:
        _ROW_WIDTH = int(environ["COLUMNS"])
    except (KeyError, ValueError):
        _ROW_WIDTH = 88


# ---- Classes -------------------------------------------------------------------------


class H(Mapping[int, int]):
    r"""
    An immutable mapping for use as a histogram that supports arithmetic operations.
    This is useful for modeling outcomes. The [initializer](#dyce.h.H.__init__) takes a
    single parameter, *items*. In its most explicit form, *items* maps faces to counts.

    Modeling a single six-sided die (``1d6``) can be expressed as:

    ```python
    >>> d6 = H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    ```

    An iterable of pairs can also be used (similar to ``dict``):

    ```python
    >>> d6 == H(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)))
    True

    ```

    Two shorthands are provided. If *items* an iterable of ``int``s, counts of one will
    be assumed:

    ```python
    >>> d6 == H((1, 2, 3, 4, 5, 6))
    True

    ```

    Repeated items do what one would expect:

    ```python
    >>> H((2, 3, 3, 4, 4, 5))
    H({2: 1, 3: 2, 4: 2, 5: 1})

    ```

    If *items* is an ``int``, it is shorthand for creating a sequential range
    $[{1} .. {items}]$ (or $[{items} .. {-1}]$ if *items* is negative):

    ```python
    >>> d6 == H(6)
    True

    ```

    Histograms are maps, so we can test equivalence against other maps:

    ```python
    >>> H(6) == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}
    True

    ```

    Simple indexes can be used to look up a face’s count:

    ```python
    >>> d6[5]
    1

    ```

    Most arithmetic operators are supported and do what one would expect. If the operand
    is an ``int``, the operator applies to the faces:

    ```python
    >>> d6 + 4
    H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})

    >>> d6 * -1
    H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})

    >>> d6 * -1 == -d6
    True

    >>> d6 * -1 == H(-6)
    True

    ```

    If the operand is another histogram, combinations are computed. Modeling the sum of
    two six-sided dice (``2d6``) can be expressed as:

    ```python
    >>> d6 + d6
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

    ```

    To sum ${n}$ identical histograms, the matrix multiplication operator (``@``)
    provides a shorthand:

    ```python
    >>> 3@d6 == d6 + d6 + d6
    True

    ```

    The ``len`` built-in function can be used to show the number of distinct sums:

    ```python
    >>> len(2@d6)
    11

    ```

    The [``counts`` method][dyce.h.H.counts] can be used to show the total number of
    combinations:

    ```python
    >>> sum((2@d6).counts())
    36

    ```

    Counts are generally accumulated without reduction:

    ```python
    >>> d6.concat(d6).concat(d6)
    H({1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3})

    ```

    To reduce, call the [``lowest_terms`` method][dyce.h.H.lowest_terms]:

    ```python
    >>> _.lowest_terms()
    H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    ```

    Testing equivalence implicitly performs reductions of operands:

    ```python
    >>> d6.concat(d6) == d6.concat(d6).concat(d6)
    True

    ```

    Histograms provide common comparators (e.g., [``eq``][dyce.h.H.eq]
    [``ne``][dyce.h.H.ne], etc.). One way to count how often a first six-sided die
    shows a different face than a second is:

    ```python
    >>> d6.ne(d6)
    H({0: 6, 1: 30})
    >>> print(_.format(width=65))
    avg |    0.83
      0 |  16.67% |########
      1 |  83.33% |#########################################

    ```

    Or, how often a first six-sided die shows a face less than a second is:

    ```python
    >>> d6.lt(d6)
    H({0: 21, 1: 15})
    >>> print(_.format(width=65))
    avg |    0.42
      0 |  58.33% |#############################
      1 |  41.67% |####################

    ```

    Or how often at least one ``2`` will show when rolling four six-sided dice:

    ```python
    >>> d6.eq(2)  # how often a 2 shows on a single six-sided die
    H({0: 5, 1: 1})
    >>> 4@(_)  # counts of how many 2s show on 4d6
    H({0: 625, 1: 500, 2: 150, 3: 20, 4: 1})
    >>> _.ge(1)  # how often the count is at least one
    H({0: 625, 1: 671})
    >>> print(_.format(width=65))
    avg |    0.52
      0 |  48.23% |########################
      1 |  51.77% |#########################

    ```

    !!! warning "Mind your parentheses"

        Parentheses are often necessary to enforce the desired order of operations:

        ```python
        >>> 2@d6.le(7)  # probably not what was intended
        H({2: 36})

        >>> 2@d6.le(7) == 2@(d6.le(7))
        True

        >>> (2@d6).le(7)
        H({0: 15, 1: 21})

        >>> 2@d6.le(7) == (2@d6).le(7)
        False

        ```
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

    # ---- Initializer -----------------------------------------------------------------

    def __init__(self, items: SourceT) -> None:
        r"Initializer."
        super().__init__()
        self._simple_init = None

        if isinstance(items, int):
            if items < 0:
                self._simple_init = items
                items = range(-1, items - 1, -1)
            elif items > 0:
                self._simple_init = items
                items = range(1, items + 1)
            else:
                items = {}
        elif isinstance(items, H.AbleT):
            items = items.h()

        if not isinstance(items, ABCMapping):
            h = defaultdict(int)  # type: DefaultDict[int, int]

            for item in items:
                if isinstance(item, tuple):
                    face, count = item
                    h[face] += count
                else:
                    h[item] += 1

            items = h

        self._h = OrderedDict((face, items[face]) for face in sorted(items))

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        if self._simple_init is not None:
            arg = str(self._simple_init)
        else:
            arg = dict.__repr__(self._h)

        return "{}({})".format(self.__class__.__name__, arg)

    def __eq__(self, other) -> bool:
        if isinstance(other, H.AbleT):
            return op_eq(self, other.h())
        elif isinstance(other, H):
            return op_eq(self.lowest_terms()._h, other.lowest_terms()._h)
        else:
            return super().__eq__(other)

    def __ne__(self, other) -> bool:
        if isinstance(other, H.AbleT):
            return op_ne(self, other.h())
        elif isinstance(other, H):
            return not op_eq(self, other)
        else:
            return super().__ne__(other)

    def __len__(self) -> int:
        return len(self._h)

    def __getitem__(self, key: int) -> int:
        return op_getitem(self._h, key)

    def __iter__(self) -> Iterator[int]:
        return iter(self._h)

    def __add__(self, other: OperandT) -> "H":
        try:
            return self.map(op_add, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_add, other)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: OperandT) -> "H":
        try:
            return self.map(op_sub, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_sub, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: OperandT) -> "H":
        try:
            return self.map(op_mul, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_mul, other)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: int) -> "H":
        if not isinstance(other, int):
            return NotImplemented
        elif other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return cast(H, sum(repeat(self, other)))

    def __rmatmul__(self, other: int) -> "H":
        return self.__matmul__(other)

    def __floordiv__(self, other: OperandT) -> "H":
        try:
            return self.map(op_floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: OperandT) -> "H":
        try:
            return self.map(op_mod, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_mod, other)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: OperandT) -> "H":
        try:
            return self.map(op_pow, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_pow, other)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: OperandT) -> "H":
        try:
            return self.map(op_and, other)
        except NotImplementedError:
            return NotImplemented

    def __rand__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_and, other)
        except NotImplementedError:
            return NotImplemented

    def __xor__(self, other: OperandT) -> "H":
        try:
            return self.map(op_xor, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_xor, other)
        except NotImplementedError:
            return NotImplemented

    def __or__(self, other: OperandT) -> "H":
        try:
            return self.map(op_or, other)
        except NotImplementedError:
            return NotImplemented

    def __ror__(self, other: OperandT) -> "H":
        try:
            return self.rmap(op_or, other)
        except NotImplementedError:
            return NotImplemented

    def __neg__(self) -> "H":
        return self.umap(op_neg)

    def __pos__(self) -> "H":
        return self.umap(op_pos)

    def __abs__(self) -> "H":
        return self.umap(op_abs)

    def items(self):
        return self._h.items()

    def keys(self):
        return self._h.keys()

    def values(self):
        return self._h.values()

    # ---- Methods ---------------------------------------------------------------------

    def map(self, oper: _BinaryOperatorT, other: OperandT) -> "H":
        r"""
        Applies *oper* to each face of the histogram paired with *other*:

        ```python
        >>> import operator
        >>> d6 = H(6)
        >>> d6.map(operator.add, d6)
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        >>> d6.map(operator.mul, -1)
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})

        >>> d6.map(operator.gt, 3)
        H({0: 3, 1: 3})

        ```

        Note that shorthands exist for many arithmetic operators and comparators:

        ```python
        >>> d6 + d6 == d6.map(operator.add, d6)
        True

        >>> d6 * -1 == d6.map(operator.mul, -1)
        True

        >>> d6.gt(3) == d6.map(operator.gt, 3)
        True

        ```
        """
        if isinstance(other, H.AbleT):
            other = other.h()

        if isinstance(other, int):
            return H((int(oper(face, other)), count) for face, count in self.items())
        elif isinstance(other, H):
            return H(
                (int(oper(a, b)), self[a] * other[b]) for a, b in product(self, other)
            )
        else:
            raise NotImplementedError

    def rmap(self, oper: _BinaryOperatorT, other: OperandT) -> "H":
        if isinstance(other, H.AbleT):
            other = other.h()

        if isinstance(other, int):
            return H((int(oper(other, face)), count) for face, count in self.items())
        elif isinstance(other, H):
            return H(
                (int(oper(b, a)), other[b] * self[a]) for b, a in product(other, self)
            )
        else:
            raise NotImplementedError

    def umap(self, oper: _UnaryOperatorT) -> "H":
        h = H((oper(face), count) for face, count in self.items())

        if self._simple_init is not None:
            h_simple = H(oper(self._simple_init))

            if h_simple == h:
                return h_simple

        return h

    def lt(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.lt, other)``:

        ```python
        >>> H(6).lt(3)
        H({0: 4, 1: 2})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_lt, other)

    def le(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.le, other)``.

        ```python
        >>> H(6).le(3)
        H({0: 3, 1: 3})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_le, other)

    def eq(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.eq, other)``.

        ```python
        >>> H(6).eq(3)
        H({0: 5, 1: 1})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_eq, other)

    def ne(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.ne, other)``.

        ```python
        >>> H(6).ne(3)
        H({0: 1, 1: 5})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_ne, other)

    def gt(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.gt, other)``.

        ```python
        >>> H(6).gt(3)
        H({0: 3, 1: 3})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_gt, other)

    def ge(
        self,
        other: OperandT,
    ) -> "H":
        r"""
        Shorthand for ``self.map(operator.ge, other)``.

        ```python
        >>> H(6).ge(3)
        H({0: 2, 1: 4})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_ge, other)

    def even(self) -> "H":
        r"""
        ```python
        >>> H((-4, -2, 0, 1, 2, 3)).even()
        H({0: 2, 1: 4})

        ```
        """

        def is_even(a: int) -> int:
            return (a & 0b1) ^ 0b1

        return self.umap(is_even)

    def odd(self) -> "H":
        r"""
        ```python
        >>> H((-4, -2, 0, 1, 2, 3)).odd()
        H({0: 4, 1: 2})

        ```
        """

        def is_odd(a: int) -> int:
            return a & 0b1

        return self.umap(is_odd)

    def avg(self) -> float:
        numerator = denominator = 0

        for face, count in self.items():
            numerator += face * count
            denominator += count

        return numerator / (denominator or 1)

    def concat(self, other: SourceT) -> "H":
        r"""
        Accumulates counts:

        ```python
        >>> H(4).concat(H(6))
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})

        ```
        """
        if isinstance(other, int):
            other = (other,)
        elif isinstance(other, ABCMapping):
            other = other.items()

        return H(chain(self.items(), cast(Iterable, other)))

    def counts(self) -> Iterator[int]:
        r"""
        More descriptive synonym for the [``values`` method][dyce.h.H.values].
        """
        return self.values()

    def data(
        self,
        relative: bool = False,
        fill_items: Optional[Mapping[int, int]] = None,
    ) -> Iterator[Tuple[int, float]]:
        r"""
        Presentation helper function that returns an iterator for each face/frequency pair:

        ```python
        >>> d6 = H(6)
        >>> list(d6.gt(3).data())
        [(0, 3.0), (1, 3.0)]

        >>> list(d6.gt(3).data(relative=True))
        [(0, 0.5), (1, 0.5)]

        ```

        If provided, *fill_items* supplies defaults for any missing faces:

        ```python
        >>> list(d6.gt(7).data())
        [(0, 6.0)]

        >>> list(d6.gt(7).data(fill_items={1: 0, 0: 0}))
        [(0, 6.0), (1, 0.0)]

        ```
        """
        if fill_items is None:
            fill_items = {}

        if relative:
            total = sum(self.counts()) or 1
        else:
            total = 1

        combined = dict(chain(fill_items.items(), self.items()))

        return ((face, count / total) for face, count in sorted(combined.items()))

    def data_xy(
        self,
        relative: bool = False,
        fill_items: Optional[Mapping[int, int]] = None,
    ) -> Tuple[Tuple[int, ...], Tuple[float, ...]]:
        r"""
        Presentation helper function that returns an iterator for a “zipped” arrangement of
        the output from the [``data`` method][dyce.h.H.data]:

        ```python
        >>> d6 = H(6)
        >>> list(d6.data())
        [(1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0)]
        >>> d6.data_xy()
        ((1, 2, 3, 4, 5, 6), (1.0, 1.0, 1.0, 1.0, 1.0, 1.0))

        ```
        """
        return cast(
            Tuple[Tuple[int, ...], Tuple[float, ...]],
            tuple(zip(*self.data(relative, fill_items))),
        )

    def explode(
        self,
        max_depth: int = 1,
    ) -> "H":
        r"""
        Shorthand for ``self.substitute(lambda h, f: h if f == max(h) else f, operator.add,
        max_depth)``.

        ```python
        >>> H(6).explode(max_depth=2)
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})

        ```

        See the [``substitute`` method][dyce.h.H.substitute].
        """

        def _reroll_greatest(h: H, face: int) -> Union[H, int]:
            return h if face == max(h) else face

        return self.substitute(_reroll_greatest, op_add, max_depth)

    def faces(self) -> Iterator[int]:
        r"""
        More descriptive synonym for the [``keys`` method][dyce.h.H.keys].
        """
        return self.keys()

    def format(
        self,
        fill_items: Optional[Mapping[int, int]] = None,
        width: int = _ROW_WIDTH,
        tick: str = "#",
        scaled: bool = False,
        sep: str = linesep,
    ) -> str:
        r"""
        Returns a formatted string representation of the histogram. If provided,
        *fill_items* supplies defaults for any missing faces. If *width* is greater than
        zero, a horizontal bar ASCII graph is printed using *tick* and *sep* (which are
        otherwise ignored if *width* is zero or less).

        ```python
        >>> print(H(6).format(width=0))
        {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}

        >>> print((2@H(6)).format(fill_items={i: 0 for i in range(1, 21)}, width=65, tick="@"))
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

        ```

        If *scaled* is ``True``, horizontal bars are scaled to *width*:

        ```python
        >>> h = (2@H(6)).ge(7)
        >>> print("{:->65}".format(" 65 chars wide -->|"))
        ---------------------------------------------- 65 chars wide -->|
        >>> print(h.format(width=65, scaled=False))
        avg |    0.58
          0 |  41.67% |####################
          1 |  58.33% |#############################
        >>> print(h.format(width=65, scaled=True))
        avg |    0.58
          0 |  41.67% |###################################
          1 |  58.33% |##################################################

        ```
        """
        if width <= 0:

            def parts():
                yield "avg: {:.2f}".format(self.avg())

                for face, percentage in self.data(relative=True, fill_items=fill_items):
                    yield "{}:{:7.2%}".format(face, percentage)

            return "{" + ", ".join(parts()) + "}"
        else:
            w = width - 15

            def lines():
                yield "avg | {:7.2f}".format(self.avg())
                total = sum(self.counts())
                tick_scale = max(self.counts()) if scaled else total

                for face, count in self.data(relative=False, fill_items=fill_items):
                    percentage = count / total
                    ticks = int(w * count / tick_scale)
                    yield "{: 3} | {:7.2%} |{}".format(face, percentage, tick * ticks)

            return sep.join(lines())

    def lowest_terms(self) -> "H":
        r"""
        Computes and returns a histogram whose counts share a greatest common divisor of 1.

        ```python
        >>> H((-1, -1, 0, 0, 1, 1))
        H({-1: 2, 0: 2, 1: 2})
        >>> _.lowest_terms()
        H({-1: 1, 0: 1, 1: 1})

        >>> H((2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5))
        H({2: 2, 3: 4, 4: 4, 5: 2})
        >>> _.lowest_terms()
        H({2: 1, 3: 2, 4: 2, 5: 1})

        ```
        """
        counts_gcd = reduce(gcd, self.counts(), 0)

        return H({k: v // counts_gcd for k, v in self.items()})

    def roll(self) -> int:
        r"""
        Returns a (weighted) random face.
        """
        val = randrange(0, sum(self.counts()))
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
        r"""
        Calls *expand* on each face, recursively up to *max_depth* times. If *expand*
        returns an ``int``, it replaces the face. [``H`` object][dyce.h.H], *coalesce*
        is called on the face and the expanded histogram, and the returned histogram is
        folded into result. The default behavior for *coalesce* is to replace the face
        with the expanded histogram.

        This can be used to model complex rules. The following models re-rolling a face
        of 1 on the first roll:

        ```python
        >>> def reroll_one(h: H, face: int) -> Union[H, int]:
        ...   return h if face == 1 else face
        >>> H(6).substitute(reroll_one)
        H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

        ```

        See the [``explode`` method][dyce.h.H.explode] for a common shorthand for
        exploding dice.

        For a more complicated example, consider the following rules:

          1. Start with a total of zero.
          2. Roll a six-sided die. Add the face to the total. If the face was a six, go
             to step 3. Otherwise stop.
          3. Roll a four-sided die. Add the face to the total. If the face was a four,
             go to step 2. Otherwise stop.

        What is the likelihood of an even final tally? This can be approximated by:

        ```python
        >>> d4, d6 = H(4), H(6)
        >>> def reroll_greatest_on_d4_d6(h: H, face: int) -> Union[H, int]:
        ...   if face == max(h):
        ...     if h == d6: return d4
        ...     if h == d4: return d6
        ...   return face
        >>> import operator
        >>> h = d6.substitute(reroll_greatest_on_d4_d6, operator.add, max_depth=6)
        >>> h_even = h.even()
        >>> print("{:.3%}".format(h_even.get(1, 0) / sum(h_even.counts())))
        39.131%

        ```

        Because ``substitute`` accepts arbitrary functions, it is well suited for
        modeling complicated logical progressions:

        ```python
        >>> bonus = 1
        >>> dmg_dice = H(8)
        >>> dmg = dmg_dice + bonus
        >>> crit = dmg + dmg_dice
        >>> target = 15 - bonus
        >>> d20 = H(20)
        >>> def dmg_from_attack_roll(h: H, face: int) -> Union[H, int]:
        ...   if face == 20:
        ...     return crit
        ...   elif face >= target:
        ...     return dmg
        ...   else:
        ...     return 0
        >>> h = d20.substitute(dmg_from_attack_roll)
        >>> print(h.format(width=0))
        {avg: 2.15, 0: 65.00%, 2:  3.75%, 3:  3.83%, 4:  3.91%, ..., 15:  0.23%, 16:  0.16%, 17:  0.08%}

        ```
        """
        if coalesce is None:
            coalesce = _coalesce_replace

        def _substitute(
            h: H,
            depth: int = 0,
        ) -> H:
            assert coalesce is not None

            if depth == max_depth:
                return h

            total_scalar = 1
            items_for_reassembly: List[Tuple[int, int, int]] = []

            for face, count in h.items():
                expanded = expand(h, face)

                if isinstance(expanded, int):
                    items_for_reassembly.append((expanded, count, 1))
                else:
                    # Keep expanding deeper, if we can
                    expanded = _substitute(expanded, depth + 1)
                    # Coalesce the result
                    expanded = coalesce(expanded, face)
                    # Account for the impact of expansion on peers
                    expanded_scalar = sum(expanded.counts())
                    total_scalar *= expanded_scalar
                    # Account for the impact of the original count on the result, but
                    # keep track of the impact on peers so we can factor it out for
                    # these items later
                    items_for_reassembly.extend(
                        (f, c * count, expanded_scalar) for f, c in expanded.items()
                    )

            return H(
                (
                    # Apply the total_scalar, but factor out this item's contribution
                    (f, c * total_scalar // s)
                    for f, c, s in items_for_reassembly
                )
            ).lowest_terms()

        return _substitute(self)

    def within(self, lo: int, hi: int, other: OperandT = 0) -> "H":
        r"""
        Computes the difference between this histogram and *other*. -1 is represents where
        that difference is less than *lo*. 0 represents where that difference between
        *lo* and *hi* (inclusive). 1 represents where that difference is greater than
        *hi*.

        ```python
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

        ```
        """
        return self.map(_within(lo, hi), other)


# ---- Functions -----------------------------------------------------------------------


def _coalesce_replace(h: H, face: int) -> H:  # pylint: disable=unused-argument
    return h


def _within(lo: int, hi: int) -> _BinaryOperatorT:
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

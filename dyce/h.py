# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import os
from collections import Counter as counter
from collections.abc import Iterable as IterableC
from collections.abc import Mapping as MappingC
from fractions import Fraction
from itertools import chain, product, repeat
from math import sqrt
from operator import (
    __abs__,
    __add__,
    __and__,
    __eq__,
    __floordiv__,
    __ge__,
    __getitem__,
    __gt__,
    __invert__,
    __le__,
    __lt__,
    __mod__,
    __mul__,
    __ne__,
    __neg__,
    __or__,
    __pos__,
    __pow__,
    __sub__,
    __truediv__,
    __xor__,
)
from random import choices
from typing import (
    Callable,
    Counter,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    ValuesView,
    cast,
    overload,
)

from .lifecycle import deprecated, experimental
from .symmetries import comb, gcd, sum_w_start
from .types import (
    CachingProtocolMeta,
    IntT,
    OutcomeT,
    Protocol,
    _IntCs,
    _OutcomeCs,
    _RationalConstructorT,
    as_int,
    runtime_checkable,
    sorted_outcomes,
)

__all__ = ("H",)


# ---- Types ---------------------------------------------------------------------------


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_MappingT = Mapping[OutcomeT, int]
_SourceT = Union[
    IntT,
    Iterable[OutcomeT],
    Iterable[Tuple[OutcomeT, IntT]],
    _MappingT,
    "HAbleT",
]
_OperandT = Union[OutcomeT, "H", "HAbleT"]
_UnaryOperatorT = Callable[[_T_co], _T_co]
_BinaryOperatorT = Callable[[_T_co, _T_co], _T_co]
_ExpandT = Callable[["H", OutcomeT], Union[OutcomeT, "H"]]
_CoalesceT = Callable[["H", OutcomeT], "H"]


# ---- Data ----------------------------------------------------------------------------


try:
    _ROW_WIDTH = os.get_terminal_size().columns
except OSError:
    try:
        _ROW_WIDTH = int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        _ROW_WIDTH = 88


# ---- Functions -----------------------------------------------------------------------


def coalesce_replace(h: H, outcome: OutcomeT) -> H:
    r"""
    Default behavior for [``H.substitute``][dyce.h.H.substitute]. Returns *h* unmodified
    (*outcome* is ignored).
    """
    return h


# ---- Classes -------------------------------------------------------------------------


class H(_MappingT):
    r"""
    An immutable mapping for use as a histogram which supports arithmetic operations.
    This is useful for modeling discrete outcomes, like individual dice. ``#!python H``
    objects encode discrete probability distributions as integer counts without any
    denominator.

    !!! info

        The lack of an explicit denominator is intentional and has two benefits. First,
        a denominator is redundant. Without it, one never has to worry about
        probabilities summing to one (e.g., via miscalculation, floating point error,
        etc.). Second (and perhaps more importantly), sometimes one wants to have an
        insight into non-reduced counts, not just probabilities. If needed,
        probabilities can always be derived, as shown below.

    The [initializer][dyce.h.H.__init__] takes a single parameter, *items*. In its most
    explicit form, *items* maps outcome values to counts.

    Modeling a single six-sided die (``1d6``) can be expressed as:

    ``` python
    >>> from dyce import H
    >>> d6 = H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    ```

    An iterable of pairs can also be used (similar to ``#!python dict``).

    ``` python
    >>> d6 == H(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)))
    True

    ```

    Two shorthands are provided. If *items* is an iterable of numbers, counts of 1 are
    assumed.

    ``` python
    >>> d6 == H((1, 2, 3, 4, 5, 6))
    True

    ```

    Repeated items are accumulated, as one would expect.

    ``` python
    >>> H((2, 3, 3, 4, 4, 5))
    H({2: 1, 3: 2, 4: 2, 5: 1})

    ```

    If *items* is an integer, it is shorthand for creating a sequential range $[{1} ..
    {items}]$ (or $[{items} .. {-1}]$ if *items* is negative).

    ``` python
    >>> d6 == H(6)
    True

    ```

    Histograms are maps, so we can test equivalence against other maps.

    ``` python
    >>> H(6) == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}
    True

    ```

    Simple indexes can be used to look up an outcome’s count.

    ``` python
    >>> H((2, 3, 3, 4, 4, 5))[3]
    2

    ```

    Most arithmetic operators are supported and do what one would expect. If the operand
    is a number, the operator applies to the outcomes.

    ``` python
    >>> d6 + 4
    H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})

    ```

    ``` python
    >>> d6 * -1
    H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})
    >>> d6 * -1 == -d6
    True
    >>> d6 * -1 == H(-6)
    True

    ```

    If the operand is another histogram, combinations are computed. Modeling the sum of
    two six-sided dice (``2d6``) can be expressed as:

    ``` python
    >>> d6 + d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
    >>> print((d6 + d6).format(width=65))
    avg |    7.00
    std |    2.42
    var |    5.83
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
    provides a shorthand.

    ``` python
    >>> 3@d6 == d6 + d6 + d6
    True

    ```

    The ``#!python len`` built-in function can be used to show the number of distinct
    outcomes.

    ``` python
    >>> len(2@d6)
    11

    ```

    The [``total`` property][dyce.h.H.total] can be used to compute the total number of
    combinations and each outcome’s probability.

    ``` python
    >>> from fractions import Fraction
    >>> (2@d6).total
    36
    >>> [(outcome, Fraction(count, (2@d6).total)) for outcome, count in (2@d6).items()]
    [(2, Fraction(1, 36)), (3, Fraction(1, 18)), (4, Fraction(1, 12)), (5, Fraction(1, 9)), (6, Fraction(5, 36)), (7, Fraction(1, 6)), ..., (12, Fraction(1, 36))]

    ```

    Histograms provide common comparators (e.g., [``eq``][dyce.h.H.eq]
    [``ne``][dyce.h.H.ne], etc.). One way to count how often a first six-sided die
    shows a different face than a second is:

    ``` python
    >>> d6.ne(d6)
    H({False: 6, True: 30})
    >>> print(d6.ne(d6).format(width=65))
    avg |    0.83
    std |    0.37
    var |    0.14
      0 |  16.67% |########
      1 |  83.33% |#########################################

    ```

    Or, how often a first six-sided die shows a face less than a second is:

    ``` python
    >>> d6.lt(d6)
    H({False: 21, True: 15})
    >>> print(d6.lt(d6).format(width=65))
    avg |    0.42
    std |    0.49
    var |    0.24
      0 |  58.33% |#############################
      1 |  41.67% |####################

    ```

    Or how often at least one ``#!python 2`` will show when rolling four six-sided dice:

    ``` python
    >>> d6_eq2 = d6.eq(2) ; d6_eq2  # how often a 2 shows on a single six-sided die
    H({False: 5, True: 1})
    >>> 4@d6_eq2  # count of 2s showing on 4d6
    H({0: 625, 1: 500, 2: 150, 3: 20, 4: 1})
    >>> (4@d6_eq2).ge(1)  # how often that count is at least one
    H({False: 625, True: 671})
    >>> print((4@d6_eq2).ge(1).format(width=65))
    avg |    0.52
    std |    0.50
    var |    0.25
      0 |  48.23% |########################
      1 |  51.77% |#########################

    ```

    !!! tip "Mind your parentheses"

        Parentheses are often necessary to enforce the desired order of operations. This
        is most often an issue with the ``#!python @`` operator, because it behaves
        differently than the ``d`` operator in most dedicated grammars. More
        specifically, in Python, ``#!python @`` has a [lower
        precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence)
        than ``#!python .`` and ``#!python […]``.

        ``` python
        >>> 2@d6[7]  # type: ignore
        Traceback (most recent call last):
          ...
        KeyError: 7
        >>> 2@d6.le(7)  # probably not what was intended
        H({2: 36})
        >>> 2@d6.le(7) == 2@(d6.le(7))
        True

        ```

        ``` python
        >>> (2@d6)[7]
        6
        >>> (2@d6).le(7)
        H({False: 15, True: 21})
        >>> 2@d6.le(7) == (2@d6).le(7)
        False

        ```

    Counts are generally accumulated without reduction. To reduce, call the
    [``lowest_terms`` method][dyce.h.H.lowest_terms].

    ``` python
    >>> d6.ge(4)
    H({False: 3, True: 3})
    >>> d6.ge(4).lowest_terms()
    H({False: 1, True: 1})

    ```

    Testing equivalence implicitly performs reductions of operands.

    ``` python
    >>> d6.ge(4) == d6.ge(4).lowest_terms()
    True

    ```
    """

    # ---- Initializer -----------------------------------------------------------------

    def __init__(self, items: _SourceT) -> None:
        r"Initializer."
        super().__init__()
        self._simple_init: Optional[int] = None
        tmp: Counter[OutcomeT] = counter()

        if isinstance(items, MappingC):
            items = items.items()

        if isinstance(items, _IntCs):
            if items != 0:
                self._simple_init = as_int(items)
                outcome_range = range(
                    self._simple_init,
                    0,
                    1 if self._simple_init < 0 else -1,  # count toward zero
                )

                if isinstance(items, _OutcomeCs):
                    outcome_type = type(items)
                    tmp.update({outcome_type(i): 1 for i in outcome_range})
                else:
                    tmp.update({i: 1 for i in outcome_range})
        elif isinstance(items, HAbleT):
            tmp.update(items.h())
        elif isinstance(items, IterableC):
            # Items is either an Iterable[OutcomeT] or an Iterable[Tuple[OutcomeT,
            # IntT]] (although this technically supports Iterable[Union[OutcomeT,
            # Tuple[OutcomeT, IntT]]])
            for item in items:
                if isinstance(item, tuple):
                    outcome, count = item
                    tmp[outcome] += as_int(count)
                else:
                    tmp[item] += 1
        else:
            raise ValueError(f"unrecognized initializer {items}")

        # Sort and omit zero counts. As of Python 3.7, insertion order of keys is
        # preserved.
        self._h: _MappingT = {
            outcome: tmp[outcome]
            for outcome in sorted_outcomes(tmp)
            if tmp[outcome] != 0
        }

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        if self._simple_init is not None:
            arg = str(self._simple_init)
        else:
            arg = dict.__repr__(self._h)

        return f"{self.__class__.__name__}({arg})"

    def __eq__(self, other) -> bool:
        if isinstance(other, HAbleT):
            return __eq__(self, other.h())
        elif isinstance(other, H):
            return __eq__(self.lowest_terms()._h, other.lowest_terms()._h)
        else:
            return super().__eq__(other)

    def __ne__(self, other) -> bool:
        if isinstance(other, HAbleT):
            return __ne__(self, other.h())
        elif isinstance(other, H):
            return not __eq__(self, other)
        else:
            return super().__ne__(other)

    def __hash__(self) -> int:
        return hash(frozenset(self._lowest_terms()))

    def __len__(self) -> int:
        return len(self._h)

    def __getitem__(self, key: OutcomeT) -> int:
        return __getitem__(self._h, key)

    def __iter__(self) -> Iterator[OutcomeT]:
        return iter(self._h)

    def __add__(self, other: _OperandT) -> H:
        try:
            if self and not other:
                return self.map(__add__, 0)
            elif not self and isinstance(other, (H, HAbleT)):
                return __add__(0, other.h() if isinstance(other, HAbleT) else other)
            else:
                return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: _OperandT) -> H:
        try:
            if self and not other:
                return self.map(__sub__, 0)
            elif not self and isinstance(other, (H, HAbleT)):
                return __sub__(0, other.h() if isinstance(other, HAbleT) else other)
            else:
                return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: _OperandT) -> H:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: IntT) -> H:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return sum_w_start(repeat(self, other), start=H({}))

    def __rmatmul__(self, other: IntT) -> H:
        return self.__matmul__(other)

    def __truediv__(self, other: _OperandT) -> H:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    def __rtruediv__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    def __floordiv__(self, other: _OperandT) -> H:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: _OperandT) -> H:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: _OperandT) -> H:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OutcomeT) -> H:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: Union[IntT, H, HAbleT]) -> H:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__and__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __rand__(self, other: IntT) -> H:
        try:
            return self.rmap(as_int(other), __and__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __xor__(self, other: Union[IntT, H, HAbleT]) -> H:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__xor__, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: IntT) -> H:
        try:
            return self.rmap(as_int(other), __xor__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __or__(self, other: Union[IntT, H, HAbleT]) -> H:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__or__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __ror__(self, other: IntT) -> H:
        try:
            return self.rmap(as_int(other), __or__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __neg__(self) -> H:
        return self.umap(__neg__)

    def __pos__(self) -> H:
        return self.umap(__pos__)

    def __abs__(self) -> H:
        return self.umap(__abs__)

    def __invert__(self) -> H:
        return self.umap(__invert__)

    def counts(self) -> ValuesView[int]:
        r"""
        More descriptive synonym for the [``values`` method][dyce.h.H.values].
        """
        return self._h.values()

    def items(self) -> ItemsView[OutcomeT, int]:
        # TODO(posita): See <https://github.com/python/typeshed/issues/5808>
        return self._h.items()  # type: ignore

    def keys(self) -> KeysView[OutcomeT]:
        return self.outcomes()

    def outcomes(self) -> KeysView[OutcomeT]:
        r"""
        More descriptive synonym for the [``keys`` method][dyce.h.H.keys].
        """
        # TODO(posita): See <https://github.com/python/typeshed/issues/5808>
        return self._h.keys()  # type: ignore

    def values(self) -> ValuesView[int]:
        return self.counts()

    # ---- Properties ------------------------------------------------------------------

    @property
    def total(self) -> int:
        r"""
        !!! warning "Experimental"

            This propertyshould be considered experimental and may change or disappear
            in future versions.

        Equivalent to ``#!python sum(self.counts())``.
        """

        @experimental
        def _total() -> int:
            return sum(self.counts())

        return _total()

    # ---- Methods ---------------------------------------------------------------------

    def map(
        self,
        op: _BinaryOperatorT,
        right_operand: _OperandT,
    ) -> H:
        r"""
        Applies *op* to each outcome of the histogram as the left operand and
        *right_operand* as the right. Shorthands exist for many arithmetic operators and
        comparators.

        ``` python
        >>> import operator
        >>> d6 = H(6)
        >>> d6.map(operator.__add__, d6)
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
        >>> d6.map(operator.__add__, d6) == d6 + d6
        True

        ```

        ``` python
        >>> d6.map(operator.__pow__, 2)
        H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1})
        >>> d6.map(operator.__pow__, 2) == d6 ** 2
        True

        ```

        ``` python
        >>> d6.map(operator.__gt__, 3)
        H({False: 3, True: 3})
        >>> d6.map(operator.__gt__, 3) == d6.gt(3)
        True

        ```
        """
        if isinstance(right_operand, HAbleT):
            right_operand = right_operand.h()

        if isinstance(right_operand, H):
            return H(
                (op(s, o), self[s] * right_operand[o])
                for s, o in product(self, right_operand)
            )
        else:
            return H(
                (op(outcome, right_operand), count) for outcome, count in self.items()
            )

    def rmap(
        self,
        left_operand: OutcomeT,
        op: _BinaryOperatorT,
    ) -> H:
        r"""
        Analogous to the [``map`` method][dyce.h.H.map], but where the caller supplies
        *left_operand*.

        ``` python
        >>> import operator
        >>> d6 = H(6)
        >>> d6.rmap(2, operator.__pow__)
        H({2: 1, 4: 1, 8: 1, 16: 1, 32: 1, 64: 1})
        >>> d6.rmap(2, operator.__pow__) == 2 ** d6
        True

        ```

        Note that the positions of *left_operand* and *op* are different from
        [``map`` method][dyce.h.H.map]. This is intentional and serves as a reminder
        of operand ordering.

        !!! warning "Deprecated"

            This method originally accepted the *op* parameter in the first position,
            and the *left_operand* parameter in the second. While that is still silently
            supported, that ordering is deprecated and will likely be removed in the
            next major release.
        """
        if isinstance(op, _OutcomeCs):
            # Warning! It's opposite day! Things are all mixed up! op is the operand and
            # left_operand is the operator!
            return self._deprecated_rmap_signature(left_operand, op)

        return H((op(left_operand, outcome), count) for outcome, count in self.items())

    @deprecated
    def _deprecated_rmap_signature(
        self,
        op: _BinaryOperatorT,
        other: OutcomeT,
    ) -> H:
        r"""
        ``` python
        >>> import operator
        >>> H(6).rmap(operator.__pow__, 2)  # type: ignore
        H({2: 1, 4: 1, 8: 1, 16: 1, 32: 1, 64: 1})

        ```
        """
        return self.rmap(other, op)

    def umap(
        self,
        op: _UnaryOperatorT,
    ) -> H:
        r"""
        Applies *op* to each outcome of the histogram.

        ``` python
        >>> import operator
        >>> H(6).umap(operator.__neg__)
        H(-6)

        ```

        ``` python
        >>> H(4).umap(lambda outcome: (-outcome) ** outcome)
        H({-27: 1, -1: 1, 4: 1, 256: 1})

        ```
        """
        h = H((op(outcome), count) for outcome, count in self.items())

        if self._simple_init is not None:
            simple_init = op(self._simple_init)

            if isinstance(simple_init, _IntCs):
                h_simple = H(simple_init)

                if h_simple == h:
                    return h_simple

        return h

    def lt(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__lt__, other).umap(bool)``.

        ``` python
        >>> H(6).lt(3)
        H({False: 4, True: 2})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__lt__, other).umap(bool)

    def le(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__le__, other).umap(bool)``.

        ``` python
        >>> H(6).le(3)
        H({False: 3, True: 3})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__le__, other).umap(bool)

    def eq(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__eq__, other).umap(bool)``.

        ``` python
        >>> H(6).eq(3)
        H({False: 5, True: 1})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__eq__, other).umap(bool)

    def ne(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__ne__, other).umap(bool)``.

        ``` python
        >>> H(6).ne(3)
        H({False: 1, True: 5})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__ne__, other).umap(bool)

    def gt(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__gt__, other).umap(bool)``.

        ``` python
        >>> H(6).gt(3)
        H({False: 3, True: 3})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__gt__, other).umap(bool)

    def ge(
        self,
        other: _OperandT,
    ) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__ge__, other).umap(bool)``.

        ``` python
        >>> H(6).ge(3)
        H({False: 2, True: 4})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__ge__, other).umap(bool)

    def is_even(self) -> H:
        r"""
        Equivalent to ``#!python self.umap(lambda outcome: outcome % 2 == 0)``.

        ``` python
        >>> H((-4, -2, 0, 1, 2, 3)).is_even()
        H({False: 2, True: 4})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """

        def _is_even(outcome: IntT) -> bool:
            return as_int(outcome) % 2 == 0

        return self.umap(_is_even)

    @deprecated
    def even(self) -> H:
        r"""
        !!! warning "Deprecated"

            This method is deprecated and will likely be removed in the next major
            release.

        Alias for the [``is_even`` method][dyce.h.H.is_even].
        """
        return self.is_even()

    def is_odd(self) -> H:
        r"""
        Equivalent to ``#!python self.umap(lambda outcome: outcome % 2 != 0)``.

        ``` python
        >>> H((-4, -2, 0, 1, 2, 3)).is_odd()
        H({False: 4, True: 2})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """

        def _is_odd(outcome: IntT) -> bool:
            return as_int(outcome) % 2 != 0

        return self.umap(_is_odd)

    @deprecated
    def odd(self) -> H:
        r"""
        !!! warning "Deprecated"

            This method is deprecated and will likely be removed in the next major
            release.

        Alias for the [``is_odd`` method][dyce.h.H.is_odd].
        """
        return self.is_odd()

    def accumulate(self, other: _SourceT) -> H:
        r"""
        Accumulates counts.

        ``` python
        >>> H(4).accumulate(H(6))
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})

        ```
        """
        if isinstance(other, MappingC):
            other = other.items()
        elif not isinstance(other, IterableC):
            other = cast(Iterable[OutcomeT], (other,))

        return H(chain(self.items(), cast(Iterable, other)))

    @experimental
    def exactly_k_times_in_n(
        self,
        outcome: OutcomeT,
        n: IntT,
        k: IntT,
    ) -> int:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Computes and returns the probability distribution where *outcome* appears
        exactly *k* times among ``#!python n@self``.

        ``` python
        >>> H(6).exactly_k_times_in_n(outcome=5, n=4, k=2)
        150
        >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=2, n=3, k=3)
        1
        >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=4, n=3, k=3)
        8

        ```
        """
        n = as_int(n)
        k = as_int(k)
        assert k <= n
        c_outcome = self.get(outcome, 0)

        return comb(n, k) * c_outcome ** k * (self.total - c_outcome) ** (n - k)

    def explode(self, max_depth: IntT = 1) -> H:
        r"""
        Shorthand for ``#!python self.substitute(lambda h, outcome: h if outcome == max(h)
        else outcome, operator.__add__, max_depth)``.

        ``` python
        >>> H(6).explode(max_depth=2)
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})

        ```

        See the [``substitute`` method][dyce.h.H.substitute].
        """
        return self.substitute(
            lambda h, outcome: h if outcome == max(h) else outcome,
            __add__,
            max_depth,
        )

    def lowest_terms(self) -> H:
        r"""
        Computes and returns a histogram whose counts share a greatest common divisor of 1.

        ``` python
        >>> df = H((-1, -1, 0, 0, 1, 1)) ; df
        H({-1: 2, 0: 2, 1: 2})
        >>> df.lowest_terms()
        H({-1: 1, 0: 1, 1: 1})

        ```

        ``` python
        >>> d6avg = H((2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5)) ; d6avg
        H({2: 2, 3: 4, 4: 4, 5: 2})
        >>> d6avg.lowest_terms()
        H({2: 1, 3: 2, 4: 2, 5: 1})

        ```
        """
        return H(self._lowest_terms())

    @experimental
    def order_stat_for_n_at_pos(self, n: IntT, pos: IntT) -> H:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Shorthand for ``#!python self.order_stat_func_for_n(n)(pos)``.
        """
        return self.order_stat_func_for_n(n)(pos)

    @experimental
    def order_stat_func_for_n(self, n: IntT) -> Callable[[IntT], H]:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Returns a function that takes a single argument (*pos*) and computes the
        probability distribution for each outcome appearing in that position among
        ``#!python n@self``.

        ``` python
        >>> d6avg = H((2, 3, 3, 4, 4, 5))
        >>> order_stat_for_5d6avg = d6avg.order_stat_func_for_n(5)
        >>> order_stat_for_5d6avg(3)  # counts where outcome appears at index 3
        H({2: 26, 3: 1432, 4: 4792, 5: 1526})

        ```

        The results show that, when rolling five six-sided “averaging” dice and sorting
        each roll, there are 26 ways where ``#!python 2`` appears at the fourth (index
        ``#!python 3``) position, 1432 ways where ``#!python 3`` appears at the fourth
        position, etc. This can be verified independently using the computationally
        expensive method of enumerating rolls and counting those that meet the criteria.

        ``` python
        >>> from dyce import P
        >>> p_5d6avg = 5@P(d6avg)
        >>> sum(count for roll, count in p_5d6avg.rolls_with_counts() if roll[3] == 5)
        1526

        ```

        This method exists in addition to the
        [``H.order_stat_for_n_at_pos`` method][dyce.h.H.order_stat_for_n_at_pos] because
        computing the betas for each outcome in *n* is unnecessary for each *pos*. Where
        different *pos* values are needed for the same *n* (e.g., in a loop) and where
        *n* is large, that overhead can be significant. The returned function caches
        those betas for *n* such that repeated querying or results at *pos* can be
        computed much faster.

        ``` python
        In [2]: %timeit [H(6).order_stat_for_n_at_pos(100, i) for i in range(10)]
        1.61 s ± 31.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

        In [3]: %%timeit
           ...: order_stat_for_100d6_at_pos = H(6).order_stat_func_for_n(100)
           ...: [order_stat_for_100d6_at_pos(i) for i in range(10)]
        170 ms ± 3.41 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
        ```
        """
        betas_by_outcome: Dict[OutcomeT, Tuple[H, H]] = {}

        for outcome in self.outcomes():
            betas_by_outcome[outcome] = (
                n @ self.le(outcome),
                n @ self.lt(outcome),
            )

        def _gen_h_items_at_pos(pos: int) -> Iterator[Tuple[OutcomeT, int]]:
            for outcome, (h_le, h_lt) in betas_by_outcome.items():
                yield (
                    outcome,
                    h_le.gt(pos).get(True, 0) - h_lt.gt(pos).get(True, 0),
                )

        def order_stat_for_n_at_pos(pos: IntT) -> H:
            return H(_gen_h_items_at_pos(as_int(pos)))

        return order_stat_for_n_at_pos

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: _CoalesceT = coalesce_replace,
        max_depth: IntT = 1,
    ) -> H:
        r"""
        Calls *expand* on each outcome, recursively up to *max_depth* times. If *expand*
        returns a number, it replaces the outcome. If it returns an
        [``H`` object][dyce.h.H], *coalesce* is called on the outcome and the expanded
        histogram, and the returned histogram is folded into result. The default
        behavior for *coalesce* is to replace the outcome with the expanded histogram.
        Returned histograms are always reduced to their lowest terms.

        See [``coalesce_replace``][dyce.h.coalesce_replace] and the
        [``lowest_terms`` method][dyce.h.H.lowest_terms].

        This method can be used to model complex rules. The following models re-rolling
        a face of 1 on the first roll:

        ``` python
        >>> def reroll_one(h: H, outcome):
        ...   return h if outcome == 1 else outcome

        >>> H(6).substitute(reroll_one)
        H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

        ```

        See the [``explode`` method][dyce.h.H.explode] for a common shorthand for
        “exploding” dice (i.e., where, if the greatest face come up, the die is
        re-rolled and the result is added to a running sum).

        In nearly all cases, when a histogram is substituted for an outcome, it takes on
        the substituted outcome’s “scale”. In other words, the sum of the counts of the
        replacement retains the same proportion as the replaced outcome in relation to
        other outcomes. This becomes clearer when there is no overlap between the
        original histogram and the substitution.

        ``` python
        >>> orig = H({1: 1, 2: 2, 3: 3, 4: 4})
        >>> sub = orig.substitute(lambda h, outcome: -h if outcome == 4 else outcome) ; sub
        H({-4: 8, -3: 6, -2: 4, -1: 2, 1: 5, 2: 10, 3: 15})
        >>> sum(count for outcome, count in orig.items() if outcome == 4) / orig.total
        0.4
        >>> sum(count for outcome, count in sub.items() if outcome < 0) / sub.total
        0.4

        ```

        !!! tip "An important exception"

            If *coalesce* returns the empty histogram (``H({})``), the corresponding
            outcome and its counts are omitted from the result without substitution or
            scaling. A silly example is modeling a d5 by indefinitely re-rolling a d6
            until something other than a 6 comes up.

            ``` python
            >>> H(6).substitute(lambda h, outcome: H({}) if outcome == 6 else outcome)
            H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

            ```

            This technique is more useful when modeling re-rolling certain derived
            outcomes, like ties in a contest.

            ``` python
            >>> d6_3, d8_2 = 3@H(6), 2@H(8)
            >>> d6_3.vs(d8_2)
            H({-1: 4553, 0: 1153, 1: 8118})
            >>> d6_3.vs(d8_2).substitute(lambda h, outcome: H({}) if outcome == 0 else outcome)
            H({-1: 4553, 1: 8118})

            ```

        Because it delegates to a callback for refereeing substitution decisions,
        ``#!python substitute`` is quite flexible and well suited to modeling (or at
        least approximating) logical progressions. Consider the following rules:

          1. Start with a total of zero.
          2. Roll a six-sided die. Add the face to the total. If the face was a six, go
             to step 3. Otherwise stop.
          3. Roll a four-sided die. Add the face to the total. If the face was a four,
             go to step 2. Otherwise stop.

        What is the likelihood of an even final tally? This can be approximated by:

        ``` python
        >>> d4, d6 = H(4), H(6)

        >>> def reroll_greatest_on_d4_d6(h: H, outcome):
        ...   if outcome == max(h):
        ...     if h == d6: return d4
        ...     if h == d4: return d6
        ...   return outcome

        >>> import operator
        >>> h = d6.substitute(reroll_greatest_on_d4_d6, operator.__add__, max_depth=6)
        >>> h_even = h.is_even()
        >>> print("{:.3%}".format(h_even[1] / h_even.total))
        39.131%

        ```

        Surprised? Because both six and four are even numbers, the only way we keep
        rolling is if the total is even. You might think this would lead to evens being
        *more* likely. However, we only care about the final tally and the rules direct
        us to re-roll certain evens (nudging us toward an odd number more often than
        not).

        We can also use this method to model expected damage from a single attack in
        d20-like role playing games.

        ``` python
        >>> bonus = 1
        >>> dmg_dice = H(8)
        >>> dmg = dmg_dice + bonus
        >>> crit = dmg + dmg_dice
        >>> target = 15 - bonus
        >>> d20 = H(20)

        >>> def dmg_from_attack_roll(h: H, outcome):
        ...   if outcome == 20:
        ...     return crit
        ...   elif outcome >= target:
        ...     return dmg
        ...   else:
        ...     return 0

        >>> h = d20.substitute(dmg_from_attack_roll)
        >>> print(h.format(width=65, scaled=True))
        avg |    2.15
        std |    3.40
        var |   11.55
          0 |  65.00% |##################################################
          2 |   3.75% |##
          3 |   3.83% |##
          4 |   3.91% |###
          5 |   3.98% |###
          6 |   4.06% |###
          7 |   4.14% |###
          8 |   4.22% |###
          9 |   4.30% |###
         10 |   0.62% |
         11 |   0.55% |
         12 |   0.47% |
         13 |   0.39% |
         14 |   0.31% |
         15 |   0.23% |
         16 |   0.16% |
         17 |   0.08% |

        ```
        """
        max_depth = as_int(max_depth)

        def _substitute(h: H, depth: int = 0) -> H:
            assert coalesce is not None

            if depth == max_depth:
                return h

            total_scalar = 1
            items_for_reassembly: List[Tuple[OutcomeT, int, int]] = []

            for outcome, count in h.items():
                expanded = expand(h, outcome)

                if isinstance(expanded, H):
                    # Keep expanding deeper, if we can
                    expanded = _substitute(expanded, depth + 1)
                    # Coalesce the result
                    expanded = coalesce(expanded, outcome)
                    # Account for the impact of expansion on peers
                    expanded_scalar = expanded.total

                    if expanded_scalar:
                        total_scalar *= expanded_scalar
                        # Account for the impact of the original count on the result, but
                        # keep track of the impact on peers so we can factor it out for
                        # these items later
                        items_for_reassembly.extend(
                            (exp_f, exp_c * count, expanded_scalar)
                            for exp_f, exp_c in expanded.items()
                        )
                else:
                    items_for_reassembly.append((expanded, count, 1))

            return H(
                (
                    # Apply the total_scalar, but factor out this item's contribution
                    (outcome, count * total_scalar // s)
                    for outcome, count, s in items_for_reassembly
                )
            ).lowest_terms()

        return _substitute(self)

    def vs(self, other: _OperandT) -> H:
        r"""
        Compares the histogram with *other*. -1 represents where *other* is greater. 0
        represents where they are equal. 1 represents where *other* is less.

        Shorthand for ``#!python self.within(0, 0, other)``.

        ``` python
        >>> H(6).vs(H(4))
        H({-1: 6, 0: 4, 1: 14})
        >>> H(6).vs(H(4)) == H(6).within(0, 0, H(4))
        True

        ```

        See the [``within`` method][dyce.h.H.within].
        """
        return self.within(0, 0, other)

    def within(self, lo: OutcomeT, hi: OutcomeT, other: _OperandT = 0) -> H:
        r"""
        Computes the difference between the histogram and *other*. -1 represents where that
        difference is less than *lo*. 0 represents where that difference between *lo*
        and *hi* (inclusive). 1 represents where that difference is greater than *hi*.

        ``` python
        >>> d6_2 = 2@H(6)
        >>> d6_2.within(7, 9)
        H({-1: 15, 0: 15, 1: 6})
        >>> print(d6_2.within(7, 9).format(width=65))
        avg |   -0.25
        std |    0.72
        var |    0.52
         -1 |  41.67% |####################
          0 |  41.67% |####################
          1 |  16.67% |########

        ```

        ``` python
        >>> d6_3, d8_2 = 3@H(6), 2@H(8)
        >>> d6_3.within(-1, 1, d8_2)  # 3d6 w/in 1 of 2d8
        H({-1: 3500, 0: 3412, 1: 6912})
        >>> print(d6_3.within(-1, 1, d8_2).format(width=65))
        avg |    0.25
        std |    0.83
        var |    0.69
         -1 |  25.32% |############
          0 |  24.68% |############
          1 |  50.00% |#########################

        ```
        """
        return self.map(_within(lo, hi), other)

    @overload
    def distribution(
        self,
        fill_items: Optional[_MappingT] = None,
    ) -> Iterator[Tuple[OutcomeT, Fraction]]:
        ...

    @overload
    def distribution(
        self,
        fill_items: _MappingT,
        rational_t: _RationalConstructorT[_T],
    ) -> Iterator[Tuple[OutcomeT, _T]]:
        ...

    @overload
    def distribution(
        self,
        *,
        rational_t: _RationalConstructorT[_T],
    ) -> Iterator[Tuple[OutcomeT, _T]]:
        ...

    @experimental
    def distribution(
        self,
        fill_items: Optional[_MappingT] = None,
        # TODO(posita): See <https://github.com/python/mypy/issues/10854> for context on
        # all the @overload work-around nonsense above and remove those once that issue
        # is addressed.
        rational_t: _RationalConstructorT[_T] = Fraction,
    ) -> Iterator[Tuple[OutcomeT, _T]]:
        r"""
        Presentation helper function returning an iterator for each outcome/count or
        outcome/probability pair.

        ``` python
        >>> h = H((1, 2, 3, 3, 4, 4, 5, 6))
        >>> list(h.distribution())
        [(1, Fraction(1, 8)), (2, Fraction(1, 8)), (3, Fraction(1, 4)), (4, Fraction(1, 4)), (5, Fraction(1, 8)), (6, Fraction(1, 8))]
        >>> list(h.ge(3).distribution())
        [(False, Fraction(1, 4)), (True, Fraction(3, 4))]

        ```

        If provided, *fill_items* supplies defaults for any “missing” outcomes.

        ``` python
        >>> list(h.distribution())
        [(1, Fraction(1, 8)), (2, Fraction(1, 8)), (3, Fraction(1, 4)), (4, Fraction(1, 4)), (5, Fraction(1, 8)), (6, Fraction(1, 8))]
        >>> list(h.distribution(fill_items={0: 0, 7: 0}))
        [(0, Fraction(0, 1)), (1, Fraction(1, 8)), (2, Fraction(1, 8)), (3, Fraction(1, 4)), (4, Fraction(1, 4)), (5, Fraction(1, 8)), (6, Fraction(1, 8)), (7, Fraction(0, 1))]

        ```

        !!! warning "Experimental"

            The *rational_t* argument to this method should be considered experimental
            and may change or disappear in future versions.

        If provided, *rational_t* must be a callable that takes two ``#!python int``s (a
        numerator and denominator) and returns an instance of a desired (but otherwise
        arbitrary) type.

        ``` python
        >>> list(h.distribution(rational_t=lambda n, d: f"{n}/{d}"))
        [(1, '1/8'), (2, '1/8'), (3, '2/8'), (4, '2/8'), (5, '1/8'), (6, '1/8')]

        ```

        ``` python
        >>> import sympy
        >>> list(h.distribution(rational_t=sympy.Rational))
        [(1, 1/8), (2, 1/8), (3, 1/4), (4, 1/4), (5, 1/8), (6, 1/8)]

        ```

        ``` python
        >>> import sage.rings.rational  # doctest: +SKIP
        >>> list(h.distribution(rational_t=lambda n, d: sage.rings.rational.Rational((n, d))))  # doctest: +SKIP
        [(1, 1/8), (2, 1/8), (3, 1/4), (4, 1/4), (5, 1/8), (6, 1/8)]

        ```

        !!! tip

            The arguments passed to *rational_t* are not reduced to the lowest terms.

        The *rational_t* argument is a convenience. Iteration or comprehension can be
        used to accomplish something similar.

        ``` python
        >>> [(outcome, f"{probability.numerator}/{probability.denominator}") for outcome, probability in (h).distribution()]
        [(1, '1/8'), (2, '1/8'), (3, '1/4'), (4, '1/4'), (5, '1/8'), (6, '1/8')]

        ```

        Many number implementations can convert directly from ``#!python
        fractions.Fraction``s.

        ``` python
        >>> import sympy.abc  # doctest: +SKIP
        >>> [(outcome, sympy.Rational(probability)) for outcome, probability in (h + sympy.abc.x).distribution()]  # doctest: +SKIP
        [(x + 1, 1/8), (x + 2, 1/8), (x + 3, 1/4), (x + 4, 1/4), (x + 5, 1/8), (x + 6, 1/8)]

        ```

        ``` python
        >>> import sage.rings.rational  # doctest: +SKIP
        >>> [(outcome, sage.rings.rational.Rational(probability)) for outcome, probability in h.distribution()]  # doctest: +SKIP
        [(1, 1/6), (2, 1/6), (3, 1/3), (4, 1/3), (5, 1/6), (6, 1/6)]

        ```
        """
        if fill_items is None:
            fill_items = {}

        combined = dict(chain(fill_items.items(), self.items()))
        total = sum(combined.values()) or 1

        return (
            (outcome, rational_t(combined[outcome], total))
            for outcome in sorted_outcomes(combined)
        )

    def distribution_xy(
        self,
        fill_items: Optional[_MappingT] = None,
    ) -> Tuple[Tuple[OutcomeT, ...], Tuple[float, ...]]:
        r"""
        Presentation helper function returning an iterator for a “zipped” arrangement of the
        output from the [``distribution`` method][dyce.h.H.distribution] and ensures the
        values are ``#!python float``s.

        ``` python
        >>> list(H(6).distribution())
        [(1, Fraction(1, 6)), (2, Fraction(1, 6)), (3, Fraction(1, 6)), (4, Fraction(1, 6)), (5, Fraction(1, 6)), (6, Fraction(1, 6))]
        >>> H(6).distribution_xy()
        ((1, 2, 3, 4, 5, 6), (0.16666666, 0.16666666, 0.16666666, 0.16666666, 0.16666666, 0.16666666))

        ```
        """
        # TODO(posita): See <https://github.com/python/typing/issues/193>
        return tuple(  # type: ignore
            zip(
                *(
                    (outcome, float(probability))
                    for outcome, probability in self.distribution(fill_items)
                )
            )
        )

    def format(
        self,
        fill_items: Optional[_MappingT] = None,
        width: IntT = _ROW_WIDTH,
        scaled: bool = False,
        tick: str = "#",
        sep: str = os.linesep,
    ) -> str:
        r"""
        Returns a formatted string representation of the histogram. If provided,
        *fill_items* supplies defaults for any missing outcomes. If *width* is greater
        than zero, a horizontal bar ASCII graph is printed using *tick* and *sep* (which
        are otherwise ignored if *width* is zero or less).

        ``` python
        >>> print(H(6).format(width=0))
        {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}

        ```

        ``` python
        >>> print((2@H(6)).format(fill_items={i: 0 for i in range(1, 21)}, width=65, tick="@"))
        avg |    7.00
        std |    2.42
        var |    5.83
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

        If *scaled* is ``#!python True``, horizontal bars are scaled to *width*.

        ``` python
        >>> h = (2@H(6)).ge(7)
        >>> print("{:->65}".format(" 65 chars wide -->|"))
        ---------------------------------------------- 65 chars wide -->|
        >>> print(h.format(width=65, scaled=False))
        avg |    0.58
        std |    0.49
        var |    0.24
          0 |  41.67% |####################
          1 |  58.33% |#############################
        >>> print(h.format(width=65, scaled=True))
        avg |    0.58
        std |    0.49
        var |    0.24
          0 |  41.67% |###################################
          1 |  58.33% |##################################################

        ```
        """
        width = as_int(width)

        # We convert various values herein to native ints and floats because number
        # tower implementations sometimes neglect to implement __format__ properly (or
        # at all). (I'm looking at you, sage.rings.…!)
        try:
            mu: OutcomeT = float(self.mean())
        except TypeError:
            mu = self.mean()

        if width <= 0:

            def _parts() -> Iterator[str]:
                yield f"avg: {mu:.2f}"

                for (
                    outcome,
                    probability,
                ) in self.distribution(fill_items):
                    probability_f = float(probability)
                    yield f"{outcome}:{probability_f:7.2%}"

            return "{" + ", ".join(_parts()) + "}"
        else:
            w = width - 15

            def lines() -> Iterator[str]:
                yield f"avg | {mu:7.2f}"

                try:
                    std = float(self.stdev(mu))
                    var = float(self.variance(mu))
                    yield f"std | {std:7.2f}"
                    yield f"var | {var:7.2f}"
                except TypeError:
                    pass

                outcomes, probabilities = self.distribution_xy(fill_items)
                tick_scale = max(probabilities) if scaled else 1.0

                for outcome, probability in zip(outcomes, probabilities):
                    try:
                        outcome_str = f"{outcome: 3}"
                    except (TypeError, ValueError):
                        outcome_str = str(outcome)
                        outcome_str = f"{outcome_str: >3}"

                    ticks = tick * int(w * probability / tick_scale)
                    probability_f = float(probability)
                    yield f"{outcome_str} | {probability_f:7.2%} |{ticks}"

            return sep.join(lines())

    def mean(self) -> OutcomeT:
        r"""
        Returns the mean of the weighted outcomes (or 0.0 if there are no outcomes).
        """
        numerator: float
        denominator: float
        numerator = denominator = 0

        for outcome, count in self.items():
            numerator += outcome * count
            denominator += count

        return numerator / (denominator or 1)

    def stdev(self, mu: Optional[OutcomeT] = None) -> OutcomeT:
        r"""
        Shorthand for ``#!python math.sqrt(self.variance(mu))``.
        """
        return sqrt(self.variance(mu))

    def variance(self, mu: Optional[OutcomeT] = None) -> OutcomeT:
        r"""
        Returns the variance of the weighted outcomes. If provided, *mu* is used as the mean
        (to avoid duplicate computation).
        """
        mu = mu if mu else self.mean()
        numerator: float
        denominator: float
        numerator = denominator = 0

        for outcome, count in self.items():
            numerator += (outcome - mu) ** 2 * count
            denominator += count

        return numerator / (denominator or 1)

    def roll(self) -> OutcomeT:
        r"""
        Returns a (weighted) random outcome, sorted.

        !!! tip "On ordering"

            This method “works” (i.e., falls back to a “natural” ordering of string
            representations) for outcomes whose relative values cannot be known (e.g.,
            symbolic expressions). This is deliberate to allow random roll functionality
            where symbolic resolution is not needed or will happen later.
        """
        if not self:
            return 0

        return choices(tuple(self.outcomes()), tuple(self.counts()))[0]

    def _lowest_terms(self) -> Iterable[Tuple[OutcomeT, int]]:
        counts_gcd = gcd(*self.counts())

        return ((k, v // counts_gcd) for k, v in self.items())


@runtime_checkable
class HAbleT(
    Protocol,
    metaclass=CachingProtocolMeta,
):
    r"""
    A protocol whose implementer can be expressed as (or reduced to) an
    [``H`` object][dyce.h.H] by calling its [``h`` method][dyce.h.HAbleT.h]. Currently,
    only the [``P`` class][dyce.p.P] implements this protocol, but this affords an
    integration point for ``#!python dyce`` users.
    """

    def h(self) -> H:
        r"""
        Express its implementer as an [``H`` object][dyce.h.H].
        """
        ...


class HAbleOpsMixin:
    r"""
    A “mix-in” class providing arithmetic operations for implementers of the
    [``HAbleT`` protocol][dyce.h.HAbleT]. The [``P`` class][dyce.p.P] derives from this
    class.
    """

    def __add__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__add__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __add__(self.h(), other)

    def __radd__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__add__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __add__(other, self.h())

    def __sub__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__sub__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __sub__(self.h(), other)

    def __rsub__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__sub__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __sub__(other, self.h())

    def __mul__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__mul__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __mul__(self.h(), other)

    def __rmul__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__mul__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __mul__(other, self.h())

    def __truediv__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__truediv__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __truediv__(self.h(), other)

    def __rtruediv__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__truediv__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __truediv__(other, self.h())

    def __floordiv__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__floordiv__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __floordiv__(self.h(), other)

    def __rfloordiv__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__floordiv__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __floordiv__(other, self.h())

    def __mod__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__mod__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __mod__(self.h(), other)

    def __rmod__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__mod__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __mod__(other, self.h())

    def __pow__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__pow__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __pow__(self.h(), other)

    def __rpow__(self: HAbleT, other: OutcomeT) -> H:
        r"""
        Shorthand for ``#!python operator.__pow__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __pow__(other, self.h())

    def __and__(self: HAbleT, other: Union[IntT, H, HAbleT]) -> H:
        r"""
        Shorthand for ``#!python operator.__and__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __and__(self.h(), other)

    def __rand__(self: HAbleT, other: IntT) -> H:
        r"""
        Shorthand for ``#!python operator.__and__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __and__(other, self.h())

    def __xor__(self: HAbleT, other: Union[IntT, H, HAbleT]) -> H:
        r"""
        Shorthand for ``#!python operator.__xor__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __xor__(self.h(), other)

    def __rxor__(self: HAbleT, other: IntT) -> H:
        r"""
        Shorthand for ``#!python operator.__xor__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __xor__(other, self.h())

    def __or__(self: HAbleT, other: Union[IntT, H, HAbleT]) -> H:
        r"""
        Shorthand for ``#!python operator.__or__(self.h(), other)``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __or__(self.h(), other)

    def __ror__(self: HAbleT, other: IntT) -> H:
        r"""
        Shorthand for ``#!python operator.__or__(other, self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __or__(other, self.h())

    def __neg__(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python operator.__neg__(self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __neg__(self.h())

    def __pos__(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python operator.__pos__(self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __pos__(self.h())

    def __abs__(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python operator.__abs__(self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __abs__(self.h())

    def __invert__(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python operator.__invert__(self.h())``. See the
        [``h`` method][dyce.h.HAbleT.h].
        """
        return __invert__(self.h())

    def lt(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().lt(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.lt``][dyce.h.H.lt].
        """
        return self.h().lt(other)

    def le(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().le(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.le``][dyce.h.H.le].
        """
        return self.h().le(other)

    def eq(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().eq(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.eq``][dyce.h.H.eq].
        """
        return self.h().eq(other)

    def ne(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().ne(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.ne``][dyce.h.H.ne].
        """
        return self.h().ne(other)

    def gt(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().gt(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.gt``][dyce.h.H.gt].
        """
        return self.h().gt(other)

    def ge(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().ge(other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.ge``][dyce.h.H.ge].
        """
        return self.h().ge(other)

    def is_even(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python self.h().is_even()``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.is_even``][dyce.h.H.is_even].
        """
        return self.h().is_even()

    @deprecated
    def even(self: HAbleT) -> H:
        r"""
        !!! warning "Deprecated"

            This method is deprecated and will likely be removed in the next major
            release.

        Shorthand for ``#!python self.h().is_even()``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.is_even``][dyce.h.H.is_even].
        """
        return self.h().is_even()

    def is_odd(self: HAbleT) -> H:
        r"""
        Shorthand for ``#!python self.h().is_odd()``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.is_odd``][dyce.h.H.is_odd].
        """
        return self.h().is_odd()

    @deprecated
    def odd(self: HAbleT) -> H:
        r"""
        !!! warning "Deprecated"

            This method is deprecated and will likely be removed in the next major
            release.

        Shorthand for ``#!python self.h().is_odd()``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.is_odd``][dyce.h.H.is_odd].
        """
        return self.h().is_odd()

    def explode(self: HAbleT, max_depth: IntT = 1) -> H:
        r"""
        Shorthand for ``#!python self.h().explode(max_depth)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.explode``][dyce.h.H.explode].
        """
        return self.h().explode(max_depth)

    def substitute(
        self: HAbleT,
        expand: _ExpandT,
        coalesce: _CoalesceT = coalesce_replace,
        max_depth: IntT = 1,
    ) -> H:
        r"""
        Shorthand for ``#!python self.h().substitute(expand, coalesce, max_depth)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.substitute``][dyce.h.H.substitute].
        """
        return self.h().substitute(expand, coalesce, max_depth)

    def within(self: HAbleT, lo: OutcomeT, hi: OutcomeT, other: _OperandT = 0) -> H:
        r"""
        Shorthand for ``#!python self.h().within(lo, hi, other)``. See the
        [``h`` method][dyce.h.HAbleT.h] and [``H.within``][dyce.h.H.within].
        """
        return self.h().within(lo, hi, other)


# ---- Functions -----------------------------------------------------------------------


def _within(lo: OutcomeT, hi: OutcomeT) -> _BinaryOperatorT:
    if lo > hi:
        raise ValueError(f"lower bound ({lo}) is greater than upper bound ({hi})")

    def _cmp(a: OutcomeT, b: OutcomeT) -> int:
        # This approach will probably not work with most symbolic outcomes
        diff = a - b

        return bool(diff > hi) - bool(diff < lo)

    setattr(_cmp, "lo", lo)
    setattr(_cmp, "hi", hi)

    return _cmp

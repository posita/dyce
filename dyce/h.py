# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import os
import sys
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
from pprint import pformat
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
    Type,
    TypeVar,
    Union,
    ValuesView,
    cast,
    overload,
)

from numerary import RealLike
from numerary.bt import beartype
from numerary.types import CachingProtocolMeta, Protocol, SupportsInt, runtime_checkable

from . import rng
from .lifecycle import deprecated, experimental
from .symmetries import comb, gcd
from .types import (
    _BinaryOperatorT,
    _RationalInitializerT,
    _UnaryOperatorT,
    as_int,
    is_even,
    is_odd,
    sorted_outcomes,
)

__all__ = ("H",)


# ---- Types ---------------------------------------------------------------------------


_T = TypeVar("_T")
_MappingT = Mapping[RealLike, int]
_SourceT = Union[
    SupportsInt,
    Iterable[RealLike],
    Iterable[Tuple[RealLike, SupportsInt]],
    _MappingT,
    "HableT",
]
_OperandT = Union[RealLike, "H", "HableT"]
_ExpandT = Callable[["H", RealLike], Union["H", RealLike]]
_CoalesceT = Callable[["H", RealLike], "H"]


# ---- Data ----------------------------------------------------------------------------


try:
    _ROW_WIDTH = int(os.environ["COLUMNS"])
except (KeyError, ValueError):
    _ROW_WIDTH = 65


# ---- Functions -----------------------------------------------------------------------


def coalesce_replace(h: H, outcome: RealLike) -> H:
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
    objects encode finite discrete probability distributions as integer counts without
    any denominator.

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
    >>> print((d6 + d6).format())
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
    >>> print(d6.ne(d6).format())
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
    >>> print(d6.lt(d6).format())
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
    >>> print((4@d6_eq2).ge(1).format())
    avg |    0.52
    std |    0.50
    var |    0.25
      0 |  48.23% |########################
      1 |  51.77% |#########################

    ```

    !!! bug "Mind your parentheses"

        Parentheses are often necessary to enforce the desired order of operations. This
        is most often an issue with the ``#!python @`` operator, because it behaves
        differently than the ``d`` operator in most dedicated grammars. More
        specifically, in Python, ``#!python @`` has a [lower
        precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence)
        than ``#!python .`` and ``#!python […]``.

        ``` python
        >>> 2@d6[7]  # type: ignore [operator]
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
    __slots__: Union[str, Iterable[str]] = ("_h", "_simple_init")

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(self, items: _SourceT) -> None:
        r"Initializer."
        super().__init__()
        self._simple_init: Optional[int] = None
        tmp: Counter[RealLike] = counter()

        if isinstance(items, MappingC):
            items = items.items()

        if isinstance(items, SupportsInt):
            if items != 0:
                self._simple_init = as_int(items)
                outcome_range = range(
                    self._simple_init,
                    0,
                    1 if self._simple_init < 0 else -1,  # count toward zero
                )

                if isinstance(items, RealLike):
                    outcome_type = type(items)
                    tmp.update({outcome_type(i): 1 for i in outcome_range})
                else:
                    tmp.update({i: 1 for i in outcome_range})
        elif isinstance(items, HableT):
            tmp.update(items.h())
        elif isinstance(items, IterableC):
            # items is either an Iterable[RealLike] or an Iterable[Tuple[RealLike,
            # SupportsInt]] (although this technically supports Iterable[Union[RealLike,
            # Tuple[RealLike, SupportsInt]]])
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

    @beartype
    def __repr__(self) -> str:
        if self._simple_init is not None:
            arg = str(self._simple_init)
        elif sys.version_info >= (3, 8):
            arg = pformat(self._h, sort_dicts=False)
        else:
            arg = dict.__repr__(self._h)

        return f"{type(self).__name__}({arg})"

    @beartype
    def __eq__(self, other) -> bool:
        if isinstance(other, HableT):
            return __eq__(self, other.h())
        elif isinstance(other, H):
            return __eq__(self.lowest_terms()._h, other.lowest_terms()._h)
        else:
            return super().__eq__(other)

    @beartype
    def __ne__(self, other) -> bool:
        if isinstance(other, HableT):
            return __ne__(self, other.h())
        elif isinstance(other, H):
            return not __eq__(self, other)
        else:
            return super().__ne__(other)

    @beartype
    def __hash__(self) -> int:
        return hash(frozenset(self._lowest_terms()))

    @beartype
    def __len__(self) -> int:
        return len(self._h)

    @beartype
    def __getitem__(self, key: RealLike) -> int:
        return __getitem__(self._h, key)

    @beartype
    def __iter__(self) -> Iterator[RealLike]:
        return iter(self._h)

    @beartype
    def __add__(self, other: _OperandT) -> H:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __sub__(self, other: _OperandT) -> H:
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rsub__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mul__(self, other: _OperandT) -> H:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmul__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __matmul__(self, other: SupportsInt) -> H:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return sum_h(repeat(self, other))

    @beartype
    def __rmatmul__(self, other: SupportsInt) -> H:
        return self.__matmul__(other)

    @beartype
    def __truediv__(self, other: _OperandT) -> H:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rtruediv__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __floordiv__(self, other: _OperandT) -> H:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rfloordiv__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mod__(self, other: _OperandT) -> H:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmod__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __pow__(self, other: _OperandT) -> H:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rpow__(self, other: RealLike) -> H:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __and__(self, other: Union[SupportsInt, "H", "HableT"]) -> H:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__and__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rand__(self, other: SupportsInt) -> H:
        try:
            return self.rmap(as_int(other), __and__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __xor__(self, other: Union[SupportsInt, "H", "HableT"]) -> H:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__xor__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rxor__(self, other: SupportsInt) -> H:
        try:
            return self.rmap(as_int(other), __xor__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __or__(self, other: Union[SupportsInt, "H", "HableT"]) -> H:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__or__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __ror__(self, other: SupportsInt) -> H:
        try:
            return self.rmap(as_int(other), __or__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __neg__(self) -> H:
        return self.umap(__neg__)

    @beartype
    def __pos__(self) -> H:
        return self.umap(__pos__)

    @beartype
    def __abs__(self) -> H:
        return self.umap(__abs__)

    @beartype
    def __invert__(self) -> H:
        return self.umap(__invert__)

    @beartype
    def counts(self) -> ValuesView[int]:
        r"""
        More descriptive synonym for the [``values`` method][dyce.h.H.values].
        """
        return self._h.values()

    @beartype
    def items(self) -> ItemsView[RealLike, int]:
        return self._h.items()

    @beartype
    def keys(self) -> KeysView[RealLike]:
        return self.outcomes()

    @beartype
    def outcomes(self) -> KeysView[RealLike]:
        r"""
        More descriptive synonym for the [``keys`` method][dyce.h.H.keys].
        """
        return self._h.keys()

    @beartype
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

    @classmethod
    @beartype
    def foreach(
        cls,
        dependent_term: Callable[..., Union["H", RealLike]],
        **independent_sources: _SourceT,
    ) -> H:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Calls ``#!python dependent_term`` for each set of outcomes from the product of
        ``independent_sources`` and accumulates the results. This is useful for
        resolving dependent probabilities. Returned histograms are always reduced to
        their lowest terms.

        For example rolling a d20, re-rolling a ``#!python 1`` if it comes up, and
        keeping the result might be expressed as[^1]:

        [^1]:

            This is primarily for illustration. [``H.substitute``][dyce.h.H.substitute]
            is often better suited to cases involving re-rolling a single independent
            term such as this one.

        ``` python
        >>> d20 = H(20)

        >>> def reroll_one_dependent_term(d20_outcome):
        ...   if d20_outcome == 1:
        ...     return d20
        ...   else:
        ...     return d20_outcome

        >>> H.foreach(reroll_one_dependent_term, d20_outcome=d20)
        H({1: 1,
         2: 21,
         3: 21,
         ...,
         19: 21,
         20: 21})

        ```

        The ``#!python foreach`` class method merely wraps *dependent_term* and calls
        [``P.foreach``][dyce.p.P.foreach]. In doing so, it imposes a very modest
        overhead that is negligible in most cases.

        ``` python
        --8<-- "docs/assets/perf_foreach.txt"
        ```

        <details>
        <summary>Source: <a href="https://github.com/posita/dyce/blob/latest/docs/assets/perf_foreach.ipy"><code>perf_foreach.ipy</code></a></summary>

        ``` python
        --8<-- "docs/assets/perf_foreach.ipy"
        ```
        </details>
        """
        from dyce import P

        def _dependent_term(**roll_kw):
            outcome_kw: Dict[str, RealLike] = {}

            for key, roll in roll_kw.items():
                assert isinstance(roll, tuple)
                assert len(roll) == 1
                outcome_kw[key] = roll[0]

            return dependent_term(**outcome_kw)

        return P.foreach(_dependent_term, **independent_sources)

    @beartype
    def map(self, bin_op: _BinaryOperatorT, right_operand: _OperandT) -> H:
        r"""
        Applies *bin_op* to each outcome of the histogram as the left operand and
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
        if isinstance(right_operand, HableT):
            right_operand = right_operand.h()

        if isinstance(right_operand, H):
            return type(self)(
                (bin_op(s, o), self[s] * right_operand[o])
                for s, o in product(self, right_operand)
            )
        else:
            return type(self)(
                (bin_op(outcome, right_operand), count)
                for outcome, count in self.items()
            )

    @beartype
    def rmap(self, left_operand: RealLike, bin_op: _BinaryOperatorT) -> H:
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

        !!! note

            The positions of *left_operand* and *bin_op* are different from
            [``map`` method][dyce.h.H.map]. This is intentional and serves as a reminder
            of operand ordering.
        """
        return type(self)(
            (bin_op(left_operand, outcome), count) for outcome, count in self.items()
        )

    @beartype
    def umap(self, un_op: _UnaryOperatorT) -> H:
        r"""
        Applies *un_op* to each outcome of the histogram.

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
        h = type(self)((un_op(outcome), count) for outcome, count in self.items())

        if self._simple_init is not None:
            simple_init = un_op(self._simple_init)

            if isinstance(simple_init, SupportsInt):
                h_simple = type(self)(simple_init)

                if h_simple == h:
                    return h_simple

        return h

    @beartype
    def lt(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__lt__, other).umap(bool)``.

        ``` python
        >>> H(6).lt(3)
        H({False: 4, True: 2})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__lt__, other).umap(bool)

    @beartype
    def le(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__le__, other).umap(bool)``.

        ``` python
        >>> H(6).le(3)
        H({False: 3, True: 3})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__le__, other).umap(bool)

    @beartype
    def eq(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__eq__, other).umap(bool)``.

        ``` python
        >>> H(6).eq(3)
        H({False: 5, True: 1})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__eq__, other).umap(bool)

    @beartype
    def ne(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__ne__, other).umap(bool)``.

        ``` python
        >>> H(6).ne(3)
        H({False: 1, True: 5})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__ne__, other).umap(bool)

    @beartype
    def gt(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__gt__, other).umap(bool)``.

        ``` python
        >>> H(6).gt(3)
        H({False: 3, True: 3})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__gt__, other).umap(bool)

    @beartype
    def ge(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.map(operator.__ge__, other).umap(bool)``.

        ``` python
        >>> H(6).ge(3)
        H({False: 2, True: 4})

        ```

        See the [``map``][dyce.h.H.map] and [``umap``][dyce.h.H.umap] methods.
        """
        return self.map(__ge__, other).umap(bool)

    @beartype
    def is_even(self) -> H:
        r"""
        Equivalent to ``#!python self.umap(dyce.types.is_even)``.

        ``` python
        >>> H((-4, -2, 0, 1, 2, 3)).is_even()
        H({False: 2, True: 4})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """
        return self.umap(is_even)

    @beartype
    def is_odd(self) -> H:
        r"""
        Equivalent to ``#!python self.umap(dyce.types.is_odd)``.

        ``` python
        >>> H((-4, -2, 0, 1, 2, 3)).is_odd()
        H({False: 4, True: 2})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """
        return self.umap(is_odd)

    @beartype
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
            other = cast(Iterable[RealLike], (other,))

        return type(self)(chain(self.items(), cast(Iterable, other)))

    @experimental
    @beartype
    def exactly_k_times_in_n(
        self,
        outcome: RealLike,
        n: SupportsInt,
        k: SupportsInt,
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

    @beartype
    def explode(self, max_depth: SupportsInt = 1) -> H:
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

    @beartype
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
        return type(self)(self._lowest_terms())

    @experimental
    @beartype
    def order_stat_for_n_at_pos(self, n: SupportsInt, pos: SupportsInt) -> H:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Shorthand for ``#!python self.order_stat_func_for_n(n)(pos)``.
        """
        # TODO(posita): Explore different memoization strategies (e.g., with
        # functools.cache) for this method and H.order_stat_func_for_n
        return self.order_stat_func_for_n(n)(pos)

    @experimental
    @beartype
    def order_stat_func_for_n(self, n: SupportsInt) -> Callable[[SupportsInt], "H"]:
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
        --8<-- "docs/assets/perf_order_stat_for_n.txt"
        ```

        <details>
        <summary>Source: <a href="https://github.com/posita/dyce/blob/latest/docs/assets/perf_order_stat_for_n.ipy"><code>perf_order_stat_for_n.ipy</code></a></summary>

        ``` python
        --8<-- "docs/assets/perf_order_stat_for_n.ipy"
        ```
        </details>
        """
        betas_by_outcome: Dict[RealLike, Tuple[H, H]] = {}

        for outcome in self.outcomes():
            betas_by_outcome[outcome] = (
                n @ self.le(outcome),
                n @ self.lt(outcome),
            )

        def _gen_h_items_at_pos(pos: int) -> Iterator[Tuple[RealLike, int]]:
            for outcome, (h_le, h_lt) in betas_by_outcome.items():
                yield (
                    outcome,
                    h_le.gt(pos).get(True, 0) - h_lt.gt(pos).get(True, 0),
                )

        @beartype
        def order_stat_for_n_at_pos(pos: SupportsInt) -> H:
            return type(self)(_gen_h_items_at_pos(as_int(pos)))

        return order_stat_for_n_at_pos

    @beartype
    def substitute(
        self,
        expand: _ExpandT,
        coalesce: _CoalesceT = coalesce_replace,
        max_depth: SupportsInt = 1,
    ) -> H:
        r"""
        Calls *expand* on each outcome, recursively up to *max_depth* times. If *expand*
        returns a number, it replaces the outcome. If it returns an
        [``H`` object][dyce.h.H], *coalesce* is called on the outcome and the expanded
        histogram, and the returned histogram is folded into result. The default
        behavior for *coalesce* is to replace the outcome with the expanded histogram.
        Returned histograms are always reduced to their lowest terms.

        See the [``coalesce_replace``][dyce.h.coalesce_replace] and
        [``lowest_terms``][dyce.h.H.lowest_terms] methods.

        This method can be used to model complex mechanics. The following models
        re-rolling a face of 1 on the first roll:

        ``` python
        >>> def reroll_one(h: H, outcome):
        ...   return h if outcome == 1 else outcome

        >>> H(6).substitute(reroll_one)
        H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

        ```

        See the [``explode`` method][dyce.h.H.explode] for a common shorthand for
        “exploding” dice (i.e., where, if the greatest face come up, the die is
        re-rolled and the result is added to a running sum).

        This method uses the [``aggregate_with_counts``][dyce.h.aggregate_with_counts]
        function in its implementation. As such, If *coalesce* returns the empty
        histogram (``H({})``), the corresponding outcome and its counts are omitted from
        the result without substitution or scaling. A silly example is modeling a d5 by
        indefinitely re-rolling a d6 until something other than a 6 comes up.

        ``` python
        >>> H(6).substitute(lambda __, outcome: H({}) if outcome == 6 else outcome)
        H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

        ```

        This technique is more useful when modeling re-rolling certain derived
        outcomes, like ties in a contest.

        ``` python
        >>> d6_3, d8_2 = 3@H(6), 2@H(8)
        >>> d6_3.vs(d8_2)
        H({-1: 4553, 0: 1153, 1: 8118})
        >>> d6_3.vs(d8_2).substitute(lambda __, outcome: H({}) if outcome == 0 else outcome)
        H({-1: 4553, 1: 8118})

        ```

        Because it delegates to a callback for refereeing substitution decisions,
        ``#!python substitute`` is quite flexible and well suited to modeling (or at
        least approximating) logical progressions with dependent variables. Consider the
        following mechanic:

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
        >>> print(f"{h_even[1] / h_even.total:.3%}")
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
        >>> print(h.format(scaled=True))
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

        if max_depth < 0:
            raise ValueError("max_depth cannot be negative")

        def _substitute(h: H, depth: int = 0) -> H:
            assert coalesce is not None

            if depth == max_depth:
                return h

            def _expand_and_coalesce() -> Iterator[Tuple[Union[H, RealLike], int]]:
                for outcome, count in h.items():
                    expanded = expand(h, outcome)

                    if isinstance(expanded, H):
                        # Keep expanding deeper, if we can
                        expanded = _substitute(expanded, depth + 1)
                        # Coalesce the result
                        expanded = coalesce(expanded, outcome)

                    yield expanded, count

            return aggregate_with_counts(_expand_and_coalesce(), type(self))

        return _substitute(self).lowest_terms()

    @beartype
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

    @beartype
    def within(self, lo: RealLike, hi: RealLike, other: _OperandT = 0) -> H:
        r"""
        Computes the difference between the histogram and *other*. -1 represents where that
        difference is less than *lo*. 0 represents where that difference between *lo*
        and *hi* (inclusive). 1 represents where that difference is greater than *hi*.

        ``` python
        >>> d6_2 = 2@H(6)
        >>> d6_2.within(7, 9)
        H({-1: 15, 0: 15, 1: 6})
        >>> print(d6_2.within(7, 9).format())
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
        >>> print(d6_3.within(-1, 1, d8_2).format())
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
    ) -> Iterator[Tuple[RealLike, Fraction]]:
        ...

    @overload
    def distribution(
        self,
        fill_items: _MappingT,
        rational_t: _RationalInitializerT[_T],
    ) -> Iterator[Tuple[RealLike, _T]]:
        ...

    @overload
    def distribution(
        self,
        *,
        rational_t: _RationalInitializerT[_T],
    ) -> Iterator[Tuple[RealLike, _T]]:
        ...

    @experimental
    @beartype
    def distribution(
        self,
        fill_items: Optional[_MappingT] = None,
        # TODO(posita): See <https://github.com/python/mypy/issues/10854> for context on
        # all the @overload work-around nonsense above and remove those once that issue
        # is addressed.
        rational_t: _RationalInitializerT[_T] = cast(_RationalInitializerT, Fraction),
    ) -> Iterator[Tuple[RealLike, _T]]:
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

        !!! note

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
        >>> import sympy.abc
        >>> [(outcome, sympy.Rational(probability)) for outcome, probability in (h + sympy.abc.x).distribution()]
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

    @beartype
    def distribution_xy(
        self,
        fill_items: Optional[_MappingT] = None,
    ) -> Tuple[Tuple[RealLike, ...], Tuple[float, ...]]:
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
        return tuple(  # type: ignore [return-value]
            zip(
                *(
                    (outcome, float(probability))
                    for outcome, probability in self.distribution(fill_items)
                )
            )
        )

    @beartype
    def format(
        self,
        fill_items: Optional[_MappingT] = None,
        width: SupportsInt = _ROW_WIDTH,
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
        >>> print((2@H(6)).format(fill_items={i: 0 for i in range(1, 21)}, tick="@"))
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
        >>> print(f"{' 65 chars wide -->|':->65}")
        ---------------------------------------------- 65 chars wide -->|
        >>> print(h.format(scaled=False))
        avg |    0.58
        std |    0.49
        var |    0.24
          0 |  41.67% |####################
          1 |  58.33% |#############################
        >>> print(h.format(scaled=True))
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
            mu: RealLike = float(self.mean())
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

            @beartype
            def lines() -> Iterator[str]:
                yield f"avg | {mu:7.2f}"

                try:
                    std = float(self.stdev(mu))
                    var = float(self.variance(mu))
                    yield f"std | {std:7.2f}"
                    yield f"var | {var:7.2f}"
                except TypeError:
                    pass

                if self:
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

    @beartype
    def mean(self) -> RealLike:
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

    @beartype
    def stdev(self, mu: Optional[RealLike] = None) -> RealLike:
        r"""
        Shorthand for ``#!python math.sqrt(self.variance(mu))``.
        """
        return sqrt(self.variance(mu))

    @beartype
    def variance(self, mu: Optional[RealLike] = None) -> RealLike:
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

    @beartype
    def roll(self) -> RealLike:
        r"""
        Returns a (weighted) random outcome, sorted.
        """
        return (
            rng.RNG.choices(
                population=tuple(self.outcomes()),
                weights=tuple(self.counts()),
                k=1,
            )[0]
            if self
            else 0
        )

    def _lowest_terms(self) -> Iterable[Tuple[RealLike, int]]:
        counts_gcd = gcd(*self.counts())

        return ((k, v // counts_gcd) for k, v in self.items())


@runtime_checkable
class HableT(
    Protocol,
    metaclass=CachingProtocolMeta,
):
    r"""
    A protocol whose implementer can be expressed as (or reduced to) an
    [``H`` object][dyce.h.H] by calling its [``h`` method][dyce.h.HableT.h]. Currently,
    only the [``P`` class][dyce.p.P] implements this protocol, but this affords an
    integration point for ``#!python dyce`` users.

    !!! info

        The intended pronunciation of ``Hable`` is *AYCH-uh-bul*[^1] (i.e.,
        [``H``][dyce.h.H]-able). Yes, that is a clumsy attempt at
        [verbing](https://www.gocomics.com/calvinandhobbes/1993/01/25). (You could
        *totally* [``H``][dyce.h.H] that, dude!) However, if you prefer something else
        (e.g. *HAY-bul* or *AYCH-AY-bul*), no one is going to judge you. (Well, they
        *might*, but they *shouldn’t*.) We all know what you mean.

    [^1]:

        World Book Online (WBO) style [pronunciation
        respelling](https://en.wikipedia.org/wiki/Pronunciation_respelling_for_English#Traditional_respelling_systems).
    """
    __slots__: Union[str, Iterable[str]] = ()

    def h(self) -> H:
        r"""
        Express its implementer as an [``H`` object][dyce.h.H].
        """
        ...


class HableOpsMixin:
    r"""
    A “mix-in” class providing arithmetic operations for implementers of the
    [``HableT`` protocol][dyce.h.HableT]. The [``P`` class][dyce.p.P] derives from this
    class.

    !!! info

        See [``HableT``][dyce.h.HableT] for notes on pronunciation.
    """
    __slots__: Union[str, Iterable[str]] = ()

    @beartype
    def __add__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__add__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __add__(self.h(), other)

    @beartype
    def __radd__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__add__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __add__(other, self.h())

    @beartype
    def __sub__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__sub__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __sub__(self.h(), other)

    @beartype
    def __rsub__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__sub__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __sub__(other, self.h())

    @beartype
    def __mul__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__mul__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __mul__(self.h(), other)

    @beartype
    def __rmul__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__mul__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __mul__(other, self.h())

    @beartype
    def __truediv__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__truediv__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __truediv__(self.h(), other)

    @beartype
    def __rtruediv__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__truediv__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __truediv__(other, self.h())

    @beartype
    def __floordiv__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__floordiv__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __floordiv__(self.h(), other)

    @beartype
    def __rfloordiv__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__floordiv__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __floordiv__(other, self.h())

    @beartype
    def __mod__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__mod__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __mod__(self.h(), other)

    @beartype
    def __rmod__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__mod__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __mod__(other, self.h())

    @beartype
    def __pow__(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python operator.__pow__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __pow__(self.h(), other)

    @beartype
    def __rpow__(self: HableT, other: RealLike) -> H:
        r"""
        Shorthand for ``#!python operator.__pow__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __pow__(other, self.h())

    @beartype
    def __and__(self: HableT, other: Union[SupportsInt, H, HableT]) -> H:
        r"""
        Shorthand for ``#!python operator.__and__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __and__(self.h(), other)

    @beartype
    def __rand__(self: HableT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``#!python operator.__and__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __and__(other, self.h())

    @beartype
    def __xor__(self: HableT, other: Union[SupportsInt, H, HableT]) -> H:
        r"""
        Shorthand for ``#!python operator.__xor__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __xor__(self.h(), other)

    @beartype
    def __rxor__(self: HableT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``#!python operator.__xor__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __xor__(other, self.h())

    @beartype
    def __or__(self: HableT, other: Union[SupportsInt, H, HableT]) -> H:
        r"""
        Shorthand for ``#!python operator.__or__(self.h(), other)``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __or__(self.h(), other)

    @beartype
    def __ror__(self: HableT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``#!python operator.__or__(other, self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __or__(other, self.h())

    @beartype
    def __neg__(self: HableT) -> H:
        r"""
        Shorthand for ``#!python operator.__neg__(self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __neg__(self.h())

    @beartype
    def __pos__(self: HableT) -> H:
        r"""
        Shorthand for ``#!python operator.__pos__(self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __pos__(self.h())

    @beartype
    def __abs__(self: HableT) -> H:
        r"""
        Shorthand for ``#!python operator.__abs__(self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __abs__(self.h())

    @beartype
    def __invert__(self: HableT) -> H:
        r"""
        Shorthand for ``#!python operator.__invert__(self.h())``. See the
        [``h`` method][dyce.h.HableT.h].
        """
        return __invert__(self.h())

    @beartype
    def lt(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().lt(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.lt``][dyce.h.H.lt].
        """
        return self.h().lt(other)

    @beartype
    def le(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().le(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.le``][dyce.h.H.le].
        """
        return self.h().le(other)

    @beartype
    def eq(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().eq(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.eq``][dyce.h.H.eq].
        """
        return self.h().eq(other)

    @beartype
    def ne(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().ne(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.ne``][dyce.h.H.ne].
        """
        return self.h().ne(other)

    @beartype
    def gt(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().gt(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.gt``][dyce.h.H.gt].
        """
        return self.h().gt(other)

    @beartype
    def ge(self: HableT, other: _OperandT) -> H:
        r"""
        Shorthand for ``#!python self.h().ge(other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.ge``][dyce.h.H.ge].
        """
        return self.h().ge(other)

    @beartype
    def is_even(self: HableT) -> H:
        r"""
        Shorthand for ``#!python self.h().is_even()``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.is_even``][dyce.h.H.is_even].
        """
        return self.h().is_even()

    @beartype
    def is_odd(self: HableT) -> H:
        r"""
        Shorthand for ``#!python self.h().is_odd()``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.is_odd``][dyce.h.H.is_odd].
        """
        return self.h().is_odd()

    @beartype
    def explode(self: HableT, max_depth: SupportsInt = 1) -> H:
        r"""
        Shorthand for ``#!python self.h().explode(max_depth)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.explode``][dyce.h.H.explode].
        """
        return self.h().explode(max_depth)

    @beartype
    def substitute(
        self: HableT,
        expand: _ExpandT,
        coalesce: _CoalesceT = coalesce_replace,
        max_depth: SupportsInt = 1,
    ) -> H:
        r"""
        Shorthand for ``#!python self.h().substitute(expand, coalesce, max_depth)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.substitute``][dyce.h.H.substitute].
        """
        return self.h().substitute(expand, coalesce, max_depth)

    @beartype
    def within(self: HableT, lo: RealLike, hi: RealLike, other: _OperandT = 0) -> H:
        r"""
        Shorthand for ``#!python self.h().within(lo, hi, other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.within``][dyce.h.H.within].
        """
        return self.h().within(lo, hi, other)


# ---- Functions -----------------------------------------------------------------------


@beartype
def aggregate_with_counts(
    source_counts: Iterable[Tuple[Union[H, RealLike], int]],
    h_type: Type[H] = H,
) -> H:
    r"""
    Aggregates *source_counts* into an [``H`` object][dyce.h.H]. Each source_count is a
    two-tuple of either an outcome-count pair or a histogram-count pair. This function
    is used in the implementation of the [``H.substitute``][dyce.h.H.substitute] and
    [``P.foreach``][dyce.p.P.foreach] methods. Unlike those, the histogram returned from
    this function is *not* reduced to its lowest terms.

    In nearly all cases, when a source contains a histogram, it takes on the
    corresponding count’s “scale”. In other words, the sum of the counts of the
    histogram retains the same proportion as the count in relation to other outcomes.
    This becomes clearer when there is no overlap between the histogram and the other
    outcomes.

    ``` python
    >>> from dyce.h import aggregate_with_counts
    >>> source_counts = ((H(3), 3), (H(-3), 2))
    >>> h = aggregate_with_counts(source_counts).lowest_terms() ; h
    H({-3: 2, -2: 2, -1: 2, 1: 3, 2: 3, 3: 3})

    ```

    !!! note "An important exception"

        If a source is the empty histogram (``H({})``), it and its count is omitted from
        the result without scaling.

        ``` python
        >>> source_counts = ((H(2), 1), (H({}), 20))
        >>> aggregate_with_counts(source_counts)
        H({1: 1, 2: 1})

        ```
    """
    aggregate_scalar = 1
    outcome_counts: List[Tuple[RealLike, int]] = []

    for outcome_or_h, count in source_counts:
        if isinstance(outcome_or_h, H):
            if outcome_or_h:
                h_scalar = outcome_or_h.total

                for i, (prior_outcome, prior_count) in enumerate(outcome_counts):
                    outcome_counts[i] = (prior_outcome, prior_count * h_scalar)

                for new_outcome, new_count in outcome_or_h.items():
                    outcome_counts.append(
                        (new_outcome, count * aggregate_scalar * new_count)
                    )

                aggregate_scalar *= h_scalar
        else:
            outcome_counts.append((outcome_or_h, count * aggregate_scalar))

    return h_type(outcome_counts)


@deprecated
def resolve_dependent_probability(
    dependent_term: Callable[..., Union[H, RealLike]],
    **independent_sources: _SourceT,
) -> H:
    r"""
    !!! warning "Deprecated"

        This function has been moved to the [``H.foreach``][dyce.h.H.foreach] class
        method. This alias will be removed in a future release.

    Shorthand for ``#!python H.foreach(dependent_term, **independent_sources)``.
    """
    return H.foreach(dependent_term, **independent_sources)


@beartype
def sum_h(hs: Iterable[H]):
    """
    Shorthand for ``#!python H({}) if h_sum == 0 else sum(hs)``.

    This is to ensure that summing zero or more histograms always returns a histograms.
    """
    h_sum = sum(hs)

    return H({}) if h_sum == 0 else h_sum


@beartype
def _within(lo: RealLike, hi: RealLike) -> _BinaryOperatorT:
    if __gt__(lo, hi):
        raise ValueError(f"lower bound ({lo}) is greater than upper bound ({hi})")

    def _cmp(a: RealLike, b: RealLike) -> int:
        # This approach will probably not work with most symbolic outcomes
        diff = a - b

        return bool(__gt__(diff, hi)) - bool(__lt__(diff, lo))

    setattr(_cmp, "lo", lo)
    setattr(_cmp, "hi", hi)

    return _cmp

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import os
import warnings
from abc import abstractmethod
from collections import Counter
from collections.abc import Iterable as IterableC
from fractions import Fraction
from itertools import chain, product, repeat
from math import comb, gcd, sqrt
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
from typing import (
    Any,
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Optional,
    TypeVar,
    Union,
    ValuesView,
    cast,
    overload,
)

from numerary import IntegralLike, RealLike
from numerary.bt import beartype
from numerary.protocol import CachingProtocolMeta
from numerary.types import Protocol, RationalLikeMixedU, SupportsInt, runtime_checkable

from . import rng
from .lifecycle import deprecated, experimental
from .types import (
    _BinaryOperatorT,
    _UnaryOperatorT,
    as_int,
    is_even,
    is_odd,
    natural_key,
    sorted_outcomes,
)

__all__ = ("H",)


# ---- Types ---------------------------------------------------------------------------


HOrOutcomeT = Union["H", RealLike]
_T = TypeVar("_T")
_MappingT = Mapping[RealLike, int]
_SourceT = Union[
    SupportsInt,
    Iterable[RealLike],
    Iterable[tuple[RealLike, SupportsInt]],
    _MappingT,
    "HableT",
]
_OperandT = Union[RealLike, "H", "HableT"]
_OutcomeCountT = tuple[RealLike, int]
_SubstituteExpandCallbackT = Callable[["H", RealLike], HOrOutcomeT]
_SubstituteCoalesceCallbackT = Callable[["H", RealLike], "H"]


# ---- Data ----------------------------------------------------------------------------


try:
    _ROW_WIDTH = int(os.environ["COLUMNS"])
except (KeyError, ValueError):
    _ROW_WIDTH = 65


# ---- Functions -----------------------------------------------------------------------


@deprecated
def coalesce_replace(h: "H", outcome: RealLike) -> "H":
    r"""
    !!! warning "Deprecated"

        This function has been deprecated and will be removed in a future release. See
        the [``expandable`` decorator][dyce.evaluation.expandable] and
        [``foreach`` function][dyce.evaluation.foreach] for more flexible alternatives.

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

    __slots__: Any = (
        "_h",
        "_hash",
        "_lowest_terms",
        "_order_stat_funcs_by_n",
        "_total",
    )

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(self, items: _SourceT) -> None:
        r"Initializer."
        super().__init__()
        self._h: _MappingT

        if isinstance(items, H):
            self._h = items._h
        elif isinstance(items, SupportsInt):
            if items == 0:
                self._h = {}
            else:
                simple_init = as_int(items)
                outcome_range = range(
                    simple_init if simple_init < 0 else 1,
                    0 if simple_init < 0 else simple_init + 1,
                )

                # if isinstance(items, RealLike):
                #     outcome_type = type(items)
                #     self._h = {outcome_type(i): 1 for i in outcome_range}
                # else:
                #     self._h = {i: 1 for i in outcome_range}
                assert isinstance(items, RealLike)
                outcome_type = type(items)
                self._h = {outcome_type(i): 1 for i in outcome_range}
        elif isinstance(items, HableT):
            self._h = items.h()._h
        elif isinstance(items, IterableC):
            if isinstance(items, Mapping):
                items = items.items()

            # items is either an Iterable[RealLike] or an Iterable[tuple[RealLike,
            # SupportsInt]] (although this technically supports Iterable[RealLike |
            # tuple[RealLike, SupportsInt]])
            self._h = {}
            sorted_items = list(items)

            try:
                sorted_items.sort()
            except TypeError:
                sorted_items.sort(key=natural_key)

            # As of Python 3.7, insertion order of keys is preserved
            for item in sorted_items:
                if isinstance(item, tuple):
                    outcome, count = item
                    count = as_int(count)
                else:
                    outcome = item
                    count = 1

                if count < 0:
                    raise ValueError(f"count for {outcome} cannot be negative")

                if outcome not in self._h:
                    self._h[outcome] = 0

                self._h[outcome] += count
        else:
            raise TypeError(f"unrecognized initializer type {items!r}")

        # We can't use something like functools.lru_cache for these values because those
        # mechanisms call this object's __hash__ method which relies on both of these
        # and we don't want a circular dependency when computing this object's hash.
        self._hash: Optional[int] = None
        self._total: int = sum(self._h.values())
        self._lowest_terms: Optional[H] = None

        # We don't use functools' caching mechanisms generally because they don't
        # present a good mechanism for scoping the cache to object instances such that
        # the cache will be purged when the object is deleted. functools.cached_property
        # is an exception, but it requires that objects have proper __dict__ values,
        # which Hs do not. So we basically do what functools.cached_property does, but
        # without a __dict__.
        self._order_stat_funcs_by_n: dict[int, Callable[[int], H]] = {}

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict.__repr__(self._h)})"

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
        if self._hash is None:
            self._hash = hash(frozenset(self.lowest_terms().items()))

        return self._hash

    @beartype
    def __bool__(self) -> int:
        return bool(self.total)

    @beartype
    def __len__(self) -> int:
        return len(self._h)

    @beartype
    def __getitem__(self, key: RealLike) -> int:
        return __getitem__(self._h, key)

    @beartype
    def __iter__(self) -> Iterator[RealLike]:
        yield from self._h

    @beartype
    def __reversed__(self) -> Iterator[RealLike]:
        return reversed(self._h)

    @beartype
    def __contains__(self, key: RealLike) -> bool:  # type: ignore [override]
        return key in self._h

    @beartype
    def __add__(self, other: _OperandT) -> "H":
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __sub__(self, other: _OperandT) -> "H":
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rsub__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mul__(self, other: _OperandT) -> "H":
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmul__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __matmul__(self, other: SupportsInt) -> "H":
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return sum_h(repeat(self, other))

    @beartype
    def __rmatmul__(self, other: SupportsInt) -> "H":
        return self.__matmul__(other)

    @beartype
    def __truediv__(self, other: _OperandT) -> "H":
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rtruediv__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __floordiv__(self, other: _OperandT) -> "H":
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rfloordiv__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mod__(self, other: _OperandT) -> "H":
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmod__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __pow__(self, other: _OperandT) -> "H":
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rpow__(self, other: RealLike) -> "H":
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    # TODO(posita): See <https://github.com/beartype/beartype/issues/152>
    def __and__(self, other: Union[SupportsInt, "H", "HableT"]) -> "H":
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__and__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rand__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(as_int(other), __and__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    # TODO(posita): See <https://github.com/beartype/beartype/issues/152>
    def __xor__(self, other: Union[SupportsInt, "H", "HableT"]) -> "H":
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__xor__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rxor__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(as_int(other), __xor__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    # TODO(posita): See <https://github.com/beartype/beartype/issues/152>
    def __or__(self, other: Union[SupportsInt, "H", "HableT"]) -> "H":
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__or__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __ror__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(as_int(other), __or__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __neg__(self) -> "H":
        return self.umap(__neg__)

    @beartype
    def __pos__(self) -> "H":
        return self.umap(__pos__)

    @beartype
    def __abs__(self) -> "H":
        return self.umap(__abs__)

    @beartype
    def __invert__(self) -> "H":
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
    def reversed(self) -> Iterator[RealLike]:
        return reversed(self)

    @beartype
    def values(self) -> ValuesView[int]:
        return self.counts()

    # ---- Properties ------------------------------------------------------------------

    @property
    def total(self) -> int:
        r"""
        !!! warning "Experimental"

            This property should be considered experimental and may change or disappear
            in future versions.

        Equivalent to ``#!python sum(self.counts())``.
        """
        return self._total

    # ---- Methods ---------------------------------------------------------------------

    @classmethod
    @deprecated
    @beartype
    def foreach(
        cls,
        dependent_term: Callable[..., HOrOutcomeT],
        **independent_sources: _SourceT,
    ) -> "H":
        r"""
        !!! warning "Deprecated"

            This method has been deprecated and will be removed in a future release. See
            the [``expandable`` decorator][dyce.evaluation.expandable] and
            [``foreach`` function][dyce.evaluation.foreach] for more flexible
            alternatives.

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
        H({1: 1, 2: 21, 3: 21, ..., 19: 21, 20: 21})

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

        def _dependent_term(**roll_kw) -> HOrOutcomeT:
            outcome_kw: dict[str, RealLike] = {}

            for key, roll in roll_kw.items():
                assert isinstance(roll, tuple)
                assert len(roll) == 1
                outcome_kw[key] = roll[0]

            return dependent_term(**outcome_kw)

        return P.foreach(_dependent_term, **independent_sources)

    @beartype
    def map(self, bin_op: _BinaryOperatorT, right_operand: _OperandT) -> "H":
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
    def rmap(self, left_operand: RealLike, bin_op: _BinaryOperatorT) -> "H":
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
    def umap(self, un_op: _UnaryOperatorT) -> "H":
        r"""
        Applies *un_op* to each outcome of the histogram.

        ``` python
        >>> import operator
        >>> H(6).umap(operator.__neg__)
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})

        ```

        ``` python
        >>> H(4).umap(lambda outcome: (-outcome) ** outcome)
        H({-27: 1, -1: 1, 4: 1, 256: 1})

        ```
        """
        return type(self)((un_op(outcome), count) for outcome, count in self.items())

    @beartype
    def lt(self, other: _OperandT) -> "H":
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
    def le(self, other: _OperandT) -> "H":
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
    def eq(self, other: _OperandT) -> "H":
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
    def ne(self, other: _OperandT) -> "H":
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
    def gt(self, other: _OperandT) -> "H":
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
    def ge(self, other: _OperandT) -> "H":
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
    def is_even(self) -> "H":
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
    def is_odd(self) -> "H":
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
    def accumulate(self, other: _SourceT) -> "H":
        r"""
        Accumulates counts.

        ``` python
        >>> H(4).accumulate(H(6))
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})

        ```
        """
        if not isinstance(other, H):
            other = H(other)

        return type(self)(cast(_SourceT, chain(self.items(), other.items())))

    @beartype
    def draw(
        self,
        outcomes: Optional[Union[RealLike, Iterable[RealLike], _MappingT]] = None,
    ) -> "H":
        r"""
        !!! warning "Experimental"

            This property should be considered experimental and may change or disappear
            in future versions.

        Returns a new [``H`` object][dyce.h.H] where the counts associated with
        *outcomes* has been updated. This may be useful for using histograms to model
        decks of cards (rather than dice). If *outcome* is ``#!python None``, this is
        equivalent to ``#!python self.draw(self.roll())``.

        If *outcomes* is a single value, that value’s count is decremented by one. If
        *outcomes* is an iterable of values, those values’ outcomes are decremented by
        one for each time that outcome appears. If *outcomes* is a mapping of outcomes
        to counts, those outcomes are decremented by the respective counts.

        Counts are not reduced and zero counts are preserved. To reduce, call the
        [``lowest_terms`` method][dyce.h.H.lowest_terms].

        <!-- BEGIN MONKEY PATCH --
        For deterministic outcomes.

        >>> import random
        >>> from dyce import rng
        >>> rng.RNG = random.Random(1691413956)

          -- END MONKEY PATCH -->

        ``` python
        >>> H(6).draw()
        H({1: 1, 2: 1, 3: 1, 4: 0, 5: 1, 6: 1})

        >>> H(6).draw(2)
        H({1: 1, 2: 0, 3: 1, 4: 1, 5: 1, 6: 1})

        >>> H(6).draw((2, 3, 4, 5)).lowest_terms()
        H({1: 1, 6: 1})

        >>> h = H(6).accumulate(H(4)) ; h
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})
        >>> h.draw({1: 2, 4: 1, 6: 1})
        H({1: 0, 2: 2, 3: 2, 4: 1, 5: 1, 6: 0})

        ```

        !!! tip "Negative counts can be used to increase counts"

            Where *outcomes* is a mapping of outcomes to counts, negative counts can be
            used to *increase* or “add” outcomes’ counts.

            ``` python
            >>> H(4).draw({5: -1})
            H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

            ```
        """
        if outcomes is None:
            return self.draw(self.roll())

        if isinstance(outcomes, RealLike):
            outcomes = (outcomes,)

        to_draw_outcome_counts = Counter(outcomes)
        self_outcome_counts = Counter(self)
        # This approach is necessary because Counter.__sub__ does not preserve negative
        # counts and Counter.subtract modifies the counter in-place
        new_outcome_counts = Counter(self_outcome_counts)
        new_outcome_counts.subtract(to_draw_outcome_counts)
        would_go_negative = set(+to_draw_outcome_counts) - set(+self_outcome_counts)

        if would_go_negative:
            raise ValueError(f"outcomes to be drawn {would_go_negative} not in {self}")

        zeros = set(self_outcome_counts) - set(new_outcome_counts)

        for outcome in zeros:
            new_outcome_counts[outcome] = 0

        return type(self)(new_outcome_counts)

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

        Computes (in constant time) and returns the number of times *outcome* appears
        exactly *k* times among ``#!python n@self``. This computes the binomial
        coefficient as a more efficient alternative to ``#!python
        (n@(self.eq(outcome)))[k]``. See [this
        video](https://www.khanacademy.org/math/ap-statistics/random-variables-ap/binomial-random-variable/v/generalizing-k-scores-in-n-attempts)
        for a pretty clear explanation.

        ``` python
        >>> H(6).exactly_k_times_in_n(outcome=5, n=4, k=2)
        150
        >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=2, n=3, k=3)
        1
        >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=4, n=3, k=3)
        8

        ```

        !!! note "Counts, *not* probabilities"

            This computes the *number* of ways to get exactly *k* of *outcome* from *n*
            like histograms, which may not expressed in the lowest terms. (See the
            [``lowest_terms`` method][dyce.h.H.lowest_terms].) If we want the
            *probability* of getting exactly *k* of *outcome* from *n* like histograms,
            we can divide by ``#!python h.total ** n``. (See the
            [``total`` property][dyce.h.H.total].)

            ``` python
            >>> from fractions import Fraction
            >>> h = H((2, 3, 3, 4, 4, 5))
            >>> n, k = 3, 2
            >>> (n @ h).total == h.total ** n
            True
            >>> Fraction(
            ...   h.exactly_k_times_in_n(outcome=3, n=n, k=k),
            ...   h.total ** n,
            ... )
            Fraction(2, 9)
            >>> h_not_lowest_terms = h.accumulate(h)
            >>> h == h_not_lowest_terms
            True
            >>> h_not_lowest_terms
            H({2: 2, 3: 4, 4: 4, 5: 2})
            >>> h_not_lowest_terms.exactly_k_times_in_n(outcome=3, n=n, k=k)
            384
            >>> Fraction(
            ...   h_not_lowest_terms.exactly_k_times_in_n(outcome=3, n=n, k=k),
            ...   h_not_lowest_terms.total ** n,
            ... )
            Fraction(2, 9)

            ```
        """
        n = as_int(n)
        k = as_int(k)
        assert k <= n
        c_outcome = self.get(outcome, 0)

        return (
            # number of ways to choose k things from n things (k <= n)
            comb(n, k)
            # cumulative counts for the particular outcomes we want
            * c_outcome**k
            # cumulative counts for all other outcomes
            * (self.total - c_outcome) ** (n - k)
        )

    @overload
    def explode(
        self,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> "H": ...

    @overload
    def explode(
        self,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> "H": ...

    @overload
    def explode(
        self,
        max_depth: None = None,
        *,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> "H": ...

    @overload
    def explode(
        self,
        max_depth: None = None,
        precision_limit: None = None,
    ) -> "H": ...

    @deprecated
    @beartype
    def explode(
        self,
        max_depth: Optional[IntegralLike] = None,
        precision_limit: Optional[Union[RationalLikeMixedU, RealLike]] = None,
    ) -> "H":
        r"""
        !!! warning "Deprecated"

            This method has been deprecated and will be removed in a future release. See
            the [``explode`` function][dyce.evaluation.explode] for a more flexible
            alternative.

        Shorthand for ``#!python self.substitute(lambda h, outcome: outcome if len(h) == 1
        else h if outcome == max(h) else outcome, operator.__add__, max_depth,
        precision_limit)``.

        ``` python
        >>> H(6).explode(max_depth=2)
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})

        ```

        This method guards against excessive recursion by returning ``#!python outcome``
        if the passed histogram has only one face. See the [``substitute``
        method][dyce.h.H.substitute].
        """

        def _explode(h: H, outcome: RealLike) -> HOrOutcomeT:
            return outcome if len(h) == 1 else h if outcome == max(h) else outcome

        if max_depth is not None and precision_limit is not None:
            raise ValueError("only one of max_depth and precision_limit is allowed")
        elif max_depth is not None:
            return self.substitute(_explode, __add__, max_depth)
        elif precision_limit is not None:
            return self.substitute(_explode, __add__, precision_limit=precision_limit)
        else:
            return self.substitute(_explode, __add__)

    @beartype
    def lowest_terms(self) -> "H":
        r"""
        Computes and returns a histogram whose nonzero counts share a greatest
        common divisor of 1.

        ``` python
        >>> df_obscured = H({-2: 0, -1: 2, 0: 2, 1: 2, 2: 0})
        >>> df_obscured.lowest_terms()
        H({-1: 1, 0: 1, 1: 1})

        ```
        """
        if self._lowest_terms is None:
            counts_gcd = gcd(*self.counts())

            if counts_gcd in (0, 1) and 0 not in self.counts():
                self._lowest_terms = self
            else:
                self._lowest_terms = type(self)(
                    (outcome, count // counts_gcd)
                    for outcome, count in self.items()
                    if count != 0
                )

        return self._lowest_terms

    @experimental
    @beartype
    def order_stat_for_n_at_pos(self, n: SupportsInt, pos: SupportsInt) -> "H":
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions.

        Computes the probability distribution for each outcome appearing in at *pos* in
        rolls of *n* histograms where rolls are ordered least-to-greatest. *pos* is a
        zero-based index.

        ``` python
        >>> d6avg = H((2, 3, 3, 4, 4, 5))
        >>> d6avg.order_stat_for_n_at_pos(5, 3)  # counts where outcome appears in the fourth of five positions
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

        Negative values for *pos* follow Python index semantics:

        ``` python
        >>> d6 = H(6)
        >>> d6.order_stat_for_n_at_pos(6, 0) == d6.order_stat_for_n_at_pos(6, -6)
        True
        >>> d6.order_stat_for_n_at_pos(6, 5) == d6.order_stat_for_n_at_pos(6, -1)
        True

        ```

        This method caches computing the betas for *n* so they can be reused for varying
        values of *pos* in subsequent calls.
        """
        # See <https://math.stackexchange.com/q/4173084/226394> for motivation
        n = as_int(n)
        pos = as_int(pos)

        if n not in self._order_stat_funcs_by_n:
            self._order_stat_funcs_by_n[n] = self._order_stat_func_for_n(n)

        if pos < 0:
            pos = n + pos

        return self._order_stat_funcs_by_n[n](pos)

    @beartype
    def remove(self, outcome: RealLike) -> "H":
        if outcome not in self:
            return self

        return type(self)(
            (orig_outcome, count)
            for orig_outcome, count in self.items()
            if orig_outcome != outcome
        )

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        *,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        *,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: None = None,
        *,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> "H": ...

    @overload
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: None = None,
        precision_limit: None = None,
    ) -> "H": ...

    @deprecated
    @beartype
    def substitute(
        self,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: Optional[IntegralLike] = None,
        precision_limit: Optional[Union[RationalLikeMixedU, RealLike]] = None,
    ) -> "H":
        r"""
        !!! warning "Deprecated"

            This method has been deprecated and will be removed in a future release. See
            the [``expandable`` decorator][dyce.evaluation.expandable] and
            [``foreach`` function][dyce.evaluation.foreach] for more flexible
            alternatives.

        Calls *expand* on each outcome. If *expand* returns a single outcome, it
        replaces the existing outcome. If it returns an [``H`` object][dyce.h.H],
        evaluation is performed again (recursively) on that object until a limit (either
        *max_depth* or *precision_limit*) is exhausted. *coalesce* is called on the
        original outcome and the expanded histogram or outcome and the returned
        histogram is “folded” into result. The default behavior for *coalesce* is to
        replace the outcome with the expanded histogram. Returned histograms are always
        reduced to their lowest terms.

        !!! note "*coalesce* is not called unless *expand* returns a histogram"

            If *expand* returns a single outcome, it *always* replaces the existing
            outcome. This is intentional. To return a single outcome, but trigger
            *coalesce*, characterize that outcome as a single-sided die (e.g.,
            ``#!python H({outcome: 1})``.

        See the [``coalesce_replace``][dyce.h.coalesce_replace] and
        [``lowest_terms``][dyce.h.H.lowest_terms] methods.

        !!! tip "Precision limits"

            The *max_depth* parameter is similar to an
            [``expandable``][dyce.evaluation.expandable]-decorated function’s limit
            argument when given a whole number. The *precision_limit* parameter is
            similar to an [``expandable``][dyce.evaluation.expandable]-decorated
            function’s limit argument being provided a fractional value. It is an error
            to provide values for both *max_depth* and *precision_limit*.
        """
        from .evaluation import HResult, LimitT, expandable

        if max_depth is not None and precision_limit is not None:
            raise ValueError("only one of max_depth and precision_limit is allowed")

        limit: Optional[LimitT] = (
            max_depth if precision_limit is None else precision_limit
        )

        @expandable(sentinel=self)
        def _expand(result: HResult) -> HOrOutcomeT:
            res = expand(result.h, result.outcome)

            return coalesce(_expand(res), result.outcome) if isinstance(res, H) else res

        return _expand(self, limit=limit)

    @beartype
    def vs(self, other: _OperandT) -> "H":
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
    def within(self, lo: RealLike, hi: RealLike, other: _OperandT = 0) -> "H":
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

    @beartype
    def zero_fill(self, outcomes: Iterable[RealLike]) -> "H":
        r"""
        Shorthand for ``#!python self.accumulate({outcome: 0 for outcome in
        outcomes})``.

        ``` python
        >>> H(4).zero_fill(H(8).outcomes())
        H({1: 1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0})

        ```
        """
        return self.accumulate({outcome: 0 for outcome in outcomes})

    @overload
    def distribution(
        self,
    ) -> Iterator[tuple[RealLike, Fraction]]: ...

    @overload
    def distribution(
        self,
        rational_t: Callable[[int, int], _T],
    ) -> Iterator[tuple[RealLike, _T]]: ...

    @experimental
    @beartype
    def distribution(
        self,
        rational_t: Optional[Callable[[int, int], _T]] = None,
    ) -> Iterator[tuple[RealLike, _T]]:
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
        if rational_t is None:
            # TODO(posita): See <https://github.com/python/mypy/issues/10854#issuecomment-1663057450>
            rational_t = Fraction  # type: ignore [assignment]
            assert rational_t is not None

        total = sum(self.values()) or 1

        return (
            (outcome, rational_t(self[outcome], total))
            for outcome in sorted_outcomes(self)
        )

    @beartype
    def distribution_xy(
        self,
    ) -> tuple[tuple[RealLike, ...], tuple[float, ...]]:
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
        return tuple(
            zip(
                *(
                    (outcome, float(probability))
                    for outcome, probability in self.distribution()
                )
            )
        )

    @beartype
    def format(
        self,
        width: SupportsInt = _ROW_WIDTH,
        scaled: bool = False,
        tick: str = "#",
        sep: str = os.linesep,
    ) -> str:
        r"""
        Returns a formatted string representation of the histogram. If *width* is
        greater than zero, a horizontal bar ASCII graph is printed using *tick* and
        *sep* (which are otherwise ignored if *width* is zero or less).

        ``` python
        >>> print(H(6).format(width=0))
        {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}

        ```

        ``` python
        >>> print((2@H(6)).zero_fill(range(1, 21)).format(tick="@"))
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
        >>> print(H(1).format(scaled=False))
        avg |    1.00
        std |    0.00
        var |    0.00
          1 | 100.00% |##################################################
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
        except (OverflowError, TypeError):
            mu = self.mean()

        if width <= 0:

            def _parts() -> Iterator[str]:
                yield f"avg: {mu:.2f}"

                for (
                    outcome,
                    probability,
                ) in self.distribution():
                    probability_f = float(probability)
                    yield f"{outcome}:{probability_f:7.2%}"

            return "{" + ", ".join(_parts()) + "}"
        else:
            w = width - 15

            def _lines() -> Iterator[str]:
                try:
                    yield f"avg | {mu:7.2f}"
                    std = float(self.stdev(mu))
                    var = float(self.variance(mu))
                    yield f"std | {std:7.2f}"
                    yield f"var | {var:7.2f}"
                except (OverflowError, TypeError) as exc:
                    warnings.warn(f"{str(exc)}; mu: {mu}")

                if self:
                    outcomes, probabilities = self.distribution_xy()
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

            return sep.join(_lines())

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
            numerator += outcome**2 * count
            denominator += count

        # While floating point overflow is impossible to eliminate, we avoid it under
        # some circumstances by exploiting the equivalence of E[(X - E[X])**2] and the
        # more efficient E[X**2] - E[X]**2. See
        # <https://dlsun.github.io/probability/variance.html>.
        return numerator / (denominator or 1) - mu**2

    @beartype
    def roll(self) -> RealLike:
        r"""
        Returns a (weighted) random outcome.
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

    def _order_stat_func_for_n(self, n: int) -> Callable[[int], "H"]:
        betas_by_outcome: dict[RealLike, tuple[H, H]] = {}

        for outcome in self.outcomes():
            betas_by_outcome[outcome] = (
                n @ self.le(outcome),
                n @ self.lt(outcome),
            )

        def _gen_h_items_at_pos(pos: int) -> Iterator[_OutcomeCountT]:
            for outcome, (h_le, h_lt) in betas_by_outcome.items():
                yield (
                    outcome,
                    h_le.gt(pos).get(True, 0) - h_lt.gt(pos).get(True, 0),
                )

        @beartype
        def order_stat_for_n_at_pos(pos: int) -> "H":
            return type(self)(_gen_h_items_at_pos(pos))

        return order_stat_for_n_at_pos


@runtime_checkable
class HableT(Protocol, metaclass=CachingProtocolMeta):
    r"""
    A protocol whose implementer can be expressed as (or reduced to) an
    [``H`` object][dyce.h.H] by calling its [``h`` method][dyce.h.HableT.h]. Currently,
    only the [``P`` class][dyce.p.P] implements this protocol, but this affords an
    integration point for ``#!python dyce`` users.

    !!! info

        The intended pronunciation of ``Hable`` is *AYCH-uh-BUL*[^1] (i.e.,
        [``H``][dyce.h.H]-able). Yes, that is a clumsy attempt at
        [verbing](https://www.gocomics.com/calvinandhobbes/1993/01/25). (You could
        *totally* [``H``][dyce.h.H] that, dude!) However, if you prefer something else
        (e.g. *HAY-bul* or *AYCH-AY-bul*), no one is going to judge you. (Well, they
        *might*, but they *shouldn’t*.) We all know what you mean.

    [^1]:

        World Book Online (WBO) style [pronunciation
        respelling](https://en.wikipedia.org/wiki/Pronunciation_respelling_for_English#Traditional_respelling_systems).
    """

    __slots__: Any = ()

    @abstractmethod
    def h(self) -> H:
        r"""
        Express its implementer as an [``H`` object][dyce.h.H].
        """
        pass


class HableOpsMixin(HableT):
    r"""
    A “mix-in” class providing arithmetic operations for implementers of the
    [``HableT`` protocol][dyce.h.HableT]. The [``P`` class][dyce.p.P] derives from this
    class.

    !!! info

        See [``HableT``][dyce.h.HableT] for notes on pronunciation.
    """

    __slots__: Any = ()

    def __init__(self):
        object.__init__(self)

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

    @overload
    def explode(
        self: HableT,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> H: ...

    @overload
    def explode(
        self: HableT,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> H: ...

    @overload
    def explode(
        self: HableT,
        max_depth: None = None,
        *,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> H: ...

    @overload
    def explode(
        self: HableT,
        max_depth: None = None,
        precision_limit: None = None,
    ) -> H: ...

    @beartype
    def explode(
        self: HableT,
        max_depth: Optional[IntegralLike] = None,
        precision_limit: Optional[Union[RationalLikeMixedU, RealLike]] = None,
    ) -> H:
        r"""
        Shorthand for ``#!python self.h().explode(max_depth, precision_limit)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.explode``][dyce.h.H.explode].
        """
        if max_depth is not None and precision_limit is not None:
            raise ValueError("only one of max_depth and precision_limit is allowed")
        elif max_depth is not None:
            return self.h().explode(max_depth)
        elif precision_limit is not None:
            return self.h().explode(precision_limit=precision_limit)
        else:
            return self.h().explode()

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        *,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> H: ...

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT,
        max_depth: IntegralLike,
        precision_limit: None = None,
    ) -> H: ...

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        *,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> H: ...

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT,
        max_depth: None,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> H: ...

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: None = None,
        *,
        precision_limit: Union[RationalLikeMixedU, RealLike],
    ) -> H: ...

    @overload
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: None = None,
        precision_limit: None = None,
    ) -> H: ...

    @deprecated
    @beartype
    def substitute(
        self: HableT,
        expand: _SubstituteExpandCallbackT,
        coalesce: _SubstituteCoalesceCallbackT = coalesce_replace,
        max_depth: Optional[IntegralLike] = None,
        precision_limit: Optional[Union[RationalLikeMixedU, RealLike]] = None,
    ) -> H:
        r"""
        !!! warning "Deprecated"

            This method has been deprecated and will be removed in a future release. See
            the [``expandable`` decorator][dyce.evaluation.expandable] and
            [``foreach`` function][dyce.evaluation.foreach] for more flexible
            alternatives.

        Shorthand for ``#!python self.h().substitute(expand, coalesce, max_depth)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.substitute``][dyce.h.H.substitute].
        """
        if max_depth is not None and precision_limit is not None:
            raise ValueError("only one of max_depth and precision_limit is allowed")
        elif max_depth is not None:
            return self.h().substitute(expand, coalesce, max_depth)
        elif precision_limit is not None:
            return self.h().substitute(
                expand, coalesce, precision_limit=precision_limit
            )
        else:
            return self.h().substitute(expand, coalesce)

    @beartype
    def within(self: HableT, lo: RealLike, hi: RealLike, other: _OperandT = 0) -> H:
        r"""
        Shorthand for ``#!python self.h().within(lo, hi, other)``. See the
        [``h`` method][dyce.h.HableT.h] and [``H.within``][dyce.h.H.within].
        """
        return self.h().within(lo, hi, other)


# ---- Functions -----------------------------------------------------------------------


@deprecated
def resolve_dependent_probability(
    dependent_term: Callable[..., HOrOutcomeT],
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

    This is to ensure that summing zero or more histograms always returns a histogram.
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

    return _cmp

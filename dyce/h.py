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
from collections.abc import Iterable as ABCIterable
from collections.abc import Mapping as ABCMapping
from itertools import chain, product, repeat
from math import comb, sqrt
from operator import abs as op_abs
from operator import add as op_add
from operator import and_ as op_and
from operator import eq as op_eq
from operator import floordiv as op_floordiv
from operator import ge as op_ge
from operator import getitem as op_getitem
from operator import gt as op_gt
from operator import invert as op_invert
from operator import le as op_le
from operator import lt as op_lt
from operator import mod as op_mod
from operator import mul as op_mul
from operator import ne as op_ne
from operator import neg as op_neg
from operator import or_ as op_or
from operator import pos as op_pos
from operator import pow as op_pow
from operator import sub as op_sub
from operator import truediv as op_truediv
from operator import xor as op_xor
from random import choices
from typing import (
    Callable,
    Counter,
    Dict,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Protocol,
    SupportsInt,
    Tuple,
    TypeVar,
    Union,
    ValuesView,
    cast,
    runtime_checkable,
)

from .experimental import experimental
from .numtypes import OutcomeP, as_int
from .symmetries import gcd

__all__ = ("H",)


# ---- Types ---------------------------------------------------------------------------


_T_co = TypeVar("_T_co", covariant=True)
_MappingT = Mapping[OutcomeP, int]
_SourceT = Union[
    SupportsInt,
    Iterable[OutcomeP],
    Iterable[Tuple[OutcomeP, SupportsInt]],
    _MappingT,
    "HAbleT",
]
_OperandT = Union[OutcomeP, "H", "HAbleT"]
_UnaryOperatorT = Callable[[_T_co], _T_co]
_BinaryOperatorT = Callable[[_T_co, _T_co], _T_co]
_ExpandT = Callable[["H", OutcomeP], Union[OutcomeP, "H"]]
_CoalesceT = Callable[["H", OutcomeP], "H"]


# ---- Data ----------------------------------------------------------------------------


try:
    _ROW_WIDTH = os.get_terminal_size().columns
except OSError:
    try:
        _ROW_WIDTH = int(os.environ["COLUMNS"])
    except (KeyError, ValueError):
        _ROW_WIDTH = 88


# ---- Classes -------------------------------------------------------------------------


class H(_MappingT):
    r"""
    An immutable mapping for use as a histogram which supports arithmetic operations.
    This is useful for modeling discrete outcomes, like individual dice. ``H`` objects
    encode discrete probability distributions as integer counts without any denominator.

    !!! info

        The lack of an explicit denominator is intentional and has two benefits. First,
        it is redundant. Without it, one never has to worry about probabilities summing
        to one (e.g., via miscalculation, floating point error, etc.). Second (and
        perhaps more importantly), sometimes one wants to have an insight into
        non-reduced counts, not just probabilities. If needed, probabilities can always
        be derives, as shown below.

    The [initializer][dyce.h.H.__init__] takes a single parameter, *items*. In its most
    explicit form, *items* maps outcome values to counts.

    Modeling a single six-sided die (``1d6``) can be expressed as:

    ```python
    >>> from dyce import H
    >>> d6 = H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    ```

    An iterable of pairs can also be used (similar to ``dict``):

    ```python
    >>> d6 == H(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)))
    True

    ```

    Two shorthands are provided. If *items* is an iterable of numbers, counts of 1 are
    assumed:

    ```python
    >>> d6 == H((1, 2, 3, 4, 5, 6))
    True

    ```

    Repeated items are accumulated, as one would expect:

    ```python
    >>> H((2, 3, 3, 4, 4, 5))
    H({2: 1, 3: 2, 4: 2, 5: 1})

    ```

    If *items* is an integer, it is shorthand for creating a sequential range $[{1} ..
    {items}]$ (or $[{items} .. {-1}]$ if *items* is negative):

    ```python
    >>> d6 == H(6)
    True

    ```

    Histograms are maps, so we can test equivalence against other maps:

    ```python
    >>> H(6) == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}
    True

    ```

    Simple indexes can be used to look up an outcome’s count:

    ```python
    >>> H((2, 3, 3, 4, 4, 5))[3]
    2

    ```

    Most arithmetic operators are supported and do what one would expect. If the operand
    is a number, the operator applies to the outcomes:

    ```python
    >>> d6 + 4
    H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})

    ```

    ```python
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
    provides a shorthand:

    ```python
    >>> 3@d6 == d6 + d6 + d6
    True

    ```

    The ``len`` built-in function can be used to show the number of distinct outcomes:

    ```python
    >>> len(2@d6)
    11

    ```

    The [``counts`` method][dyce.h.H.counts] can be used to compute the total number of
    combinations and each outcome’s probability:

    ```python
    >>> from fractions import Fraction
    >>> total = sum((2@d6).counts()) ; total
    36
    >>> [(outcome, Fraction(count, total)) for outcome, count in (2@d6).items()]
    [(2, Fraction(1, 36)), (3, Fraction(1, 18)), (4, Fraction(1, 12)), (5, Fraction(1, 9)), (6, Fraction(5, 36)), (7, Fraction(1, 6)), ..., (12, Fraction(1, 36))]

    ```

    Histograms provide common comparators (e.g., [``eq``][dyce.h.H.eq]
    [``ne``][dyce.h.H.ne], etc.). One way to count how often a first six-sided die
    shows a different face than a second is:

    ```python
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

    ```python
    >>> d6.lt(d6)
    H({False: 21, True: 15})
    >>> print(d6.lt(d6).format(width=65))
    avg |    0.42
    std |    0.49
    var |    0.24
      0 |  58.33% |#############################
      1 |  41.67% |####################

    ```

    Or how often at least one ``2`` will show when rolling four six-sided dice:

    ```python
    >>> d6_eq2 = d6.eq(2); d6_eq2  # how often a 2 shows on a single six-sided die
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
        is most often an issue with the ``@`` operator, because it behaves differently
        than the ``d`` operator in most dedicated grammars. More specifically, in
        Python, ``@`` has a [lower
        precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence)
        than ``.`` and ``[…]``:

        ```python
        >>> 2@d6[7]  # type: ignore
        Traceback (most recent call last):
          ...
        KeyError: 7
        >>> 2@d6.le(7)  # probably not what was intended
        H({2: 36})
        >>> 2@d6.le(7) == 2@(d6.le(7))
        True

        ```

        ```python
        >>> (2@d6)[7]
        6
        >>> (2@d6).le(7)
        H({False: 15, True: 21})
        >>> 2@d6.le(7) == (2@d6).le(7)
        False

        ```

    Counts are generally accumulated without reduction. To reduce, call the
    [``lowest_terms`` method][dyce.h.H.lowest_terms]:

    ```python
    >>> d6.ge(4)
    H({False: 3, True: 3})
    >>> d6.ge(4).lowest_terms()
    H({False: 1, True: 1})

    ```

    Testing equivalence implicitly performs reductions of operands:

    ```python
    >>> d6.accumulate(d6) == d6.accumulate(d6).accumulate(d6)
    True

    ```
    """

    # ---- Initializer -----------------------------------------------------------------

    def __init__(self, items: _SourceT) -> None:
        r"Initializer."
        super().__init__()
        self._simple_init: Optional[int] = None
        tmp: Counter[OutcomeP] = counter()

        if isinstance(items, SupportsInt):
            if items != 0:
                self._simple_init = as_int(items)
                outcome_range = range(
                    self._simple_init,
                    0,
                    1 if self._simple_init < 0 else -1,  # count toward zero
                )

                if isinstance(items, OutcomeP):
                    outcome_type = type(items)
                    tmp.update({outcome_type(i): 1 for i in outcome_range})
                else:
                    tmp.update({i: 1 for i in outcome_range})
        elif isinstance(items, HAbleT):
            tmp.update(items.h())
        elif isinstance(items, ABCMapping):
            tmp.update(items)
        elif isinstance(items, ABCIterable):
            # Items is either an Iterable[OutcomeP] or an Iterable[Tuple[OutcomeP,
            # SupportsInt]] (although this technically supports Iterable[Union[OutcomeP,
            # Tuple[OutcomeP, SupportsInt]]])
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
        try:
            tmp_keys: Iterable[OutcomeP] = sorted(tmp)
        except TypeError:
            # This is for outcomes that don't support direct comparisons, like symbolic
            # representations
            tmp_keys = sorted(tmp, key=str)

        self._h: _MappingT = {
            outcome: tmp[outcome] for outcome in tmp_keys if tmp[outcome] != 0
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
            return op_eq(self, other.h())
        elif isinstance(other, H):
            return op_eq(self.lowest_terms()._h, other.lowest_terms()._h)
        else:
            return super().__eq__(other)

    def __ne__(self, other) -> bool:
        if isinstance(other, HAbleT):
            return op_ne(self, other.h())
        elif isinstance(other, H):
            return not op_eq(self, other)
        else:
            return super().__ne__(other)

    def __hash__(self) -> int:
        return hash(frozenset(self._lowest_terms()))

    def __len__(self) -> int:
        return len(self._h)

    def __getitem__(self, key: OutcomeP) -> int:
        return op_getitem(self._h, key)

    def __iter__(self) -> Iterator[OutcomeP]:
        return iter(self._h)

    def __add__(self, other: _OperandT) -> "H":
        try:
            if self and not other:
                return self.map(op_add, 0)
            elif not self and isinstance(other, (H, HAbleT)):
                return op_add(0, other.h() if isinstance(other, HAbleT) else other)
            else:
                return self.map(op_add, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_add, other)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: _OperandT) -> "H":
        try:
            if self and not other:
                return self.map(op_sub, 0)
            elif not self and isinstance(other, (H, HAbleT)):
                return op_sub(0, other.h() if isinstance(other, HAbleT) else other)
            else:
                return self.map(op_sub, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_sub, other)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: _OperandT) -> "H":
        try:
            return self.map(op_mul, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_mul, other)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: SupportsInt) -> "H":
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return sum(repeat(self, other), start=H({}))

    def __rmatmul__(self, other: SupportsInt) -> "H":
        return self.__matmul__(other)

    def __truediv__(self, other: _OperandT) -> "H":
        try:
            return self.map(op_truediv, other)
        except NotImplementedError:
            return NotImplemented

    def __rtruediv__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_truediv, other)
        except NotImplementedError:
            return NotImplemented

    def __floordiv__(self, other: _OperandT) -> "H":
        try:
            return self.map(op_floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_floordiv, other)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: _OperandT) -> "H":
        try:
            return self.map(op_mod, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_mod, other)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: _OperandT) -> "H":
        try:
            return self.map(op_pow, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OutcomeP) -> "H":
        try:
            return self.rmap(op_pow, other)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: Union[SupportsInt, "H", "HAbleT"]) -> "H":
        try:
            if not isinstance(other, (H, HAbleT)):
                other = as_int(other)

            return self.map(op_and, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __rand__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(op_and, as_int(other))
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __xor__(self, other: Union[SupportsInt, "H", "HAbleT"]) -> "H":
        try:
            if not isinstance(other, (H, HAbleT)):
                other = as_int(other)

            return self.map(op_xor, other)
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(op_xor, as_int(other))
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __or__(self, other: Union[SupportsInt, "H", "HAbleT"]) -> "H":
        try:
            if not isinstance(other, (H, HAbleT)):
                other = as_int(other)

            return self.map(op_or, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __ror__(self, other: SupportsInt) -> "H":
        try:
            return self.rmap(op_or, as_int(other))
        except (NotImplementedError, TypeError):
            return NotImplemented

    def __neg__(self) -> "H":
        return self.umap(op_neg)

    def __pos__(self) -> "H":
        return self.umap(op_pos)

    def __abs__(self) -> "H":
        return self.umap(op_abs)

    def __invert__(self) -> "H":
        return self.umap(op_invert)

    def counts(self) -> ValuesView[int]:
        r"""
        More descriptive synonym for the [``values`` method][dyce.h.H.values].
        """
        return self.values()

    def items(self):
        return self._h.items()

    def keys(self):
        return self._h.keys()

    def outcomes(self) -> KeysView[OutcomeP]:
        r"""
        More descriptive synonym for the [``keys`` method][dyce.h.H.keys].
        """
        return self.keys()

    def values(self):
        return self._h.values()

    # ---- Methods ---------------------------------------------------------------------

    def map(self, oper: _BinaryOperatorT, other: _OperandT) -> "H":
        r"""
        Applies *oper* to each outcome of the histogram paired with *other*. Shorthands
        exist for many arithmetic operators and comparators.

        ```python
        >>> import operator
        >>> d6 = H(6)
        >>> d6.map(operator.add, d6)
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
        >>> d6.map(operator.add, d6) == d6 + d6
        True

        ```

        ```python
        >>> d6.map(operator.mul, -1)
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})
        >>> d6.map(operator.mul, -1) == d6 * -1
        True

        ```

        ```python
        >>> d6.map(operator.gt, 3)
        H({False: 3, True: 3})
        >>> d6.map(operator.gt, 3) == d6.gt(3)
        True

        ```
        """
        if isinstance(other, HAbleT):
            other = other.h()

        if isinstance(other, H):
            return H((oper(s, o), self[s] * other[o]) for s, o in product(self, other))
        else:
            return H((oper(outcome, other), count) for outcome, count in self.items())

    def rmap(self, oper: _BinaryOperatorT, other: OutcomeP) -> "H":
        return H((oper(other, outcome), count) for outcome, count in self.items())

    def umap(self, oper: _UnaryOperatorT) -> "H":
        r"""
        Applies *oper* to each outcome of the histogram:

        ```python
        >>> H(6).umap(lambda outcome: outcome * -1)
        H(-6)

        ```

        ```python
        >>> H(4).umap(lambda outcome: (-outcome) ** outcome)
        H({-27: 1, -1: 1, 4: 1, 256: 1})

        ```
        """
        h = H((oper(outcome), count) for outcome, count in self.items())

        if self._simple_init is not None:
            h_simple = H(oper(self._simple_init))

            if h_simple == h:
                return h_simple

        return h

    def lt(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.lt, other)``:

        ```python
        >>> H(6).lt(3)
        H({False: 4, True: 2})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_lt, other)

    def le(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.le, other)``.

        ```python
        >>> H(6).le(3)
        H({False: 3, True: 3})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_le, other)

    def eq(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.eq, other)``.

        ```python
        >>> H(6).eq(3)
        H({False: 5, True: 1})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_eq, other)

    def ne(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.ne, other)``.

        ```python
        >>> H(6).ne(3)
        H({False: 1, True: 5})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_ne, other)

    def gt(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.gt, other)``.

        ```python
        >>> H(6).gt(3)
        H({False: 3, True: 3})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_gt, other)

    def ge(self, other: _OperandT) -> "H":
        r"""
        Shorthand for ``self.map(operator.ge, other)``.

        ```python
        >>> H(6).ge(3)
        H({False: 2, True: 4})

        ```

        See the [``map`` method][dyce.h.H.map].
        """
        return self.map(op_ge, other)

    def even(self) -> "H":
        r"""
        Equivalent to ``self.umap(lambda outcome: outcome % 2 == 0)``.

        ```python
        >>> H((-4, -2, 0, 1, 2, 3)).even()
        H({False: 2, True: 4})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """

        def is_even(outcome: SupportsInt) -> bool:
            return as_int(outcome) % 2 == 0

        return self.umap(is_even)

    def odd(self) -> "H":
        r"""
        Equivalent to ``self.umap(lambda outcome: outcome % 2 != 0)``.

        ```python
        >>> H((-4, -2, 0, 1, 2, 3)).odd()
        H({False: 4, True: 2})

        ```

        See the [``umap`` method][dyce.h.H.umap].
        """

        def is_odd(outcome: SupportsInt) -> bool:
            return as_int(outcome) % 2 != 0

        return self.umap(is_odd)

    def accumulate(self, other: _SourceT) -> "H":
        r"""
        Accumulates counts:

        ```python
        >>> H(4).accumulate(H(6))
        H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})

        ```
        """
        if isinstance(other, ABCMapping):
            other = other.items()
        elif not isinstance(other, ABCIterable):
            other = cast(Iterable[OutcomeP], (other,))

        return H(chain(self.items(), cast(Iterable, other)))

    @experimental
    def exactly_k_times_in_n(
        self,
        outcome: OutcomeP,
        n: SupportsInt,
        k: SupportsInt,
    ) -> int:
        """
        !!! warning "Experimental"

            This method should be considered experimental and may disappear in future
            versions.

        Computes and returns the probability distribution where *outcome* appears
        exactly *k* times among ``n@self``.

        ```python
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
        c_total = sum(self.counts())

        return comb(n, k) * c_outcome ** k * (c_total - c_outcome) ** (n - k)

    def explode(self, max_depth: SupportsInt = 1) -> "H":
        r"""
        Shorthand for ``self.substitute(lambda h, outcome: h if outcome == max(h) else
        outcome, operator.add, max_depth)``.

        ```python
        >>> H(6).explode(max_depth=2)
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})

        ```

        See the [``substitute`` method][dyce.h.H.substitute].
        """
        return self.substitute(
            lambda h, outcome: h if outcome == max(h) else outcome,
            op_add,
            max_depth,
        )

    def lowest_terms(self) -> "H":
        r"""
        Computes and returns a histogram whose counts share a greatest common divisor of 1.

        ```python
        >>> df = H((-1, -1, 0, 0, 1, 1)); df
        H({-1: 2, 0: 2, 1: 2})
        >>> df.lowest_terms()
        H({-1: 1, 0: 1, 1: 1})

        ```

        ```python
        >>> d6avg = H((2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5)) ; d6avg
        H({2: 2, 3: 4, 4: 4, 5: 2})
        >>> d6avg.lowest_terms()
        H({2: 1, 3: 2, 4: 2, 5: 1})

        ```
        """
        return H(self._lowest_terms())

    @experimental
    def order_stat_for_n_at_pos(self, n: SupportsInt, pos: SupportsInt) -> "H":
        """
        !!! warning "Experimental"

            This method should be considered experimental and may disappear in future
            versions.

        Shorthand for ``self.order_stat_func_for_n(n)(pos)``.
        """
        return self.order_stat_func_for_n(n)(pos)

    @experimental
    def order_stat_func_for_n(self, n: SupportsInt) -> Callable[[SupportsInt], "H"]:
        """
        !!! warning "Experimental"

            This method should be considered experimental and may disappear in future
            versions.

        Returns a function that takes a single argument (*pos*) and computes the
        probability distribution for each outcome appearing in that position among
        ``n@self``.

        ```python
        >>> d6avg = H((2, 3, 3, 4, 4, 5))
        >>> order_stat_for_5d6avg = d6avg.order_stat_func_for_n(5)
        >>> order_stat_for_5d6avg(3)  # counts where outcome appears at index 3
        H({2: 26, 3: 1432, 4: 4792, 5: 1526})

        ```

        The results show that, when rolling five six-sided “averaging” dice and sorting
        each roll, there are 26 ways where ``2`` appears at the fourth (index ``3``)
        position, 1432 ways where ``3`` appears at the fourth position, etc. This can be
        verified independently using the computationally expensive method of enumerating
        rolls and counting those that meet the criteria:

        ```python
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
        computed much faster:

        ```python
        In [2]: %timeit [H(6).order_stat_for_n_at_pos(100, i) for i in range(10)]
        1.61 s ± 31.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

        In [3]: %%timeit
           ...: order_stat_for_100d6_at_pos = H(6).order_stat_func_for_n(100)
           ...: [order_stat_for_100d6_at_pos(i) for i in range(10)]
        170 ms ± 3.41 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
        ```
        """
        betas_by_outcome: Dict[OutcomeP, Tuple[H, H]] = {}

        for outcome in self.outcomes():
            betas_by_outcome[outcome] = (
                n @ self.le(outcome),
                n @ self.lt(outcome),
            )

        def _gen_h_items_at_pos(pos: int) -> Iterator[Tuple[OutcomeP, int]]:
            for outcome, (h_le, h_lt) in betas_by_outcome.items():
                yield (
                    outcome,
                    h_le.gt(pos).get(True, 0) - h_lt.gt(pos).get(True, 0),
                )

        def order_stat_for_n_at_pos(pos: SupportsInt) -> H:
            return H(_gen_h_items_at_pos(as_int(pos)))

        return order_stat_for_n_at_pos

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: _CoalesceT = None,
        max_depth: SupportsInt = 1,
    ) -> "H":
        r"""
        Calls *expand* on each outcome, recursively up to *max_depth* times. If *expand*
        returns a number, it replaces the outcome. If it returns an [``H``
        object][dyce.h.H], *coalesce* is called on the outcome and the expanded
        histogram, and the returned histogram is folded into result. The default
        behavior for *coalesce* is to replace the outcome with the expanded histogram.
        Returned histograms are always reduced to their lowest terms. (See the
        [``lowest_terms`` method][dyce.h.H.lowest_terms].)

        This can be used to model complex rules. The following models re-rolling a face
        of 1 on the first roll:

        ```python
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
        original histogram and the substitution:

        ```python
        >>> orig = H({1: 1, 2: 2, 3: 3, 4: 4})
        >>> sub = orig.substitute(lambda h, outcome: -h if outcome == 4 else outcome) ; sub
        H({-4: 8, -3: 6, -2: 4, -1: 2, 1: 5, 2: 10, 3: 15})
        >>> sum(count for outcome, count in orig.items() if outcome == 4) / sum(orig.counts())
        0.4
        >>> sum(count for outcome, count in sub.items() if outcome < 0) / sum(sub.counts())
        0.4

        ```

        !!! tip "An important exception"

            If *coalesce* returns the empty histogram (``H({})``), the corresponding
            outcome and its counts are omitted from the result without substitution or
            scaling. A silly example is modeling a d5 by indefinitely re-rolling a d6
            until something other than a 6 comes up:

            ```python
            >>> H(6).substitute(lambda h, outcome: H({}) if outcome == 6 else outcome)
            H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

            ```

            This technique is more useful when modeling re-rolling certain derived
            outcomes, like ties in a contest:

            ```python
            >>> d6_3, d8_2 = 3@H(6), 2@H(8)
            >>> d6_3.vs(d8_2)
            H({-1: 4553, 0: 1153, 1: 8118})
            >>> d6_3.vs(d8_2).substitute(lambda h, outcome: H({}) if outcome == 0 else outcome)
            H({-1: 4553, 1: 8118})

            ```

        Because it delegates to a callback for refereeing substitution decisions,
        ``substitute`` is quite flexible and well suited to modeling (or at least
        approximating) logical progressions. Consider the following rules:

          1. Start with a total of zero.
          2. Roll a six-sided die. Add the face to the total. If the face was a six, go
             to step 3. Otherwise stop.
          3. Roll a four-sided die. Add the face to the total. If the face was a four,
             go to step 2. Otherwise stop.

        What is the likelihood of an even final tally? This can be approximated by:

        ```python
        >>> d4, d6 = H(4), H(6)

        >>> def reroll_greatest_on_d4_d6(h: H, outcome):
        ...   if outcome == max(h):
        ...     if h == d6: return d4
        ...     if h == d4: return d6
        ...   return outcome

        >>> import operator
        >>> h = d6.substitute(reroll_greatest_on_d4_d6, operator.add, max_depth=6)
        >>> h_even = h.even()
        >>> print("{:.3%}".format(h_even[1] / sum(h_even.counts())))
        39.131%

        ```

        Surprised? Because both six and four are even numbers, the only way we keep
        rolling is if the total is even. You might think this would lead to evens being
        *more* likely. However, we only care about the final tally and the rules direct
        us to re-roll certain evens (nudging us toward an odd number more often than
        not).

        We can also use this method to model expected damage from a single attack in
        d20-like role playing games:

        ```python
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

        if coalesce is None:
            coalesce = _coalesce_replace

        def _substitute(h: H, depth: int = 0) -> H:
            assert coalesce is not None

            if depth == max_depth:
                return h

            total_scalar = 1
            items_for_reassembly: List[Tuple[OutcomeP, int, int]] = []

            for outcome, count in h.items():
                expanded = expand(h, outcome)

                if isinstance(expanded, H):
                    # Keep expanding deeper, if we can
                    expanded = _substitute(expanded, depth + 1)
                    # Coalesce the result
                    expanded = coalesce(expanded, outcome)
                    # Account for the impact of expansion on peers
                    expanded_scalar = sum(expanded.counts())

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

    def vs(self, other: _OperandT) -> "H":
        r"""
        Compares this histogram with *other*. -1 represents where *other* is greater. 0
        represents where they are equal. 1 represents where *other* is less.

        Shorthand for ``self.within(0, 0, other)``.

        ```python
        >>> H(6).vs(H(4))
        H({-1: 6, 0: 4, 1: 14})
        >>> H(6).vs(H(4)) == H(6).within(0, 0, H(4))
        True

        ```

        See the [``within`` method][dyce.h.H.within].
        """
        return self.within(0, 0, other)

    def within(self, lo: OutcomeP, hi: OutcomeP, other: _OperandT = 0) -> "H":
        r"""
        Computes the difference between this histogram and *other*. -1 represents where that
        difference is less than *lo*. 0 represents where that difference between *lo*
        and *hi* (inclusive). 1 represents where that difference is greater than *hi*.

        ```python
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

        ```python
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

    def distribution(
        self,
        fill_items: _MappingT = None,
    ) -> Iterator[Tuple[OutcomeP, float]]:
        r"""
        Presentation helper function returning an iterator for each outcome/count or
        outcome/probability pair:

        ```python
        >>> list(H(6).gt(3).distribution())
        [(False, 0.5), (True, 0.5)]

        ```

        If provided, *fill_items* supplies defaults for any “missing” outcomes:

        ```python
        >>> list(H(6).gt(7).distribution())
        [(False, 1.0)]
        >>> list(H(6).gt(7).distribution(fill_items={True: 0, False: 0}))
        [(False, 1.0), (True, 0.0)]

        ```
        """
        if fill_items is None:
            fill_items = {}

        combined = dict(chain(fill_items.items(), self.items()))
        total = sum(combined.values()) or 1

        return ((outcome, count / total) for outcome, count in sorted(combined.items()))

    def distribution_xy(
        self,
        fill_items: _MappingT = None,
    ) -> Tuple[Tuple[OutcomeP, ...], Tuple[float, ...]]:
        r"""
        Presentation helper function returning an iterator for a “zipped” arrangement of the
        output from the [``distribution`` method][dyce.h.H.distribution]:

        ```python
        >>> list(H(6).distribution())
        [(1, 0.16666666), (2, 0.16666666), (3, 0.16666666), (4, 0.16666666), (5, 0.16666666), (6, 0.16666666)]
        >>> H(6).distribution_xy()
        ((1, 2, 3, 4, 5, 6), (0.16666666, 0.16666666, 0.16666666, 0.16666666, 0.16666666, 0.16666666))

        ```
        """
        return cast(
            Tuple[Tuple[int, ...], Tuple[float, ...]],
            tuple(zip(*self.distribution(fill_items))),
        )

    def format(
        self,
        fill_items: _MappingT = None,
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

        ```python
        >>> print(H(6).format(width=0))
        {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}

        ```

        ```python
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

        If *scaled* is ``True``, horizontal bars are scaled to *width*:

        ```python
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
            mu: Union[float, OutcomeP] = float(self.mean())
        except TypeError:
            mu = self.mean()

        if width <= 0:

            def parts():
                yield f"avg: {mu:.2f}"

                for outcome, probability in self.distribution(fill_items):
                    probability_f = float(probability)
                    yield f"{outcome}:{probability_f:7.2%}"

            return "{" + ", ".join(parts()) + "}"
        else:
            w = width - 15

            def lines():
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

    def mean(self) -> Union[float, OutcomeP]:
        """
        Returns the mean of the weighted outcomes (or 0.0 if there are no outcomes).
        """
        numerator = denominator = 0

        for outcome, count in self.items():
            numerator += outcome * count
            denominator += count

        return numerator / (denominator or 1)

    def stdev(self, mu: Union[float, OutcomeP] = None) -> Union[float, OutcomeP]:
        """
        Shorthand for ``math.sqrt(self.variance(mu))``.
        """
        return sqrt(self.variance(mu))

    def variance(self, mu: Union[float, OutcomeP] = None) -> Union[float, OutcomeP]:
        """
        Returns the variance of the weighted outcomes. If provided, *mu* is used as the mean
        (to avoid duplicate computation).
        """
        mu = mu if mu else self.mean()
        numerator = denominator = 0

        for outcome, count in self.items():
            numerator += (outcome - mu) ** 2 * count
            denominator += count

        return numerator / (denominator or 1)

    def roll(self) -> OutcomeP:
        r"""
        Returns a (weighted) random outcome.
        """
        if not self:
            return 0

        return choices(*self.distribution_xy())[0]

    def _lowest_terms(self) -> Iterable[Tuple[OutcomeP, int]]:
        counts_gcd = gcd(*self.counts())

        return ((k, v // counts_gcd) for k, v in self.items())


@runtime_checkable
class HAbleT(Protocol):
    r"""
    A protocol whose implementer can be expressed as (or reduced to) an
    [``H`` object][dyce.h.H] by calling its [``h`` method][dyce.h.HAbleT.h]. Currently,
    only the [``P`` class][dyce.p.P] implements this protocol, but this affords an
    integration point for ``dyce`` users.
    """

    def h(self) -> H:
        r"""
        Express its implementer as an [``H`` object][dyce.h.H].
        """
        ...


class HAbleBinOpsMixin:
    r"""
    A “mix-in” class providing arithmetic operations for implementers of the
    [``HAbleT`` protocol][dyce.h.HAbleT]. The [``P`` class][dyce.p.P] derives from this
    class.
    """

    def __add__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.add(self.h(), other)``.
        """
        return op_add(self.h(), other)

    def __radd__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.add(other, self.h())``.
        """
        return op_add(other, self.h())

    def __sub__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.sub(self.h(), other)``.
        """
        return op_sub(self.h(), other)

    def __rsub__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.sub(other, self.h())``.
        """
        return op_sub(other, self.h())

    def __mul__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.mul(self.h(), other)``.
        """
        return op_mul(self.h(), other)

    def __rmul__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.mul(other, self.h())``.
        """
        return op_mul(other, self.h())

    def __truediv__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.truediv(self.h(), other)``.
        """
        return op_truediv(self.h(), other)

    def __rtruediv__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.truediv(other, self.h())``.
        """
        return op_truediv(other, self.h())

    def __floordiv__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.floordiv(self.h(), other)``.
        """
        return op_floordiv(self.h(), other)

    def __rfloordiv__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.floordiv(other, self.h())``.
        """
        return op_floordiv(other, self.h())

    def __mod__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.mod(self.h(), other)``.
        """
        return op_mod(self.h(), other)

    def __rmod__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.mod(other, self.h())``.
        """
        return op_mod(other, self.h())

    def __pow__(self: HAbleT, other: _OperandT) -> H:
        r"""
        Shorthand for ``operator.pow(self.h(), other)``.
        """
        return op_pow(self.h(), other)

    def __rpow__(self: HAbleT, other: OutcomeP) -> H:
        r"""
        Shorthand for ``operator.pow(other, self.h())``.
        """
        return op_pow(other, self.h())

    def __and__(self: HAbleT, other: Union[SupportsInt, H, HAbleT]) -> H:
        r"""
        Shorthand for ``operator.and_(self.h(), other)``.
        """
        return op_and(self.h(), other)

    def __rand__(self: HAbleT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``operator.and_(other, self.h())``.
        """
        return op_and(other, self.h())

    def __xor__(self: HAbleT, other: Union[SupportsInt, H, HAbleT]) -> H:
        r"""
        Shorthand for ``operator.xor(self.h(), other)``.
        """
        return op_xor(self.h(), other)

    def __rxor__(self: HAbleT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``operator.xor(other, self.h())``.
        """
        return op_xor(other, self.h())

    def __or__(self: HAbleT, other: Union[SupportsInt, H, HAbleT]) -> H:
        r"""
        Shorthand for ``operator.or_(self.h(), other)``.
        """
        return op_or(self.h(), other)

    def __ror__(self: HAbleT, other: SupportsInt) -> H:
        r"""
        Shorthand for ``operator.or_(other, self.h())``.
        """
        return op_or(other, self.h())


# ---- Functions -----------------------------------------------------------------------


def _coalesce_replace(h: H, outcome: OutcomeP) -> H:  # pylint: disable=unused-argument
    return h


def _within(lo: OutcomeP, hi: OutcomeP) -> _BinaryOperatorT:
    if lo > hi:
        raise ValueError(f"lower bound ({lo}) is greater than upper bound ({hi})")

    def _cmp(a: OutcomeP, b: OutcomeP) -> int:
        # This approach will probably not work with most symbolic outcomes
        diff = a - b

        return bool(diff > hi) - bool(diff < lo)

    setattr(_cmp, "lo", lo)
    setattr(_cmp, "hi", hi)

    return _cmp

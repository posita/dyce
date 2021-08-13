# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from collections import Counter as counter
from collections import defaultdict
from fractions import Fraction
from functools import reduce, wraps
from itertools import chain, combinations_with_replacement, groupby, product, repeat
from math import factorial
from operator import __eq__, __index__, __mul__, __ne__, __neg__, __pos__
from typing import (
    Callable,
    Counter,
    DefaultDict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    overload,
)

from .h import H, HAbleOpsMixin, _BinaryOperatorT, _MappingT, _UnaryOperatorT
from .lifecycle import deprecated, experimental
from .symmetries import sum_w_start
from .types import (
    IndexT,
    IntT,
    OutcomeT,
    _GetItemT,
    _IntCs,
    as_int,
    getitems,
    sorted_outcomes,
)

__all__ = ("P",)


# ---- Types ---------------------------------------------------------------------------


_OperandT = Union["P", OutcomeT]
_RollT = Tuple[OutcomeT, ...]
_RollCountT = Tuple[_RollT, int]


# ---- Classes -------------------------------------------------------------------------


class P(Sequence[H], HAbleOpsMixin):
    r"""
    An immutable pool (ordered sequence) supporting group operations for zero or more
    [``H`` objects][dyce.h.H] (provided or created from the
    [initializer][dyce.p.P.__init__]’s *args* parameter).

    ``` python
    >>> from dyce import P
    >>> p_d6 = P(6) ; p_d6  # shorthand for P(H(6))
    P(6)
    >>> -p_d6
    P(-6)

    ```

    ``` python
    >>> P(p_d6, p_d6)  # 2d6
    P(6, 6)
    >>> 2@p_d6  # also 2d6
    P(6, 6)
    >>> 2@(2@p_d6) == 4@p_d6
    True

    ```

    ``` python
    >>> p = P(4, P(6, P(8, P(10, P(12, P(20)))))) ; p
    P(4, 6, 8, 10, 12, 20)
    >>> sum(p.roll()) in p.h()
    True

    ```

    This class implements the [``HAbleT`` protocol][dyce.h.HAbleT] and derives from the
    [``HAbleOpsMixin`` class][dyce.h.HAbleOpsMixin], which means it can be
    “flattened” into a single histogram, either explicitly via the
    [``h`` method][dyce.p.P.h], or implicitly by using arithmetic operations.

    ``` python
    >>> p_d6 + p_d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    ```

    ``` python
    >>> 2 * P(8) - 1
    H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})

    ```

    To perform arithmetic on individual [``H`` objects][dyce.h.H] in a pool without
    flattening, use the [``map``][dyce.p.P.map], [``rmap``][dyce.p.P.rmap], and
    [``umap``][dyce.p.P.umap] methods.

    ```
    >>> import operator
    >>> P(4, 6, 8).umap(operator.__neg__)
    P(-8, -6, -4)

    ```

    ``` python
    >>> P(4, 6).map(operator.__pow__, 2)
    P(H({1: 1, 4: 1, 9: 1, 16: 1}), H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1}))

    ```

    ``` python
    >>> P(4, 6).rmap(2, operator.__pow__)
    P(H({2: 1, 4: 1, 8: 1, 16: 1}), H({2: 1, 4: 1, 8: 1, 16: 1, 32: 1, 64: 1}))

    ```

    Comparisons with [``H`` objects][dyce.h.H] work as expected.

    ``` python
    >>> from dyce import H
    >>> 3@p_d6 == H(6) + H(6) + H(6)
    True

    ```

    Indexing selects a contained histogram.

    ``` python
    >>> P(4, 6, 8)[0]
    H(4)

    ```

    Note that pools are opinionated about ordering.

    ``` python
    >>> P(8, 6, 4)
    P(4, 6, 8)
    >>> P(8, 6, 4)[0] == P(8, 4, 6)[0] == H(4)
    True

    ```

    In an extension to (departure from) the [``HAbleT`` protocol][dyce.h.HAbleT], the
    [``h`` method][dyce.p.P.h]’s implementation also affords subsets of outcomes to be
    “taken” (selected) by passing in selection criteria. Values are indexed from least
    to greatest. Negative indexes are supported and retain their idiomatic meaning.
    Modeling the sum of the greatest two faces of three six-sided dice (``3d6``) can be
    expressed as:

    ``` python
    >>> p_3d6 = 3@p_d6
    >>> p_3d6.h(-2, -1)
    H({2: 1, 3: 3, 4: 7, 5: 12, 6: 19, 7: 27, 8: 34, 9: 36, 10: 34, 11: 27, 12: 16})
    >>> print(p_3d6.h(-2, -1).format(width=65))
    avg |    8.46
    std |    2.21
    var |    4.91
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

    ```
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(self, *args: Union[IntT, P, H]) -> None:
        r"Initializer."
        super().__init__()

        def _gen_hs() -> Iterator[H]:
            for a in args:
                if isinstance(a, H):
                    yield a
                elif isinstance(a, P):
                    for h in a._hs:
                        yield h
                elif isinstance(a, _IntCs):
                    yield H(a)
                else:
                    raise ValueError(f"unrecognized initializer {args}")

        hs = list(h for h in _gen_hs() if h)

        try:
            hs.sort(key=lambda h: tuple(h.items()))
        except TypeError:
            # This is for outcomes that don't support direct comparisons, like symbolic
            # representations
            hs.sort(key=lambda h: str(tuple(h.items())))

        self._hs = tuple(hs)
        self._is_homogeneous = len(set(self._hs)) <= 1

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _parts() -> Iterator[str]:
            for h in self:
                yield (str(h._simple_init) if h._simple_init is not None else repr(h))

        args = ", ".join(_parts())

        return f"{self.__class__.__name__}({args})"

    def __eq__(self, other) -> bool:
        if isinstance(other, P):
            return __eq__(self._hs, other._hs)
        else:
            return NotImplemented

    def __ne__(self, other) -> bool:
        if isinstance(other, P):
            return __ne__(self._hs, other._hs)
        else:
            return NotImplemented

    def __len__(self) -> int:
        return len(self._hs)

    @overload
    def __getitem__(self, key: IndexT) -> H:
        ...

    @overload
    def __getitem__(self, key: slice) -> P:
        ...

    def __getitem__(self, key: _GetItemT) -> Union[H, P]:
        if isinstance(key, slice):
            return P(*self._hs[key])
        else:
            return self._hs[__index__(key)]

    def __iter__(self) -> Iterator[H]:
        return iter(self._hs)

    def __matmul__(self, other: IntT) -> P:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return P(*chain.from_iterable(repeat(self, other)))

    def __rmatmul__(self, other: IntT) -> P:
        return self.__matmul__(other)

    @deprecated
    def __neg__(self) -> P:  # type: ignore
        r"""
        !!! warning "Deprecated"

            This overridden method is deprecated and will likely be removed in the next
            major release. Use [``P.umap(__neg__)``][dyce.p.P.umap] instead.
        """
        return self.umap(__neg__)

    @deprecated
    def __pos__(self) -> P:  # type: ignore
        r"""
        !!! warning "Deprecated"

            This overridden method is deprecated and will likely be removed in the next
            major release. Use [``P.umap(__pos__)``][dyce.p.P.umap] instead.
        """
        return self.umap(__pos__)

    def h(self, *which: _GetItemT) -> H:
        r"""
        Roughly equivalent to ``#!python H((sum(roll), count) for roll, count in
        self.rolls_with_counts(*which))`` with some short-circuit optimizations.

        When provided no arguments, ``#!python h`` combines (or “flattens”) contained
        histograms in accordance with the [``HAbleT`` protocol][dyce.h.HAbleT].

        ``` python
        >>> (2@P(6)).h()
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        ```

        If one or more arguments are provided, this method sums subsets of outcomes
        those arguments identify for each roll. Outcomes are ordered from least (index
        ``#!python 0``) to greatest (index ``#!python -1`` or ``#!python len(self) -
        1``). Identifiers can be ``#!python int``s or ``#!python slice``s, and can be
        mixed.

        Taking the greatest of two six-sided dice can be modeled as:

        ``` python
        >>> p_2d6 = 2@P(6)
        >>> p_2d6.h(-1)
        H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
        >>> print(p_2d6.h(-1).format(width=65))
        avg |    4.47
        std |    1.40
        var |    1.97
          1 |   2.78% |#
          2 |   8.33% |####
          3 |  13.89% |######
          4 |  19.44% |#########
          5 |  25.00% |############
          6 |  30.56% |###############

        ```

        Taking the greatest two and least two faces of ten four-sided dice (``10d4``)
        can be modeled as:

        ``` python
        >>> p_10d4 = 10@P(4)
        >>> p_10d4.h(slice(2), slice(-2, None))
        H({4: 1, 5: 10, 6: 1012, 7: 5030, 8: 51973, 9: 168760, 10: 595004, 11: 168760, 12: 51973, 13: 5030, 14: 1012, 15: 10, 16: 1})
        >>> print(p_10d4.h(slice(2), slice(-2, None)).format(width=65, scaled=True))
        avg |   10.00
        std |    0.91
        var |    0.84
          4 |   0.00% |
          5 |   0.00% |
          6 |   0.10% |
          7 |   0.48% |
          8 |   4.96% |####
          9 |  16.09% |##############
         10 |  56.74% |##################################################
         11 |  16.09% |##############
         12 |   4.96% |####
         13 |   0.48% |
         14 |   0.10% |
         15 |   0.00% |
         16 |   0.00% |

        ```

        Taking all outcomes exactly once is equivalent to summing the histograms in the
        pool.

        ``` python
        >>> d6 = H(6)
        >>> d6avg = H((2, 3, 3, 4, 4, 5))
        >>> p = 2@P(d6, d6avg)
        >>> p.h(slice(None)) == p.h() == d6 + d6 + d6avg + d6avg
        True

        ```
        """
        if which:
            n = len(self)
            i = _analyze_selection(n, which)

            if i and i >= n:
                # The caller selected all dice in the pool exactly i // n times, so we
                # can short-circuit roll enumeration
                assert i % n == 0

                return self.h() * (i // n)
            else:
                return H(
                    (sum(roll), count) for roll, count in self.rolls_with_counts(*which)
                )
        else:
            # The caller offered no selection
            return sum_w_start(self, start=H({}))

    # ---- Properties ------------------------------------------------------------------

    @property
    def is_homogeneous(self) -> bool:
        r"""
        !!! warning "Experimental"

            This property should be considered experimental and may change or disappear
            in future versions.

        A flag indicating whether the pool’s population of histograms is homogeneous.

        ``` python
        >>> P(6, 6).is_homogeneous
        True
        >>> P(4, 6, 8).is_homogeneous
        False

        ```
        """
        return self._is_homogeneous

    # ---- Methods ---------------------------------------------------------------------

    @experimental
    def appearances_in_rolls(self, outcome: OutcomeT) -> H:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may change or disappear in
            future versions. While it does provide a performance improvement over other
            techniques, it is not significant for most applications, and rarely
            justifies the corresponding reduction in readability.

        Returns a histogram where the outcomes (keys) are the number of times *outcome*
        appears, and the counts are the number of rolls where *outcome* appears
        precisely that number of times. Equivalent to ``#!python H((sum(1 for v in roll
        if v == outcome), count) for roll, count in self.rolls_with_counts())``, but
        much more efficient.

        ``` python
        >>> p_2d6 = P(6, 6)
        >>> list(p_2d6.rolls_with_counts())
        [((1, 1), 1), ((1, 2), 2), ((1, 3), 2), ((1, 4), 2), ((1, 5), 2), ((1, 6), 2), ...]
        >>> p_2d6.appearances_in_rolls(1)
        H({0: 25, 1: 10, 2: 1})

        ```

        ``` python
        >>> # Least efficient, by far
        >>> d4, d6 = H(4), H(6)
        >>> p_3d4_2d6 = P(d4, d4, d4, d6, d6)
        >>> H((sum(1 for v in roll if v == 3), count) for roll, count in p_3d4_2d6.rolls_with_counts())
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        ```

        ``` python
        >>> # Pretty darned efficient, generalizable to other boolean inquiries, and
        >>> # arguably the most readable
        >>> d4_eq3, d6_eq3 = d4.eq(2), d6.eq(2)
        >>> 3@d4_eq3 + 2@d6_eq3
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        ```

        ``` python
        >>> # Most efficient for large sets of dice
        >>> p_3d4_2d6.appearances_in_rolls(3)
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        ```

        Based on some rudimentary testing, this method appears to converge on being
        almost twice (about $\frac{7}{4}$) as efficient as the boolean accumulation
        technique for larger sets.

        ``` python
        In [3]: %timeit 3@d4_eq3 + 2@d6_eq3
        287 µs ± 6.96 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

        In [4]: %timeit P(3@P(4), 2@P(6)).appearances_in_rolls(3)
        402 µs ± 5.59 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

        In [5]: %timeit 9@d4_eq3 + 6@d6_eq3
        845 µs ± 7.89 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

        In [6]: %timeit P(9@P(4), 6@P(6)).appearances_in_rolls(3)
        597 µs ± 9.46 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

        In [7]: %timeit 90@d4_eq3 + 60@d6_eq3
        24.7 ms ± 380 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

        In [8]: %timeit P(90@P(4), 60@P(6)).appearances_in_rolls(3)
        7.5 ms ± 84.6 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

        In [9]: %timeit 900@d4_eq3 + 600@d6_eq3
        3.34 s ± 19.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

        In [10]: %timeit P(900@P(4), 600@P(6)).appearances_in_rolls(3)
        1.93 s ± 14.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
        ```
        """
        group_counters: List[Counter[OutcomeT]] = []

        for h, hs in groupby(self):
            group_counter: Counter[OutcomeT] = counter()
            n = sum(1 for _ in hs)

            for k in range(0, n + 1):
                group_counter[k] = h.exactly_k_times_in_n(outcome, n, k) * (
                    group_counter[k] if group_counter[k] else 1
                )

            group_counters.append(group_counter)

        return sum_w_start(
            (H(group_counter) for group_counter in group_counters), start=H({})
        )

    def roll(self) -> _RollT:
        r"""
        Returns (weighted) random outcomes from contained histograms.
        """
        return tuple(sorted_outcomes(h.roll() for h in self))

    def rolls_with_counts(self, *which: _GetItemT) -> Iterator[_RollCountT]:
        r"""
        Returns an iterator yielding 2-tuples (pairs) that, collectively, enumerate all
        possible outcomes for the pool. The first item in the 2-tuple is a sorted
        sequence of the outcomes for a distinct roll. The second is the count for that
        roll. Outcomes in each roll are ordered least to greatest.

        If one or more arguments are provided, this methods selects subsets of outcomes
        for each roll. Outcomes in each roll are ordered from least (index ``#!python
        0``) to greatest (index ``#!python -1`` or ``#!python len(self) - 1``).
        Identifiers can be ``#!python int``s or ``#!python slice``s, and can be mixed
        for more flexible selections.

        ``` python
        >>> from collections import Counter
        >>> def accumulate_roll_counts(counter, roll_counts):
        ...   for roll, count in roll_counts:
        ...     counter[roll] += count
        ...   return counter
        >>> p_6d6 = 6@P(6)
        >>> every_other_d6 = accumulate_roll_counts(Counter(), p_6d6.rolls_with_counts(slice(None, None, -2))) ; every_other_d6
        Counter({(6, 4, 2): 4110, (6, 5, 3): 3390, (6, 4, 3): 3330, ..., (3, 3, 3): 13, (2, 2, 2): 7, (1, 1, 1): 1})
        >>> accumulate_roll_counts(Counter(), p_6d6.rolls_with_counts(5, 3, 1)) == every_other_d6
        True
        >>> accumulate_roll_counts(Counter(), p_6d6.rolls_with_counts(*range(5, 0, -2))) == every_other_d6
        True
        >>> accumulate_roll_counts(Counter(), p_6d6.rolls_with_counts(*(i for i in range(6, 0, -1) if i % 2 == 1))) == every_other_d6
        True

        ```

        One way to model the likelihood of achieving a “Yhatzee” (i.e., where five
        six-sided dice show the same face) on a single roll by checking rolls for where
        the least and greatest outcomes are the same.

        ``` python
        >>> p_5d6 = 5@P(6)
        >>> yhatzee_on_single_roll = H(
        ...   (1 if roll[0] == roll[-1] else 0, count)
        ...   for roll, count
        ...   in p_5d6.rolls_with_counts()
        ... )
        >>> print(yhatzee_on_single_roll.format(width=0))
        {..., 0: 99.92%, 1:  0.08%}

        ```

        !!! note "In the general case, rolls may appear more than once."

        ``` python
        >>> list(P(H(2), H(3)).rolls_with_counts())
        [((1, 1), 1), ((1, 2), 1), ((1, 3), 1), ((1, 2), 1), ((2, 2), 1), ((2, 3), 1)]

        ```

        In the above, ``#!python (1, 2)`` appears a total of two times, each with counts
        of one.

        However, if the pool is homogeneous (meaning it only contains identical
        histograms), rolls (before selection) are not repeated. (See the note on
        implementation below.)

        ``` python
        >>> list((2@P(H((-1, 0, 1)))).rolls_with_counts())
        [((-1, -1), 1), ((-1, 0), 2), ((-1, 1), 2), ((0, 0), 1), ((0, 1), 2), ((1, 1), 1)]

        ```

        Either way, by summing and counting all rolls, we can confirm identity.

        ``` python
        >>> d6 = H(6)
        >>> d6avg = H((2, 3, 3, 4, 4, 5))
        >>> p = 2@P(d6, d6avg)
        >>> H((sum(roll), count) for roll, count in p.rolls_with_counts()) == p.h() == d6 + d6 + d6avg + d6avg
        True

        ```

        This method does not try to outsmart callers by (mis)interpreting selection
        arguments. It honors selection identifier order and any redundancy.

        ``` python
        >>> p_d3_d4 = P(H(3), H(4))
        >>> # Select the second, first, then second (again) elements
        >>> list(p_d3_d4.rolls_with_counts(-1, 0, 1))
        [((1, 1, 1), 1), ((2, 1, 2), 1), ((3, 1, 3), 1), ((4, 1, 4), 1), ..., ((3, 1, 3), 1), ((3, 2, 3), 1), ((3, 3, 3), 1), ((4, 3, 4), 1)]

        ```

        Selecting the same outcomes, but in a different order is not immediately
        comparable.

        ``` python
        >>> select_0_1 = list(p_d3_d4.rolls_with_counts(0, 1))
        >>> select_1_0 = list(p_d3_d4.rolls_with_counts(1, 0))
        >>> select_0_1 == select_1_0
        False

        ```

        Equivalence can be tested when selected outcomes are sorted.

        ``` python
        >>> sorted_0_1 = [(sorted(roll), count) for roll, count in select_0_1]
        >>> sorted_1_0 = [(sorted(roll), count) for roll, count in select_1_0]
        >>> sorted_0_1 == sorted_1_0
        True

        ```

        They can also be summed and counted which is equivalent to calling the
        [``h`` method][dyce.p.P.h] with identical selection arguments.

        ``` python
        >>> summed_0_1 = H((sum(roll), count) for roll, count in select_0_1)
        >>> summed_1_0 = H((sum(roll), count) for roll, count in select_1_0)
        >>> summed_0_1 == summed_1_0 == p_d3_d4.h(0, 1) == p_d3_d4.h(1, 0)
        True

        ```

        !!! info "About the implementation"

            Enumeration is substantially more efficient for homogeneous pools than
            heterogeneous ones, because we are able to avoid the expensive enumeration
            of the Cartesian product using several techniques.

            Taking $k$ outcomes, where $k$ selects fewer than all $n$ outcomes a
            homogeneous pool benefits from [Ilmari Karonen’s
            optimization](https://rpg.stackexchange.com/a/166663/71245), which appears
            to scale geometrically with $k$ times some factor of $n$ (e.g., $\log n$,
            but I haven’t bothered to figure that out yet), such that—in observed
            testing, at least—it is generally the fastest approach for $k < n$.

            Where $k = n$, we leverage the [*multinomial
            coefficient*](https://en.wikipedia.org/wiki/Permutation#Permutations_of_multisets),
            which appears to scale generally with $n$.

            $$
            {{n} \choose {{{k}_{1}},{{k}_{2}},\ldots,{{k}_{m}}}}
            = {\frac {{n}!} {{{k}_{1}}! {{k}_{2}}! \cdots {{k}_{m}}!}}
            $$

            We enumerate combinations with replacements, and then the compute the number
            of permutations with repetitions for each combination. Consider ``#!python
            n@P(H(m))``. Enumerating combinations with replacements would yield all
            unique rolls.

            ``#!python ((1, 1, …, 1), (1, 1, …, 2), …, (1, 1, …, m), …, (m - 1, m, …,
            m), (m, m, …, m))``

            To determine the count for a particular roll ``#!python (a, b, …, n)``, we
            compute the multinomial coefficient for that roll and multiply by the scalar
            ``#!python H(m)[a] * H(m)[b] * … * H(m)[n]``. (See
            [this](https://www.lucamoroni.it/the-dice-roll-sum-problem/) for an in-depth
            exploration of the topic.)

            Further, this implementation attempts to optimize heterogeneous pools by
            breaking them into homogeneous groups before computing the Cartesian product
            of those sub-results. This approach allows homogeneous pools to be ordered
            without duplicates, where heterogeneous ones offer no such guarantees.

            As expected, this optimization allows the performance of arbitrary selection
            from mixed pools to sit between that of purely homogeneous and purely
            heterogeneous ones. Note, however, that all three appear to scale
            geometrically in some way.

            ```ipython
            In [1]: from dyce import H, P

            In [2]: for n in (6, 8):
               ...:   p = n@P(6)
               ...:   for i in range(len(p) - 4, len(p)):
               ...:     print(f"({p}).h(slice({i})):")
               ...:     %timeit p.h(slice(i))
            (P(6, 6, 6, 6, 6, 6)).h(slice(2)):
            1.35 ms ± 23.4 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
            (P(6, 6, 6, 6, 6, 6)).h(slice(3)):
            3.15 ms ± 516 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(6, 6, 6, 6, 6, 6)).h(slice(4)):
            5.37 ms ± 182 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(6, 6, 6, 6, 6, 6)).h(slice(5)):
            10.5 ms ± 1.3 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(6, 6, 6, 6, 6, 6, 6, 6)).h(slice(4)):
            5.58 ms ± 25.3 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(6, 6, 6, 6, 6, 6, 6, 6)).h(slice(5)):
            9.81 ms ± 171 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(6, 6, 6, 6, 6, 6, 6, 6)).h(slice(6)):
            14.7 ms ± 430 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(6, 6, 6, 6, 6, 6, 6, 6)).h(slice(7)):
            20.4 ms ± 328 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

            In [3]: for n in (3, 4):
               ...:   p = P(n@P(6), *[H(6) - m for m in range(n, 0, -1)])
               ...:   for i in range(len(p) - 4, len(p)):
               ...:     print(f"({p}).h(slice({i})):")
               ...:     %timeit p.h(slice(i))
            (P(H({-2: 1, ..., 3: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6)).h(slice(2)):
            16.1 ms ± 1.09 ms per loop (mean ± std. dev. of 7 runs, 100 loops each)
            (P(H({-2: 1, ..., 3: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6)).h(slice(3)):
            39 ms ± 602 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-2: 1, ..., 3: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6)).h(slice(4)):
            40.3 ms ± 3.49 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-2: 1, ..., 3: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6)).h(slice(5)):
            46.2 ms ± 7.43 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-3: 1, ..., 2: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6)).h(slice(4)):
            538 ms ± 9.46 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-3: 1, ..., 2: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6)).h(slice(5)):
            534 ms ± 30.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-3: 1, ..., 2: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6)).h(slice(6)):
            536 ms ± 13.2 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-3: 1, ..., 2: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6)).h(slice(7)):
            604 ms ± 52.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

            In [4]: for n in (6, 8):
               ...:   p = P(*[H(6) - m for m in range(n, 0, -1)])
               ...:   for i in range(len(p) - 4, len(p)):
               ...:     print(f"({p}).h(slice({i})):")
               ...:     %timeit p.h(slice(i))
            (P(H({-5: 1, ..., 0: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(2)):
            145 ms ± 4.59 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-5: 1, ..., 0: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(3)):
            147 ms ± 3.6 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-5: 1, ..., 0: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(4)):
            158 ms ± 1.38 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-5: 1, ..., 0: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(5)):
            147 ms ± 691 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
            (P(H({-7: 1, ..., -2: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(4)):
            6.09 s ± 14.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-7: 1, ..., -2: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(5)):
            6.11 s ± 36.9 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-7: 1, ..., -2: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(6)):
            6.25 s ± 47.5 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            (P(H({-7: 1, ..., -2: 1}), ..., H({0: 1, ..., 5: 1}))).h(slice(7)):
            6.31 s ± 42.2 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            ```
        """
        n = len(self)

        if not which:
            i: Optional[int] = n
        else:
            i = _analyze_selection(n, which)

        if i == 0 or n == 0:
            rolls_with_counts_iter: Iterable[_RollCountT] = iter(())
        else:
            groups = tuple((h, sum(1 for _ in hs)) for h, hs in groupby(self))

            if len(groups) == 1:
                # Based on cursory performance analysis, calling the homogeneous
                # implementation directly provides about a 15% performance savings over
                # merely falling through to _rwc_heterogeneous_h_groups. Maybe
                # itertools.product adds significant overhead?
                h, hn = groups[0]
                assert hn == n

                # Still in search of a better (i.e., more efficient) way:
                # https://math.stackexchange.com/questions/4173084/probability-distribution-of-k-1-k-2-cdots-k-m-selections-of-arbitrary-posi
                if i and abs(i) < n:
                    rolls_with_counts_iter = (
                        _rwc_homogeneous_n_h_using_karonen_partial_selection(
                            h, n, i, fill=0
                        )
                    )
                else:
                    rolls_with_counts_iter = (
                        _rwc_homogeneous_n_h_using_multinomial_coefficient(h, n)
                    )
            else:
                rolls_with_counts_iter = _rwc_heterogeneous_h_groups(groups, i)

        for sorted_outcomes_for_roll, roll_count in rolls_with_counts_iter:
            if which:
                taken_outcomes = tuple(getitems(sorted_outcomes_for_roll, which))
            else:
                taken_outcomes = sorted_outcomes_for_roll

            yield taken_outcomes, roll_count

    def map(
        self,
        op: _BinaryOperatorT,
        right_operand: _OperandT,
    ) -> P:
        r"""
        Shorthand for ``#!python P(*(h.map(op, right_operand) for h in self))``. See the
        [``H.map`` method][dyce.h.H.map].

        ``` python
        >>> import operator
        >>> p_3d6 = 3@P(H((-3, -1, 2, 4)))
        >>> p_3d6.map(operator.__mul__, -1)
        P(H({-4: 1, -2: 1, 1: 1, 3: 1}), H({-4: 1, -2: 1, 1: 1, 3: 1}), H({-4: 1, -2: 1, 1: 1, 3: 1}))

        ```
        """
        return P(*(h.map(op, right_operand) for h in self))

    def rmap(
        self,
        left_operand: OutcomeT,
        op: _BinaryOperatorT,
    ) -> P:
        r"""
        Shorthand for ``#!python P(*(h.rmap(left_operand, op) for h in self))``. See the
        [``H.rmap`` method][dyce.h.H.rmap].

        ``` python
        >>> import operator
        >>> from fractions import Fraction
        >>> p_3d6 = 2@P(H((-3, -1, 2, 4)))
        >>> p_3d6.umap(Fraction).rmap(1, operator.__truediv__)
        P(H({Fraction(-1, 1): 1, Fraction(-1, 3): 1, Fraction(1, 4): 1, Fraction(1, 2): 1}), H({Fraction(-1, 1): 1, Fraction(-1, 3): 1, Fraction(1, 4): 1, Fraction(1, 2): 1}))

        ```
        """
        return P(*(h.rmap(left_operand, op) for h in self))

    def umap(self, op: _UnaryOperatorT) -> P:
        r"""
        Shorthand for ``#!python P(*(h.umap(op) for h in self))``. See the
        [``H.umap`` method][dyce.h.H.umap].

        ``` python
        >>> import operator
        >>> p_3d6 = 3@P(H((-3, -1, 2, 4)))
        >>> p_3d6.umap(operator.__neg__)
        P(H({-4: 1, -2: 1, 1: 1, 3: 1}), H({-4: 1, -2: 1, 1: 1, 3: 1}), H({-4: 1, -2: 1, 1: 1, 3: 1}))
        >>> p_3d6.umap(operator.__abs__)
        P(H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1}))

        ```
        """
        return P(*(h.umap(op) for h in self))


# ---- Functions -----------------------------------------------------------------------


def _analyze_selection(
    n: int,
    which: Iterable[_GetItemT],
) -> Optional[int]:
    r"""
    Examines the selection *which* as applied to the values ``#!python range(n)`` and
    returns one of:

    * $0$ – *which* selects zero elements in the range
    * $\{ {i} \mid {i < n} \}$ – *which* favors elements $[0..i)$
    * $\{ {-i} \mid {i < n} \}$ – *which* favors elements $[i..n)$
    * $\{ {k} \mid {k \mod n = 0} \}$ – *which* selects each of $[0..n)$ exactly $k$ times
    * ``#!python None`` – any other selection
    """
    indexes = tuple(range(n))
    counts_by_index = counter(getitems(indexes, which))
    found_indexes = set(counts_by_index)

    if not found_indexes:
        return 0

    missing_indexes = set(indexes) - found_indexes
    distinct_counts = set(counts_by_index.values())
    assert 0 not in distinct_counts

    min_index = min(found_indexes)
    max_index = max(found_indexes) + 1

    if max_index - min_index == n:
        if not missing_indexes and len(distinct_counts) == 1:
            return n * distinct_counts.pop()
        else:
            return None
    elif min_index > n - max_index:
        return min_index - n
    elif min_index <= n - max_index:
        return max_index
    else:
        assert False, "should never be here"


def _rwc_heterogeneous_h_groups(
    h_groups: Iterable[Tuple[_MappingT, int]],
    k: Optional[int],
) -> Iterator[_RollCountT]:
    r"""
    Given an iterable of histogram/count pairs, returns an iterator yielding 2-tuples
    (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts].

    The use of histogram/count pairs for *h_groups* is acknowledged as awkward, but
    intended, since its implementation is optimized to leverage homogeneous
    optimizations (e.g.,
    [``_rwc_homogeneous_n_h_using_multinomial_coefficient``][dyce.p._rwc_homogeneous_n_h_using_multinomial_coefficient]).

    If provided, *k* signals which outcomes are to be selected from the produced rolls.
    This affords an additional optimization where *k* is less than the size of a
    homogeneous subgroup.
    """

    def _choose_rwc_homogeneous_n_h_implementation(h, n) -> Iterator[_RollCountT]:
        if k and abs(k) < n:
            return _rwc_homogeneous_n_h_using_karonen_partial_selection(h, n, k)
        else:
            return _rwc_homogeneous_n_h_using_multinomial_coefficient(h, n)

    for v in product(
        *(_choose_rwc_homogeneous_n_h_implementation(h, n) for h, n in h_groups)
    ):
        # It's possible v is () if h_groups is empty; see
        # https://stackoverflow.com/questions/3154301/ for a detailed discussion
        if v:
            rolls_by_group: Iterable[Iterable[OutcomeT]]
            counts_by_group: Iterable[int]
            rolls_by_group, counts_by_group = zip(*v)
            sorted_outcomes_for_roll = tuple(sorted(chain(*rolls_by_group)))
            total_count = reduce(__mul__, counts_by_group)

            yield sorted_outcomes_for_roll, total_count


def _rwc_homogeneous_n_h_using_karonen_partial_selection(
    h: H,
    n: int,
    k: int,
    fill: Optional[OutcomeT] = None,
) -> Iterator[_RollCountT]:
    r"""
    A memoized adaptation of [Ilmari Karonen’s
    optimization](https://rpg.stackexchange.com/a/166663/71245) yielding 2-tuples
    (pairs) for partial rolls. This is analogous to
    [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts] reflecting taking *k* outcomes
    from *n* histograms *h* with some additional limitations. If *fill* is ``#!python
    None``, non-selected terms are omitted. Otherwise, if *k* is positive, the lowest
    $k$ values are selected and higher ones will have *fill* as their values. If *k* is
    negative, the highest $-k$ values are selected and lower ones will be filled. No
    particular roll ordering is guaranteed, but there are no repetitions.


    ``` python
    >>> from dyce.p import _rwc_homogeneous_n_h_using_karonen_partial_selection
    >>> sorted(_rwc_homogeneous_n_h_using_karonen_partial_selection(H(6), 3, 0))
    []

    ```

    ``` python
    >>> sorted(_rwc_homogeneous_n_h_using_karonen_partial_selection(H(6), 3, 2, fill=None))
    [((1, 1), 16), ((1, 2), 27), ((1, 3), 21), ..., ((5, 5), 4), ((5, 6), 3), ((6, 6), 1)]
    >>> sorted(_rwc_homogeneous_n_h_using_karonen_partial_selection(H(6), 3, 2, fill=0))
    [((1, 1, 0), 16), ((1, 2, 0), 27), ((1, 3, 0), 21), ..., ((5, 5, 0), 4), ((5, 6, 0), 3), ((6, 6, 0), 1)]

    ```

    ``` python
    >>> sorted(_rwc_homogeneous_n_h_using_karonen_partial_selection(H(6), 3, -2, fill=None))
    [((1, 1), 1), ((1, 2), 3), ((1, 3), 3), ..., ((5, 5), 13), ((5, 6), 27), ((6, 6), 16)]
    >>> sorted(_rwc_homogeneous_n_h_using_karonen_partial_selection(H(6), 3, -2, fill=-1))
    [((-1, 1, 1), 1), ((-1, 1, 2), 3), ((-1, 1, 3), 3), ..., ((-1, 5, 5), 13), ((-1, 5, 6), 27), ((-1, 6, 6), 16)]

    ```
    """
    from_upper = k < 0
    k = abs(k)

    if k == 0 or k > n:
        # Maintain consistency with comb(n, k) == 0 where k > n
        return iter(())

    _DistributionEntryT = Tuple[_RollT, Fraction]
    _DistributionT = Iterator[_DistributionEntryT]
    _SelectCallableT = Callable[[H, int, int], _DistributionT]

    def _memoize(f: _SelectCallableT) -> _SelectCallableT:
        cache: DefaultDict[Tuple[H, int, int], List[_DistributionEntryT]] = defaultdict(
            list
        )

        @wraps(f)
        def _wrapped(h: H, n: int, k: int) -> _DistributionT:
            if (h, n, k) not in cache:
                cache[h, n, k].extend(f(h, n, k))

            return iter(cache[h, n, k])

        return _wrapped

    @_memoize
    def _selected_distributions(
        h: H,
        n: int,
        k: int,
    ) -> _DistributionT:
        if len(h) <= 1:
            whole = k * tuple(h)
            yield whole, Fraction(1)
        else:
            this_total = h.total ** n

            if from_upper:
                this_outcome = max(h)
            else:
                this_outcome = min(h)

            next_h = H(
                (outcome, count)
                for outcome, count in h.items()
                if outcome != this_outcome
            )
            accounted_for_p = Fraction(0)

            for i in range(0, k + 1):
                head = i * (this_outcome,)
                head_count = h.exactly_k_times_in_n(this_outcome, n, i)
                head_p = Fraction(head_count, this_total)

                if i < k:
                    accounted_for_p += head_p

                    for tail, tail_p in _selected_distributions(next_h, n - i, k - i):
                        if from_upper:
                            whole = tail + head
                        else:
                            whole = head + tail

                        whole_p = head_p * tail_p
                        yield whole, whole_p
                else:
                    yield head, Fraction(1) - accounted_for_p

    total_count = h.total ** n

    for outcomes, count in _selected_distributions(h, n, k):
        count *= total_count
        assert count.denominator == 1

        if fill is not None:
            outcomes = (
                (fill,) * (n - k) + outcomes
                if from_upper
                else outcomes + (fill,) * (n - k)
            )

        yield (outcomes, count.numerator)


def _rwc_homogeneous_n_h_using_multinomial_coefficient(
    h: _MappingT,
    n: int,
) -> Iterator[_RollCountT]:
    r"""
    Given a group of *n* identical histograms *h*, returns an iterator yielding ordered
    2-tuples (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts]. See that
    method’s explanation of homogeneous pools for insight into this implementation.
    """
    # combinations_with_replacement("ABC", 2) --> AA AB AC BB BC CC; note that input
    # order is preserved and H outcomes are already sorted
    multinomial_coefficient_numerator = factorial(n)
    rolls_iter = combinations_with_replacement(h, n)

    for sorted_outcomes_for_roll in rolls_iter:
        count_scalar = reduce(
            __mul__, (h[outcome] for outcome in sorted_outcomes_for_roll)
        )
        multinomial_coefficient_denominator = reduce(
            __mul__,
            (
                factorial(sum(1 for _ in g))
                for _, g in groupby(sorted_outcomes_for_roll)
            ),
        )

        yield (
            sorted_outcomes_for_roll,
            count_scalar
            * multinomial_coefficient_numerator
            // multinomial_coefficient_denominator,
        )

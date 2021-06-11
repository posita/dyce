# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations, generator_stop

from collections import Counter as counter
from collections import defaultdict
from fractions import Fraction
from functools import reduce, wraps
from itertools import chain, combinations_with_replacement, groupby, product, repeat
from math import factorial
from numbers import Integral
from operator import abs as op_abs
from operator import eq as op_eq
from operator import getitem as op_getitem
from operator import mul as op_mul
from operator import ne as op_ne
from operator import neg as op_neg
from operator import pos as op_pos
from typing import (
    Callable,
    Counter,
    DefaultDict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from .h import H, HAbleBinOpsMixin, _CoalesceT, _CountT, _ExpandT, _FaceT, _MappingT
from .symmetries import comb, sum_w_start

__all__ = ("P",)


# ---- Data ----------------------------------------------------------------------------


_T = TypeVar("_T")
_GetItemT = Union[int, slice]
_OperandT = Union[_FaceT, "P"]


# ---- Classes -------------------------------------------------------------------------


class P(Sequence[H], HAbleBinOpsMixin):
    r"""
    An immutable pool (ordered sequence) supporting group operations for zero or more
    [``H`` objects][dyce.h.H] (provided or created from the
    [initializer][dyce.p.P.__init__]’s *args* parameter).

    This class implements the [``HAbleT`` protocol][dyce.h.HAbleT] and derives from the
    [``HAbleBinOpsMixin`` class][dyce.h.HAbleBinOpsMixin], which means it can be
    “flattened” into a single histogram, either explicitly via the
    [``h`` method][dyce.p.P.h], or implicitly by using binary arithmetic operations.
    Note that unary operators and the ``@`` operator result in new ``P`` objects, not
    flattened histograms.

    ```python
    >>> from dyce import P
    >>> p_d6 = P(6)  # shorthand for P(H(6))
    >>> p_d6
    P(6)
    >>> -p_d6
    P(-6)

    ```

    ```python
    >>> P(p_d6, p_d6)  # 2d6
    P(6, 6)
    >>> 2@p_d6  # also 2d6
    P(6, 6)
    >>> 2@(2@p_d6) == 4@p_d6
    True

    ```

    ```python
    >>> p = P(4, P(6, P(8, P(10, P(12, P(20))))))
    >>> p
    P(4, 6, 8, 10, 12, 20)
    >>> sum(p.roll()) in p.h()
    True

    ```

    Arithmetic operators involving a number or another ``P`` object produce an
    [``H`` object][dyce.h.H]:

    ```python
    >>> p_d6 + p_d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    ```

    ```python
    >>> 2 * P(8) - 1
    H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})

    ```

    Comparisons with [``H`` objects][dyce.h.H] work as expected:

    ```python
    >>> from dyce import H
    >>> 3@p_d6 == H(6) + H(6) + H(6)
    True

    ```

    Indexing selects a contained histogram:

    ```python
    >>> P(4, 6, 8)[0]
    H(4)

    ```

    Note that pools are opinionated about histogram ordering:

    ```python
    >>> P(8, 6, 4)[0] == P(8, 4, 6)[0] == H(4)
    True

    ```

    In an extension to (departure from) the [``HAbleT`` protocol][dyce.h.HAbleT], the
    [``P.h`` method][dyce.p.P.h]’s implementation also affords subsets of faces to be
    “taken” (selected) by passing in selection criteria. Values are indexed from least
    to greatest. Negative indexes are supported and retain their idiomatic meaning.
    Modeling the sum of the greatest two faces of three six-sided dice (``3d6``) can be
    expressed as:

    ```python
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

    def __init__(self, *args: Union[int, "P", H]) -> None:
        r"Initializer."
        super().__init__()

        def _gen_hs():
            for a in args:
                if isinstance(a, (int, Integral)):
                    yield H(a)
                elif isinstance(a, H):
                    yield a
                elif isinstance(a, P):
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
        self._homogeneous = len(set(self._hs)) <= 1

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def parts():
            for h in self._hs:
                yield (
                    str(h._simple_init)  # pylint: disable=protected-access
                    if h._simple_init is not None  # pylint: disable=protected-access
                    else repr(h)
                )

        args = ", ".join(parts())

        return f"{self.__class__.__name__}({args})"

    def __eq__(self, other) -> bool:
        if isinstance(other, P):
            return op_eq(self._hs, other._hs)
        else:
            return NotImplemented

    def __ne__(self, other) -> bool:
        if isinstance(other, P):
            return op_ne(self._hs, other._hs)
        else:
            return NotImplemented

    def __len__(self) -> int:
        return len(self._hs)

    @overload
    def __getitem__(self, key: int) -> H:
        ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[H, ...]:
        ...

    def __getitem__(self, key: _GetItemT) -> Union[H, Tuple[H, ...]]:
        return self._hs[key]

    def __iter__(self) -> Iterator[H]:
        return iter(self._hs)

    def __matmul__(self, other: int) -> "P":
        if not isinstance(other, (int, Integral)):
            return NotImplemented
        elif other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return P(*chain.from_iterable(repeat(self._hs, other)))

    def __rmatmul__(self, other: int) -> "P":
        return self.__matmul__(other)

    def __neg__(self) -> "P":
        return P(*(op_neg(h) for h in self._hs))

    def __pos__(self) -> "P":
        return P(*(op_pos(h) for h in self._hs))

    def __abs__(self) -> "P":
        return P(*(op_abs(h) for h in self._hs))

    def h(self, *which: _GetItemT) -> H:
        r"""
        When provided no arguments, ``h`` combines (or “flattens”) contained histograms in
        accordance with the [``HAbleT`` protocol][dyce.h.HAbleT]:

        ```python
        >>> (2@P(6)).h()
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        ```

        If the optional *which* parameter is provided, ``h`` sums subsets of faces
        identified by *which*. *which* can include ``int``s and ``slice``s.

        All outcomes are counted. For each outcome, dice are ordered from least (index
        ``0``) to greatest (index ``-1`` or ``len(self)``). Taking the greatest of two
        six-sided dice can be modeled as:

        ```python
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

        Slices and arbitrary iterables support more flexible face selections:

        ```python
        >>> p_6d6 = 6@P(6)
        >>> every_other_d6 = p_6d6.h(slice(None, None, -2))
        >>> every_other_d6
        H({3: 1, 4: 21, 5: 86, ..., 16: 1106, 17: 395, 18: 31})
        >>> p_6d6.h(5, 3, 1) == every_other_d6
        True
        >>> p_6d6.h(*range(1, 6, 2)) == every_other_d6
        True
        >>> p_6d6.h(*(i for i in range(0, 6) if i % 2 == 1)) == every_other_d6
        True
        >>> p_6d6.h(*{1, 3, 5}) == every_other_d6
        True

        ```

        Taking the greatest two and least two faces of ten four-sided dice (``10d4``)
        can be modeled as:

        ```python
        >>> p_10d4 = 10@P(4)
        >>> p_10d4.h(slice(2), slice(-2, None))
        H({4: 1, 5: 10, 6: 1012, 7: 5030, 8: 51973, 9: 168760, 10: 595004, 11: 168760, 12: 51973, 13: 5030, 14: 1012, 15: 10, 16: 1})
        >>> print(p_10d4.h(slice(2), slice(-2, None)).format(width=65))
        avg |   10.00
        std |    0.91
        var |    0.84
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

        ```

        Taking contiguous faces from either end of a homogeneous pool benefits from
        [Ilmari Karonen’s optimization](https://rpg.stackexchange.com/a/166663/71245):

        ```python
        In [2]: %timeit P(6, 6, 6, 6, 6, 6, 6, 6, 6, 6).h(slice(-2, None))  # homogeneous from end (optimized)
        2.03 ms ± 24.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

        In [3]: %timeit P(6, 6, 6, 6, 6, 6, 6, 6, 6, 6).h(slice(3, 5))  # homogeneous from middle (less efficient)
        24.1 ms ± 461 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

        In [4]: %timeit P(4, 4, 4, 4, 4, 6, 6, 6, 6, 6).h(slice(-2, None))  # heterogeneous (least efficient)
        41.8 ms ± 526 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
        ```

        Taking all faces is equivalent to our sum operation:

        ```python
        >>> d6 = H(6)
        >>> d233445 = H((2, 3, 3, 4, 4, 5))
        >>> p = 2@P(d6, d233445)
        >>> p.h(slice(None)) == d6 + d6 + d233445 + d233445
        True
        >>> p.h(slice(None)) == p.h()
        True

        ```
        """
        n = len(self._hs)
        from_end = _analyze_selection(n, which)

        if not which:
            # The caller offered no selection
            return sum_w_start(self._hs, start=H({}))
        elif from_end == 0:
            # The caller explicitly selected zero dice
            return H({})
        elif from_end == n:
            # The caller selected all dice in the pool exactly once
            return self.h()
        elif self.homogeneous and n and from_end:
            # Optimize when taking from an end of a non-zero length homogeneous
            # pool
            return H(
                (sum(roll), count)
                for roll, count in _select_from_end(self._hs[0], n, from_end)
            )
        else:
            # Do it the hard way
            return H(_take_and_sum_faces(self.rolls_with_counts(), which))

    # ---- Properties ------------------------------------------------------------------

    @property
    def homogeneous(self) -> bool:
        return self._homogeneous

    # ---- Methods ---------------------------------------------------------------------

    def lt(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().lt(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.lt``][dyce.h.H.lt].
        """
        return self.h().lt(other)

    def le(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().le(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.le``][dyce.h.H.le].
        """
        return self.h().le(other)

    def eq(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().eq(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.eq``][dyce.h.H.eq].
        """
        return self.h().eq(other)

    def ne(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().ne(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.ne``][dyce.h.H.ne].
        """
        return self.h().ne(other)

    def gt(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().gt(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.gt``][dyce.h.H.gt].
        """
        return self.h().gt(other)

    def ge(self, other: _OperandT) -> H:
        r"""
        Shorthand for ``self.h().ge(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.ge``][dyce.h.H.ge].
        """
        return self.h().ge(other)

    def even(self) -> H:
        r"""
        Shorthand for ``self.h().even()``. See the [``h`` method][dyce.p.P.h] and
        [``H.even``][dyce.h.H.even].
        """
        return self.h().even()

    def odd(self) -> H:
        r"""
        Shorthand for ``self.h().odd()``. See the [``h`` method][dyce.p.P.h] and
        [``H.odd``][dyce.h.H.odd].
        """
        return self.h().odd()

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: _CoalesceT = None,
        max_depth: int = 1,
    ) -> H:
        r"""
        Shorthand for ``self.h().substitute(expand, coalesce, max_depth)``. See the
        [``h`` method][dyce.p.P.h] and [``H.substitute``][dyce.h.H.substitute].
        """
        return self.h().substitute(expand, coalesce, max_depth)

    def appearances_in_rolls(self, face: _FaceT) -> H:
        r"""
        !!! warning "Experimental"

            This method should be considered experimental and may disappear in future
            versions. While it does provide a performance improvement over other
            techniques, it is not significant for most applications, and rarely
            justifies the corresponding reduction in readability.

        Returns a histogram where the “faces” (keys) are the number of times *face*
        appears, and the counts are the number of rolls where *face* appears precisely
        that number of times. Equivalent to ``H((sum(1 for f in roll if f == face),
        count) for roll, count in self.rolls_with_counts())``, but much more efficient.

        ```python
        >>> p_2d6 = P(6, 6)
        >>> tuple(p_2d6.rolls_with_counts())
        (((1, 1), 1), ((1, 2), 2), ((1, 3), 2), ((1, 4), 2), ((1, 5), 2), ((1, 6), 2), ...)
        >>> p_2d6.appearances_in_rolls(1)
        H({0: 25, 1: 10, 2: 1})

        >>> # Least efficient, by far
        >>> d4, d6 = H(4), H(6)
        >>> p_3d4_2d6 = P(d4, d4, d4, d6, d6)
        >>> H((sum(1 for f in roll if f == 3), count) for roll, count in p_3d4_2d6.rolls_with_counts())
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        >>> # Pretty darned efficient, generalizable to other boolean inquiries, and
        >>> # arguably the most readable
        >>> d4_eq3, d6_eq3 = d4.eq(2), d6.eq(2)
        >>> 3@d4_eq3 + 2@d6_eq3
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        >>> # Most efficient for large sets of dice
        >>> p_3d4_2d6.appearances_in_rolls(3)
        H({0: 675, 1: 945, 2: 522, 3: 142, 4: 19, 5: 1})

        ```

        Based on some rudimentary testing, this method appears to converge on being
        almost twice (about $\frac{7}{4}$) as efficient as the boolean accumulation
        technique for larger sets:

        ```python
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
        group_counters: List[Counter[_FaceT]] = []

        for h, hs in groupby(self._hs):
            group_counter: Counter[_FaceT] = counter()
            n = sum(1 for _ in hs)

            for k in range(0, n + 1):
                group_counter[k] = _count_of_exactly_k_of_face_in_n_of_h(
                    h, face, n, k
                ) * (group_counter[k] if group_counter[k] else 1)

            group_counters.append(group_counter)

        return sum_w_start(
            (H(group_counter) for group_counter in group_counters), start=H({})
        )

    def explode(self, max_depth: int = 1) -> H:
        r"""
        Shorthand for ``self.h().explode(max_depth)``. See the [``h`` method][dyce.p.P.h]
        and [``H.explode``][dyce.h.H.explode].
        """
        return self.h().explode(max_depth)

    def roll(self) -> Tuple[_FaceT, ...]:
        r"""
        Returns (weighted) random faces from contained histograms.
        """
        return tuple(h.roll() for h in self._hs)

    def rolls_with_counts(self) -> Iterator[Tuple[Tuple[_FaceT, ...], _CountT]]:
        r"""
        Returns an iterator that yields 2-tuples (pairs) that, collectively, enumerate all
        possible outcomes for the pool. The first item in the 2-tuple is a sorted
        sequence of the faces for a distinct roll. The second is the count for that
        roll. Faces in each roll are ordered least to greatest.

        We can model the likelihood of achieving a “Yhatzee” (i.e., where five six-sided
        dice show the same face) on a single roll by checking rolls for where the least
        and greatest faces are the same:

        ```python
        >>> p_5d6 = 5@P(6)
        >>> yhatzee_on_single_roll = H(
        ...   (1 if roll[0] == roll[-1] else 0, count)
        ...   for roll, count
        ...   in p_5d6.rolls_with_counts()
        ... )
        >>> print(yhatzee_on_single_roll.format(width=0))
        {..., 0: 99.92%, 1:  0.08%}

        ```

        Note that, in the general case, rolls may appear more than once, and there are
        no guarantees about their order.

        ```python
        >>> list(P(H(2), H(3)).rolls_with_counts())
        [((1, 1), 1), ((1, 2), 1), ((1, 3), 1), ((1, 2), 1), ((2, 2), 1), ((2, 3), 1)]

        ```

        In the above, `(1, 2)` appears a total of two times, each with counts of one.

        However, if the pool is homogeneous (meaning it only contains identical
        histograms), faces are not repeated and are presented in order. (See the note
        on implementation below.)

        ```python
        >>> list((2@P(H((-1, 0, 1)))).rolls_with_counts())
        [((-1, -1), 1), ((-1, 0), 2), ((-1, 1), 2), ((0, 0), 1), ((0, 1), 2), ((1, 1), 1)]

        ```

        By summing and counting all rolls, we can confirm equivalence to taking all
        faces:

        ```python
        >>> d6 = H(6)
        >>> d233445 = H((2, 3, 3, 4, 4, 5))
        >>> pool = 2@P(d6, d233445)
        >>> H((sum(r), c) for r, c in pool.rolls_with_counts()) == pool.h(slice(None))
        True

        ```

        !!! info "About the implementation"

            Enumeration is substantially more efficient for homogeneous pools than
            heterogeneous ones. This is because, instead of merely computing the
            Cartesian product, we are able to leverage the [*multinomial
            coefficient*](https://en.wikipedia.org/wiki/Permutation#Permutations_of_multisets):

            $$
            {{n} \choose {{{k}_{1}},{{k}_{2}},\ldots,{{k}_{m}}}}
            = {\frac {{n}!} {{{k}_{1}}! {{k}_{2}}! \cdots {{k}_{m}}!}}
            $$

            We enumerate combinations with replacements, and then the compute the number
            of permutations with repetitions for each combination. Consider
            ``n@P(H(m))``. Enumerating combinations with replacements would yield all
            unique rolls:

            ``((1, 1, …, 1), (1, 1, …, 2), …, (1, 1, …, m), …, (m - 1, m, …, m), (m, m, …, m))``

            To determine the count for a particular roll ``(a, b, …, n)``, we compute
            the multinomial coefficient for that roll and multiply by the scalar
            ``H(m)[a] * H(m)[b] * … * H(m)[n]``. (See
            [this](https://www.lucamoroni.it/the-dice-roll-sum-problem/) for an in-depth
            exploration of the topic.)

            This implementation attempts to optimize heterogeneous pools by breaking
            them into homogeneous groups before computing the Cartesian product of those
            sub-results. This approach allows homogeneous pools to be ordered without
            duplicates, while heterogeneous ones offer no such guarantees.

            As expected, this optimization allows mixed pools’ performance to sit
            between purely homogeneous and purely heterogeneous ones. However, note that
            all three scale geometrically for arbitrary selections.

            ```ipython
            In [1]: from dyce import H, P

            In [2]: for i in range(2, 11, 2):
               ...:     p = i@P(6)
               ...:     print("Pool len {} (homogeneous): {}".format(len(p), p))
               ...:     %timeit p.h(slice(None, None, 2))
               ...:
            Pool len 2 (homogeneous): P(6, 6)
            392 µs ± 14 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
            Pool len 4 (homogeneous): P(6, 6, 6, 6)
            697 µs ± 17.5 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
            Pool len 6 (homogeneous): P(6, 6, 6, 6, 6, 6)
            3.19 ms ± 626 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            Pool len 8 (homogeneous): P(6, 6, 6, 6, 6, 6, 6, 6)
            9.07 ms ± 702 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            Pool len 10 (homogeneous): P(6, 6, 6, 6, 6, 6, 6, 6, 6, 6)
            22.1 ms ± 511 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

            In [3]: for i in range(1, 6):
               ...:     hs = [H(6) for _ in range(i)]
               ...:     hs.extend(H(6) - j for j in range(1, i + 1))
               ...:     p = P(*hs)
               ...:     print("Pool len {} (mixed): {}".format(len(p), p))
               ...:     %timeit p.h(slice(None, None, 2))
               ...:
            Pool len 2 (mixed): P(H({0: 1, ..., 5: 1}), 6)
            273 µs ± 1.78 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
            Pool len 4 (mixed): P(H({-1: 1, ..., 4: 1}), H({0: 1, ..., 5: 1}), 6, 6)
            2.45 ms ± 20.6 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            Pool len 6 (mixed): P(H({-2: 1, ..., 3: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6)
            36.5 ms ± 1.27 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            Pool len 8 (mixed): P(H({-3: 1, ..., 2: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6)
            544 ms ± 109 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            Pool len 10 (mixed): P(H({-4: 1, ..., 1: 1}), ..., H({0: 1, ..., 5: 1}), 6, 6, 6, 6, 6)
            6.68 s ± 271 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

            In [4]: for i in range(2, 9, 2):  # larger takes too long on my laptop
               ...:     p = P(*(H(6) - j for j in range(i)))
               ...:     print("Pool len {} (heterogeneous): {}".format(len(p), p))
               ...:     %timeit p.h(slice(None, None, 2))
               ...:
            Pool len 2 (heterogeneous): P(H({0: 1, ..., 5: 1}), H({1: 1, ..., 6: 1}))
            269 µs ± 11.7 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
            Pool len 4 (heterogeneous): P(H({-2: 1, ..., 3: 1}), ..., H({1: 1, ..., 6: 1}))
            3.93 ms ± 182 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
            Pool len 6 (heterogeneous): P(H({-4: 1, ..., 1: 1}), ..., H({1: 1, ..., 6: 1}))
            148 ms ± 5.2 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
            Pool len 8 (heterogeneous): P(H({-6: 1, ..., -1: 1}), ..., H({1: 1, ..., 6: 1}))
            5.91 s ± 205 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
            ```
        """
        groups = tuple((h, sum(1 for _ in hs)) for h, hs in groupby(self._hs))

        if len(groups) == 1:
            # Optimization to use _rolls_with_counts_for_n_homogeneous_histograms
            # directly if there's only one group; roughly 15% time savings over
            # delegating to _rolls_with_counts_for_heterogeneous_histograms based on
            # cursory performance analysis
            h, n = groups[0]

            return _rolls_with_counts_for_n_homogeneous_histograms(h, n)
        else:
            return _rolls_with_counts_for_heterogeneous_histograms(groups)

    def within(self, lo: _FaceT, hi: _FaceT, other: _OperandT = 0) -> H:
        r"""
        Shorthand for ``self.h().within(lo, hi, other)``. See the [``h`` method][dyce.p.P.h]
        and [``H.within``][dyce.h.H.within].
        """
        return self.h().within(lo, hi, other)


# ---- Functions -----------------------------------------------------------------------


def _analyze_selection(
    n: int,
    which: Iterable[_GetItemT],
) -> Optional[int]:
    r"""
    Examines the selection *which* as applied to a sequence of length *n* and returns
    one of:

    * `0` - *which* selects zero elements in the sequence
    * `i` - *which* selects exactly `i` elements from the left side of the
      sequence
    * `-i` - *which* selects exactly `i` elements from the right side of the
      sequence
    * `n` - *which* selects each element of the sequence exactly once
    * `None` - any other selection
    """
    index_counts = counter(_getitems(list(range(n)), which))

    if any(v for v in index_counts.values() if v != 1):
        return None

    indexes = set(index_counts)
    from_lt: Set[int] = set()
    from_rt: Set[int] = set()
    contiguous_from_lt = False
    contiguous_from_rt = False

    for i in range(n + 1):
        contiguous_from_lt = contiguous_from_lt or not (indexes ^ from_lt)
        contiguous_from_rt = contiguous_from_rt or not (indexes ^ from_rt)
        from_lt.add(i)
        from_rt.add(n - i - 1)

    if contiguous_from_lt:
        return len(indexes)
    elif contiguous_from_rt:
        return -len(indexes)
    else:
        return None


def _coalesce_replace(h: H, face: _FaceT) -> H:  # pylint: disable=unused-argument
    return h


def _count_of_exactly_k_of_face_in_n_of_h(
    h: H,
    face: _FaceT,
    n: int,
    k: int,
) -> _CountT:
    c_face = h.get(face, 0)
    c_total = sum(h.counts())

    return comb(n, k) * c_face ** k * (c_total - c_face) ** (n - k)


def _getitems(sequence: Sequence[_T], keys: Iterable[_GetItemT]) -> Iterator[_T]:
    for key in keys:
        if isinstance(key, (int, Integral)):
            yield op_getitem(sequence, key)
        else:
            yield from op_getitem(sequence, key)


def _rolls_with_counts_for_heterogeneous_histograms(
    h_groups: Iterable[Tuple[_MappingT, int]]
) -> Iterator[Tuple[Tuple[_FaceT, ...], _CountT]]:
    r"""
    Given an iterable of histogram/count pairs, returns an iterator that yields 2-tuples
    (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts].

    The use of histogram/count pairs for *h_groups* is acknowledged as awkward, but
    intended, since its implementation is optimized to leverage
    [``_rolls_with_counts_for_n_homogeneous_histograms``][dyce.p._rolls_with_counts_for_n_homogeneous_histograms].
    """
    for v in product(
        *(_rolls_with_counts_for_n_homogeneous_histograms(h, n) for h, n in h_groups)
    ):
        # It's possible v is () if h_groups is empty; see
        # https://stackoverflow.com/questions/3154301/ for a detailed discussion
        if v:
            rolls_by_group: Iterable[Iterable[_FaceT]]
            counts_by_group: Iterable[_CountT]
            rolls_by_group, counts_by_group = zip(*v)
            sorted_faces_for_roll = tuple(sorted(chain(*rolls_by_group)))
            total_count = reduce(op_mul, counts_by_group)

            yield sorted_faces_for_roll, total_count


def _rolls_with_counts_for_n_homogeneous_histograms(
    h: _MappingT,
    n: int,
) -> Iterator[Tuple[Tuple[_FaceT, ...], _CountT]]:
    r"""
    Given a group of *n* identical histograms *h*, returns an iterator that yields
    ordered 2-tuples (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts].
    See that method’s explanation of homogeneous pools for insight into this
    implementation.
    """
    # combinations_with_replacement("ABC", 2) --> AA AB AC BB BC CC; note that input
    # order is preserved and H faces are already sorted
    multinomial_coefficient_numerator = factorial(n)
    rolls_iter = combinations_with_replacement(h, n)

    for sorted_faces_for_roll in rolls_iter:
        count_scalar = reduce(op_mul, (h[face] for face in sorted_faces_for_roll))
        multinomial_coefficient_denominator = reduce(
            op_mul,
            (factorial(sum(1 for _ in g)) for _, g in groupby(sorted_faces_for_roll)),
        )

        yield (
            sorted_faces_for_roll,
            count_scalar
            * multinomial_coefficient_numerator
            // multinomial_coefficient_denominator,
        )


def _select_from_end(
    h: H,
    n: int,
    k: int,
) -> Iterator[Tuple[Tuple[_FaceT, ...], _CountT]]:
    r"""
    Yields 2-tuples (pairs) for partial rolls (of length `abs(k)`) analogous to
    [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts] reflecting taking *k* faces
    from *n* histograms *h*. If *k* is positive, select the lowest `k` values. If *k* is
    negative, select the highest `abs(k)` values. No particular ordering is guaranteed.

    ```python
    >>> from dyce.p import _select_from_end
    >>> sorted(_select_from_end(H(6), 3, 2))
    [((1, 1), 16), ((1, 2), 27), ((1, 3), 21), ((1, 4), 15), ..., ((4, 6), 3), ((5, 5), 4), ((5, 6), 3), ((6, 6), 1)]
    >>> sorted(_select_from_end(H(6), 3, -2))
    [((1, 1), 1), ((1, 2), 3), ((1, 3), 3), ((1, 4), 3), ..., ((4, 6), 21), ((5, 5), 13), ((5, 6), 27), ((6, 6), 16)]

    ```

    This is an adaptation of [Ilmari Karonen’s
    optimization](https://rpg.stackexchange.com/a/166663/71245).
    """
    from_upper = k < 0
    k = abs(k)

    # Maintain Consistency with comb(n, n + 1) == 0
    if k > n:
        return iter(())

    _SelectReturnEntryT = Tuple[Tuple[_FaceT, ...], Fraction]
    _SelectReturnT = Iterator[_SelectReturnEntryT]
    _SelectCallableT = Callable[[H, int, int], _SelectReturnT]

    def _memoize(f: _SelectCallableT) -> _SelectCallableT:
        cache: DefaultDict[Tuple[H, int, int], List[_SelectReturnEntryT]] = defaultdict(
            list
        )

        @wraps(f)
        def _wrapped(h: H, n: int, k: int) -> _SelectReturnT:
            if (h, n, k) not in cache:
                cache[h, n, k].extend(f(h, n, k))

            return iter(cache[h, n, k])

        return _wrapped

    @_memoize
    def _selected_faces_with_probabilities(
        h: H,
        n: int,
        k: int,
    ) -> _SelectReturnT:
        if len(h) <= 1:
            whole = k * tuple(h)
            yield whole, Fraction(1)
        else:
            this_c = sum(h.counts())
            this_t = this_c ** n

            if from_upper:
                this_f = max(h)
            else:
                this_f = min(h)

            next_h = H((f, c) for f, c in h.items() if f != this_f)
            accounted_for_p = Fraction(0)

            for i in range(0, k + 1):
                head = i * (this_f,)
                head_c = _count_of_exactly_k_of_face_in_n_of_h(h, this_f, n, i)
                head_p = Fraction(head_c, this_t)

                if i < k:
                    accounted_for_p += head_p

                    for tail, tail_p in _selected_faces_with_probabilities(
                        next_h, n - i, k - i
                    ):
                        if from_upper:
                            whole = tail + head
                        else:
                            whole = head + tail

                        whole_p = head_p * tail_p
                        yield whole, whole_p
                else:
                    yield head, Fraction(1) - accounted_for_p

    total_c = sum(h.counts()) ** n
    yield from (
        (fs, int(c * total_c)) for fs, c in _selected_faces_with_probabilities(h, n, k)
    )


def _take_and_sum_faces(
    rolls_with_counts_iter: Iterator[Tuple[Sequence[_FaceT], _CountT]],
    which: Iterable[_GetItemT],
) -> Iterator[Tuple[_FaceT, _CountT]]:
    for (
        sorted_faces_for_roll,
        roll_count,
    ) in rolls_with_counts_iter:
        taken_faces = tuple(_getitems(sorted_faces_for_roll, which))

        if taken_faces:
            yield sum(taken_faces), roll_count

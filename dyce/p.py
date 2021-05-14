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
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from collections.abc import Iterable as ABCIterable
from functools import reduce
from itertools import (
    chain,
    combinations_with_replacement,
    groupby,
    product,
    repeat,
)
from math import factorial
from operator import (
    abs as op_abs,
    add as op_add,
    and_ as op_and,
    eq as op_eq,
    floordiv as op_floordiv,
    getitem as op_getitem,
    or_ as op_or,
    mod as op_mod,
    mul as op_mul,
    ne as op_ne,
    neg as op_neg,
    pos as op_pos,
    pow as op_pow,
    sub as op_sub,
    xor as op_xor,
)

from .h import H, _BinaryOperatorT, _ExpandT, _CoalesceT

__all__ = "P"


# ---- Data ----------------------------------------------------------------------------


_T = TypeVar("_T")
_GetItemT = Union[int, slice]


# ---- Classes -------------------------------------------------------------------------


class P(Sequence[H]):
    r"""
    An immutable pool (ordered sequence) of zero or more [``H`` objects][dyce.h.H]
    supporting group operations. Objects can be flattened to a single histogram, either
    explicitly via the [``h`` method][dyce.p.P.h], or by using binary arithmetic
    operations. Unary operators and the ``@`` operator result in new ``P`` objects. If
    any of the [initializer](#dyce.p.P.__init__)’s *args* parameter is an ``int``, it is
    passed to the constructor for ``H``.

    ```python
    >>> p_d6 = P(6)  # shorthand for P(H(6))
    >>> p_d6
    P(6)
    >>> -p_d6
    P(-6)

    >>> P(p_d6, p_d6)  # 2d6
    P(6, 6)
    >>> 2@p_d6  # also 2d6
    P(6, 6)

    >>> 2@(2@p_d6) == 4@p_d6
    True

    >>> P(4, P(6, P(8, P(10, P(12, P(20))))))
    P(4, 6, 8, 10, 12, 20)
    >>> sum(_.roll()) in _.h()
    True

    ```

    Arithmetic operators involving an ``int`` or another ``P`` object produces an
    [``H`` object][dyce.h.H]:

    ```python
    >>> p_d6 + p_d6
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    >>> 2 * P(8) - 1
    H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})

    ```

    Comparisons between ``P`` and [``H``][dyce.h.H] objects still work:

    ```python
    >>> 3@p_d6 == H(6) + H(6) + H(6)
    True

    ```

    Indexing selects a contained histogram:

    ```python
    >>> P(4, 6, 8)[0]
    H(4)

    ```

    Note that containers are opinionated about histogram ordering:

    ```python
    >>> P(8, 6, 4)[0] == P(8, 4, 6)[0] == H(4)
    True

    ```

    The [``h`` method][dyce.p.P.h] also allows subsets of faces to be “taken” by index
    from least to greatest. Negative indexes are supported and retain their idiomatic
    meaning. Modeling the sum of the greatest two faces of three six-sided dice
    (``3d6``) can be expressed as:

    ```python
    >>> (3@p_d6).h((-2, -1))
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

    ```
    """

    # ---- Types -----------------------------------------------------------------------

    OperandT = Union[int, "P"]

    # ---- Constructor -----------------------------------------------------------------

    def __init__(self, *args: Union[int, "P", H]) -> None:
        r"Initializer."
        super().__init__()

        def _gen_hs():
            for a in args:
                if isinstance(a, int):
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

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def parts():
            for h in self._hs:
                yield (
                    str(h._simple_init)  # pylint: disable=protected-access
                    if h._simple_init is not None  # pylint: disable=protected-access
                    else repr(h)
                )

        return "{}({})".format(self.__class__.__name__, ", ".join(parts()))

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

    def __add__(self, other: OperandT) -> H:
        return op_add(self.h(), other)

    def __radd__(self, other: int) -> H:
        return op_add(other, self.h())

    def __sub__(self, other: OperandT) -> H:
        return op_sub(self.h(), other)

    def __rsub__(self, other: int) -> H:
        return op_sub(other, self.h())

    def __mul__(self, other: OperandT) -> H:
        return op_mul(self.h(), other)

    def __rmul__(self, other: int) -> H:
        return op_mul(other, self.h())

    def __matmul__(self, other: int) -> "P":
        if not isinstance(other, int):
            return NotImplemented
        elif other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return P(*chain.from_iterable(repeat(self._hs, other)))

    def __rmatmul__(self, other: int) -> "P":
        return self.__matmul__(other)

    def __floordiv__(self, other: OperandT) -> H:
        return op_floordiv(self.h(), other)

    def __rfloordiv__(self, other: int) -> H:
        return op_floordiv(other, self.h())

    def __mod__(self, other: OperandT) -> H:
        return op_mod(self.h(), other)

    def __rmod__(self, other: int) -> H:
        return op_mod(other, self.h())

    def __pow__(self, other: OperandT) -> H:
        return op_pow(self.h(), other)

    def __rpow__(self, other: int) -> H:
        return op_pow(other, self.h())

    def __and__(self, other: OperandT) -> H:
        return op_and(self.h(), other)

    def __rand__(self, other: int) -> H:
        return op_and(other, self.h())

    def __xor__(self, other: OperandT) -> H:
        return op_xor(self.h(), other)

    def __rxor__(self, other: int) -> H:
        return op_xor(other, self.h())

    def __or__(self, other: OperandT) -> H:
        return op_or(self.h(), other)

    def __ror__(self, other: int) -> H:
        return op_or(other, self.h())

    def __neg__(self) -> "P":
        return P(*(op_neg(h) for h in self._hs))

    def __pos__(self) -> "P":
        return P(*(op_pos(h) for h in self._hs))

    def __abs__(self) -> "P":
        return P(*(op_abs(h) for h in self._hs))

    # ---- Methods ---------------------------------------------------------------------

    def h(self, key: Optional[Union[_GetItemT, Iterable[_GetItemT]]] = None) -> H:
        r"""
        When provided no arguments, ``h`` combines (or “flattens”) contained
        histograms:

        ```python
        >>> (2@P(6)).h()
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        ```

        If the optional *key* parameter is provided, ``h`` sums subsets of faces
        selected by *key*. *key* can be an ``int``, a ``slice``, or an iterable of
        ``int``s and ``slice``s.

        All outcomes are enumerated. For each outcome, faces are ordered from least
        (index ``0``) to greatest (index ``-1`` or ``len(self)``). Modeling taking the
        greatest of two six-sided dice can be expressed as:

        ```python
        >>> (2@P(6)).h(-1)
        H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
        >>> print(_.format(width=65))
        avg |    4.47
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
        >>> p_6d6.h((5, 3, 1)) == every_other_d6
        True
        >>> p_6d6.h(range(1, 6, 2)) == every_other_d6
        True
        >>> p_6d6.h(i for i in range(0, 6) if i % 2 == 1) == every_other_d6
        True
        >>> p_6d6.h({1, 3, 5}) == every_other_d6
        True

        ```

        Modeling the sum of the greatest two and least two faces of ten four-sided dice
        (``10d4``) can be expressed as:

        ```python
        >>> (10@P(4)).h((slice(2), slice(-2, None)))
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

        ```
        """
        if key is None:
            if self._hs:
                hs_sum = sum(self._hs)
            else:
                hs_sum = H(())

            return cast(H, hs_sum)
        else:
            if isinstance(key, int):
                keys: Iterable[_GetItemT] = (key,)
            elif isinstance(key, ABCIterable):
                keys = tuple(key)
            elif isinstance(key, slice):
                keys = (key,)
            else:
                return NotImplemented

            return H(_select_and_sum_faces(self.rolls_with_counts(), keys))

    def lt(
        self,
        other: OperandT,
    ) -> H:
        r"""
        Shorthand for ``self.h().lt(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.lt``][dyce.h.H.lt].
        """
        return self.h().lt(other)

    def le(
        self,
        other: OperandT,
    ) -> H:
        r"""
        Shorthand for ``self.h().le(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.le``][dyce.h.H.le].
        """
        return self.h().le(other)

    def eq(
        self,
        other: OperandT,
    ) -> H:
        r"""
        Shorthand for ``self.h().eq(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.eq``][dyce.h.H.eq].
        """
        return self.h().eq(other)

    def ne(
        self,
        other: OperandT,
    ) -> H:
        r"""
        Shorthand for ``self.h().ne(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.ne``][dyce.h.H.ne].
        """
        return self.h().ne(other)

    def gt(
        self,
        other: OperandT,
    ) -> H:
        r"""
        Shorthand for ``self.h().gt(other)``. See the [``h`` method][dyce.p.P.h] and
        [``H.gt``][dyce.h.H.gt].
        """
        return self.h().gt(other)

    def ge(
        self,
        other: OperandT,
    ) -> H:
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

    def explode(
        self,
        max_depth: int = 1,
    ) -> H:
        r"""
        Shorthand for ``self.h().explode(max_depth)``. See the [``h`` method][dyce.p.P.h]
        and [``H.explode``][dyce.h.H.explode].
        """
        return self.h().explode(max_depth)

    def substitute(
        self,
        expand: _ExpandT,
        coalesce: Optional[_CoalesceT] = None,
        max_depth: int = 1,
    ) -> H:
        r"""
        Shorthand for ``self.h().substitute(expand, coalesce, max_depth)``. See the
        [``h`` method][dyce.p.P.h] and [``H.substitute``][dyce.h.H.substitute].
        """
        return self.h().substitute(expand, coalesce, max_depth)

    def within(self, lo: int, hi: int, other: OperandT = 0) -> H:
        r"""
        Shorthand for ``self.h().within(lo, hi, other)``. See the [``h`` method][dyce.p.P.h]
        and [``H.within``][dyce.h.H.within].
        """
        return self.h().within(lo, hi, other)

    def roll(self) -> Tuple[int, ...]:
        r"""
        Returns (weighted) random faces from contained histograms.
        """
        return tuple(h.roll() for h in self._hs)

    def rolls_with_counts(self) -> Iterator[Tuple[Tuple[int, ...], int]]:
        r"""
        Returns an iterator that yields 2-tuples (pairs) that, collectively, enumerate all
        possible outcomes for the pool. The first item in the 2-tuple is a sorted
        sequence of the faces for a distinct roll. The second is the count for that
        roll.

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
        {avg: 0.00, 0: 99.92%, 1:  0.08%}

        ```

        Note that, in the general case, rolls can appear more than once, and there are
        no guarantees about their order.

        ```python
        >>> list(P(H(2), H(3)).rolls_with_counts())
        [((1, 1), 1), ((1, 2), 1), ((1, 3), 1), ((1, 2), 1), ((2, 2), 1), ((2, 3), 1)]

        ```

        However, if the pool is homogeneous (meaning it only contains identical
        histograms), faces are not repeated and are presented in order.

        ```python
        >>> list((2@P(H((-1, 0, 1)))).rolls_with_counts())
        [((-1, -1), 1), ((-1, 0), 2), ((-1, 1), 2), ((0, 0), 1), ((0, 1), 2), ((1, 1), 1)]

        ```

        Enumeration is substantially more efficient for homogeneous pools than
        heterogeneous ones. This is because homogeneous pools can be enumerated using
        combinations with replacements, but heterogeneous pools require computing the
        Cartesian product. This implementation attempts to optimize the latter by
        breaking pools into homogeneous groups before computing the product of those
        sub-results. This approach allows homogeneous pools to be ordered without
        duplicates, but heterogeneous ones provide no such guarantees.
        """
        groups = tuple((h, sum(1 for _ in hs)) for h, hs in groupby(self._hs))

        if len(groups) == 1:
            # Optimization to use _rolls_with_counts_for_n_uniform_histograms directly if
            # there's only one group; roughly 15% time savings based on cursory
            # performance analysis
            h, n = groups[0]

            return _rolls_with_counts_for_n_uniform_histograms(h, n)
        else:
            return _rolls_with_counts_for_nonuniform_histograms(groups)


# ---- Functions -----------------------------------------------------------------------


def _coalesce_replace(h: H, face: int) -> H:  # pylint: disable=unused-argument
    return h


def _getitems(sequence: Sequence[_T], keys: Iterable[_GetItemT]) -> Iterator[_T]:
    for key in keys:
        if isinstance(key, int):
            yield op_getitem(sequence, key)
        else:
            for val in op_getitem(sequence, key):
                yield val


def _rolls_with_counts_for_n_uniform_histograms(
    h: Mapping[int, int],
    n: int,
) -> Iterator[Tuple[Tuple[int, ...], int]]:
    r"""
    Given a group of *n* identical histograms *h*, returns an iterator that yields
    ordered 2-tuples (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts].

    This is intended to be more efficient at enumerating faces and counts than merely
    computing the Cartesian product. Instead, it computes combinations with
    replacements, and computes the number of permutations with repetitions for each
    combination, leveraging the
    [*multinomial coefficient*](https://en.wikipedia.org/wiki/Permutation#Permutations_of_multisets):

    ${{n} \choose {{{k}_{1}},{{k}_{2}},\ldots,{{k}_{m}}}} = {\frac {{n}!} {{{k}_{1}}! {{k}_{2}}! \cdots {{k}_{m}}!}}$

    Consider ``n@P(H(m))``. Enumerating combinations with replacements would yield all
    unique (unordered) rolls:

    ``((1, 1, …, 1), (1, 1, …, 2), …, (1, 1, …, m), (2, 2, …, 2), …, (m - 1, m, m), (m, m, m))``

    To determine the count for a particular roll ``(a, b, …, n)``, we compute the
    multinomial coefficient for that roll and multiply by the scalar ``h[a] * h[b] * … *
    h[n]``.

    By taking all faces, we can confirm equivalence to our sum operation:

    ```python
    >>> d = H((2, 3, 3, 4, 4, 5))
    >>> (4@P(d)).h(slice(None)) == d + d + d + d
    True

    ```

    (See [this](https://www.lucamoroni.it/the-dice-roll-sum-problem/) for an excellent
    explanation.)
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

        yield sorted_faces_for_roll, count_scalar * multinomial_coefficient_numerator // multinomial_coefficient_denominator


def _rolls_with_counts_for_nonuniform_histograms(
    h_groups: Iterable[Tuple[Mapping[int, int], int]]
) -> Iterator[Tuple[Tuple[int, ...], int]]:
    r"""
    Given an iterable of histogram/count pairs, returns an iterator that yields 2-tuples
    (pairs) per [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts].

    The use of histogram/count pairs for *h_groups* is acknowledged as awkward, but
    intended, since its implementation is optimized to leverage
    ``_rolls_with_counts_for_n_uniform_histograms``.
    """
    for v in product(
        *(_rolls_with_counts_for_n_uniform_histograms(h, n) for h, n in h_groups)
    ):
        # It's possible v is () if h_groups is empty; see
        # https://stackoverflow.com/questions/3154301/ for a detailed discussion
        if v:
            rolls_by_group: Iterable[Iterable[int]]
            counts_by_group: Iterable[int]
            rolls_by_group, counts_by_group = zip(*v)
            sorted_faces_for_roll = tuple(sorted(chain(*rolls_by_group)))
            total_count = reduce(op_mul, counts_by_group)

            yield sorted_faces_for_roll, total_count


def _select_and_sum_faces(
    rolls_with_counts_iter: Iterator[Tuple[Sequence[int], int]],
    keys: Iterable[_GetItemT],
) -> Iterator[Tuple[int, int]]:
    for (
        sorted_faces_for_roll,
        roll_count,
    ) in rolls_with_counts_iter:
        selected_faces = tuple(_getitems(sorted_faces_for_roll, keys))

        if selected_faces:
            yield sum(selected_faces), roll_count


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

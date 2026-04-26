# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

import operator
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from functools import lru_cache
from itertools import chain, groupby, product, repeat, starmap
from math import comb, gcd, prod
from typing import (
    Any,
    Never,
    SupportsIndex,
    SupportsInt,
    TypeVar,
    cast,
    overload,
)

from .h import H, aggregate_weighted, sum_h
from .hable import HableOpsMixin
from .types import (
    GetItemT,
    Sentinel,
    SentinelT,
    getitems,
    lossless_int,
    natural_key,
    nobeartype,
)

__all__ = ("P", "RollCountT", "RollProbT", "RollT")

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")

RollT = tuple[_T, ...]
RollCountT = tuple[RollT[_T], int]
RollProbT = tuple[RollT[_T], int, int]


@dataclass(frozen=True, slots=True)
class _SelectionEmpty:
    r"""
    Returned by [`_analyze_selection`][dyce.p._analyze_selection] when *which* selects zero positions.
    """


@dataclass(frozen=True, slots=True)
class _SelectionUniform:
    r"""
    Returned by [`_analyze_selection`][dyce.p._analyze_selection] when *which* selects every position exactly *times* times (and nothing else).
    """

    times: int


@dataclass(frozen=True, slots=True)
class _SelectionPrefix:
    r"""
    Returned by [`_analyze_selection`][dyce.p._analyze_selection] when *which* selects only contiguous positions from the low (left) end to *max_index* positions `#!math \left[ 0 .. max\_index \right)`.
    """

    max_index: int  # positive; positions [0..max_index)


@dataclass(frozen=True, slots=True)
class _SelectionSuffix:
    r"""
    Returned by [`_analyze_selection`][dyce.p._analyze_selection] when *which* selects only contiguous positions from *min_index* to the high (right) end `#!math \left[ min\_index .. n \right)`.
    """

    min_index: int  # negative; positions [min_index..n)


@dataclass(frozen=True, slots=True)
class _SelectionExtremes:
    r"""
    Returned by [`_analyze_selection`][dyce.p._analyze_selection] when *which* selects exactly the *lo* lowest and *hi* highest sorted positions and nothing else.
    Both values are positive; together they are strictly fewer than the pool size (so there is at least one unselected interior position).
    """

    lo: int  # positions [0..lo)
    hi: int  # positions [n-hi..n)


_SelectionResult = (
    _SelectionEmpty
    | _SelectionUniform
    | _SelectionPrefix
    | _SelectionSuffix
    | _SelectionExtremes
    | None
)


class P(Sequence[H[_T_co]], HableOpsMixin[_T_co]):
    r"""
    An immutable pool (ordered sequence) supporting group operations for zero or more [`H` objects][dyce.H] (provided or created from the [initializer][dyce.P.__init__]’s *args* parameter).

        >>> from dyce import H, P
        >>> p_d6 = P(6)  # shorthand for P(H(6))
        >>> p_d6
        P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))

    <!-- -->

        >>> P(p_d6, p_d6)  # 2d6
        2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))
        >>> 2 @ p_d6  # also 2d6
        2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))
        >>> 2 @ (2 @ p_d6) == 4 @ p_d6
        True

    <!-- -->

        >>> p = P(4, P(6, P(8, P(10, P(12, P(20))))))
        >>> p == P(4, 6, 8, 10, 12, 20)
        True

    This class implements the [`HableT` protocol][dyce.HableT] and derives from the [`HableOpsMixin` class][dyce.HableOpsMixin], which means it can be “flattened” into a single histogram, either explicitly via the [`h` method][dyce.P.h], or implicitly by using arithmetic operations.

        >>> -p_d6
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})

    <!-- -->

        >>> p_d6 + p_d6
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

    <!-- -->

        >>> 2 * P(8) - 1
        H({1: 1, 3: 1, 5: 1, 7: 1, 9: 1, 11: 1, 13: 1, 15: 1})

    To perform arithmetic on individual [`H` objects][dyce.H] in a pool without flattening, use the [`apply_to_each_h`][dyce.P.apply_to_each_h] method.

        >>> import operator
        >>> P(4, 6, 8).apply_to_each_h(operator.neg)
        P(H({-8: 1, -7: 1, -6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1}), H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1}), H({-4: 1, -3: 1, -2: 1, -1: 1}))

    <!-- -->

        >>> P(4, 6).apply_to_each_h(operator.pow, 2)
        P(H({1: 1, 4: 1, 9: 1, 16: 1}), H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1}))

    <!-- -->

        >>> P(4, 6).apply_to_each_h(
        ...     lambda h_outcome, other_outcome: operator.pow(other_outcome, h_outcome),
        ...     2,
        ... )
        P(H({2: 1, 4: 1, 8: 1, 16: 1}), H({2: 1, 4: 1, 8: 1, 16: 1, 32: 1, 64: 1}))

    Comparisons with [`H` objects][dyce.H] work as expected.

        >>> 3 @ p_d6 == H(6) + H(6) + H(6)
        True

    Indexing selects a contained histogram.

        >>> P(4, 6, 8)[0]
        H({1: 1, 2: 1, 3: 1, 4: 1})

    Note that pools are opinionated about ordering.

        >>> P(8, 6, 4)
        P(H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}))
        >>> P(8, 6, 4)[0] == P(8, 4, 6)[0] == H(4)
        True
    """

    __slots__ = (
        "_hash",
        "_hs",
        "_total",
    )

    # ---- Initializer -----------------------------------------------------------------

    @overload
    def __init__(self: "P[Never]", *init_vals: Never) -> None: ...
    @overload
    def __init__(self: "P[int]", *init_vals: int) -> None: ...
    @overload
    def __init__(self: "P[_T]", *init_vals: "P[_T] | H[_T]") -> None: ...
    @overload
    def __init__(self: "P[int | _T]", *init_vals: "P[_T] | H[_T] | int") -> None: ...
    def __init__(
        self,
        *init_vals: Any,
    ) -> None:
        r"""Constructor."""
        super().__init__()

        def _gen_hs() -> Iterator[H[_T_co]]:
            for init_val in init_vals:
                if isinstance(init_val, H):
                    yield init_val
                elif isinstance(init_val, P):
                    yield from init_val._hs  # noqa: SLF001
                else:
                    yield H(init_val)

        hs = [h for h in _gen_hs() if h]
        try:
            hs.sort(key=lambda h: tuple(h.items()))
        except TypeError:
            # For Hs whose outcomes don't support direct comparisons (e.g. symbolic
            # types)
            hs.sort(key=lambda h: natural_key(h.items()))
        self._hs: tuple[H[_T_co], ...] = tuple(hs)
        self._hash: int | None = None
        self._total: int | None = None

    # ---- Overrides -------------------------------------------------------------------

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((type(self), *self._hs))
        return self._hash

    def __repr__(self) -> str:
        group_counters: dict[H[_T_co], int] = {}
        for h, hs in groupby(self):
            group_counters[h] = sum(1 for _ in hs)

        def _n_at(h: H[_T_co], n: int) -> str:
            return repr(h) if n == 1 else f"{n}@{type(self).__name__}({h!r})"

        if len(group_counters) == 1:
            h, n = next(iter(group_counters.items()))
            return f"{type(self).__name__}({_n_at(h, 1)})" if n == 1 else _n_at(h, n)
        else:
            inner = ", ".join(starmap(_n_at, group_counters.items()))
            return f"{type(self).__name__}({inner})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, P):
            return self._hs == other._hs
        return NotImplemented

    # ---- Sequence abstract methods ---------------------------------------------------

    @overload
    def __getitem__(self: "P[_T]", key: SupportsIndex) -> H[_T]: ...
    @overload
    def __getitem__(self: "P[_T]", key: slice) -> "P[_T]": ...
    @nobeartype  # TODO(posita): <https://github.com/beartype/beartype/issues/636>
    def __getitem__(self: "P[_T]", key: SupportsIndex | slice) -> "P[_T] | H[_T]":
        if isinstance(key, slice):
            return P(*self._hs[key])
        return self._hs[operator.index(key)]

    def __iter__(self: "P[_T]") -> Iterator[H[_T]]:
        yield from self._hs

    def __len__(self) -> int:
        return len(self._hs)

    # ---- Operators -------------------------------------------------------------------

    def __matmul__(self: "P[_T]", other: SupportsInt) -> "P[_T]":
        try:
            n = lossless_int(other)
        except (TypeError, ValueError):
            return NotImplemented
        if n < 0:
            return NotImplemented
        return P(*chain.from_iterable(repeat(self, n)))

    def __rmatmul__(self: "P[_T]", other: SupportsInt) -> "P[_T]":
        return self.__matmul__(other)

    # ---- Properties ------------------------------------------------------------------

    @property
    def total(self) -> int:
        r"""
        Equivalent to `#!python prod(h.total for h in self)`.
        Consistent with the empty product, this is `#!python 1` for an empty pool.
        The result is cached to avoid redundant computation with multiple accesses.
        """
        if self._total is None:
            self._total = prod(h.total for h in self._hs)
        return self._total

    # ---- Methods ---------------------------------------------------------------------

    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T], _ResultT],
        *,
        apply_to_each: bool = False,
    ) -> "P[_ResultT]": ...
    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: "H[_OtherT]",
        *,
        apply_to_each: bool = False,
    ) -> "P[_ResultT]": ...
    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: _OtherT,
        *,
        apply_to_each: bool = False,
    ) -> "P[_ResultT]": ...
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T], _ResultT] | Callable[[_T, _OtherT], _ResultT],
        other: "H[_OtherT] | _OtherT | SentinelT" = Sentinel,
        *,
        apply_to_each: bool = False,
    ) -> "P[_ResultT]":
        r"""
        Return a new [`P`][dyce.P] by applying *func* to each histogram via its [`H.apply`][dyce.H.apply] method.
        If *other* is provided, *func* should have two parameters, otherwise it should have one.

        *func* is assumed to be idempotent, meaning that for each distinct histogram `#!python h`, calling `#!python h.apply(func, other)` should return the same result regardless of context.
        This allows for *func* to be applied only once for each distinct `#!python H` in `#!python P`, and the result reused.
        If this is not desired, provide `#!python True` for *apply_to_each* to ensure that *func* is actually run on each individual histogram.
        """

        def _gen_by_group() -> Iterator[tuple[H[_T], int]]:
            for h, hs in groupby(self):
                yield h, sum(1 for _ in hs)

        def _gen_apply_to_each() -> Iterator[tuple[H[_T], int]]:
            yield from ((h, 1) for h in self)

        def _gen_hs() -> Iterator[H[_ResultT]]:
            for h, count in _gen_apply_to_each() if apply_to_each else _gen_by_group():
                new_h = h.apply(func, other)  # type: ignore[arg-type] # ty: ignore[no-matching-overload]
                yield from (new_h for _ in range(count))

        return P(*_gen_hs())

    def apply_to_each_roll(
        self: "P[_T]",
        func: Callable[[RollT[_T]], H[_ResultT] | _ResultT],
        *which: GetItemT,
    ) -> H[_ResultT]:
        r"""
        TODO(posita): Fill this out.
        """
        return cast(
            "H[_ResultT]",
            aggregate_weighted(
                (func(roll), count) for roll, count in self.rolls_with_counts(*which)
            ),
        )

    # TODO(posita): # noqa: TD003 - Use CanAdd here
    def h(self: "P[_T]", *which: GetItemT) -> H[_T]:
        r"""
        Combines (or “flattens”) all contained histograms into a single [`H`][dyce.H] in accordance with the [`HableT` protocol][dyce.HableT].

            >>> (2 @ P(6)).h()
            H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        When on or more optional *which* identifiers is provided, this is roughly equivalent to `#!python H((sum(roll), count) for roll, count in self.rolls_with_counts(*which))` with some short-circuit optimizations.
        Identifiers can be `#!python int`s or `#!python slice`s, and can be mixed.

        Taking the greatest of two six-sided dice can be modeled as:

            >>> p_2d6 = 2 @ P(6)
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

        Taking the greatest two and least two faces of ten four-sided dice (`10d4`) can be modeled as:

            >>> p_10d4 = 10 @ P(4)
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

        Taking all outcomes exactly once is equivalent to summing the histograms in the pool.

            >>> d6 = H(6)
            >>> d6avg = H((2, 3, 3, 4, 4, 5))
            >>> p = 2 @ P(d6, d6avg)
            >>> p.h(slice(None)) == p.h() == d6 + d6 + d6avg + d6avg
            True
        """
        if not which:
            return sum_h(self)
        n = len(self)
        i = _analyze_selection(n, which)
        # Optimization for when each and every position is selected the same number of times
        if n and isinstance(i, _SelectionUniform):
            try:
                # This optimization assumes outcomes support multiplication with native
                # ints while retaining their type ...
                return sum_h(self) * i.times  # type: ignore[operator] # ty: ignore[unsupported-operator]
            except TypeError:
                # ... but if we get into trouble, fall through to enumerating via rolls_with_counts
                pass
        return H.from_counts(
            # This slightly esoteric use of sum() is to avoid an attempt to 0 to
            # outcomes, which is sum()'s default behavior. At worst, this results in
            # more accurate error messages where outcomes don't support addition at all.
            (sum(roll[1:], start=roll[0]), count)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
            for roll, count in self.rolls_with_counts(*which)
        )

    def roll(self: "P[_T]") -> RollT[_T]:
        r"""
        Returns (weighted) random outcomes from contained histograms.

        !!! note "On ordering"

            This method “works” (i.e., falls back to a “natural” ordering of string representations) for outcomes whose relative values cannot be known (e.g., symbolic expressions).
            This is deliberate to allow random roll functionality where symbolic resolution is not needed or will happen later.
        """
        roll = [h.roll() for h in self]
        try:
            roll.sort()  # pyrefly: ignore[bad-specialization] # pyright: ignore[reportCallIssue] # ty: ignore[invalid-argument-type]
        except TypeError:
            roll.sort(key=natural_key)
        return tuple(roll)

    def rolls_with_counts(self: "P[_T]", *which: GetItemT) -> Iterator[RollCountT[_T]]:
        r"""
        Returns an iterator yielding `#!python (roll, count)` pairs that collectively enumerate all distinct rolls of the pool.
        Each *roll* is a sorted tuple of outcomes (least to greatest); *count* is the number of ways that roll occurs.

        If one or more *which* arguments are provided (as `#!python SupportsIndex` or `#!python slice` values), each roll is filtered to the selected positions before yielding.

            >>> from dyce import H, P
            >>> p_2d6 = 2 @ P(6)
            >>> H.from_counts(
            ...     (sum(roll), count) for roll, count in p_2d6.rolls_with_counts()
            ... ) == p_2d6.h()
            True

        *which* selects by sorted position. To take the highest outcome from 3d6:

            >>> p_3d6 = 3 @ P(6)
            >>> H.from_counts(
            ...     (roll[0], count) for roll, count in p_3d6.rolls_with_counts(-1)
            ... )
            H({1: 1, 2: 7, 3: 19, 4: 37, 5: 61, 6: 91})

        Multiple *which* arguments are aggregated:

            >>> lo_hi_from_all_3d6_rolls = sorted(
            ...     p_3d6.rolls_with_counts(0, -1)  # selects lowest and highest of 3d6
            ... )
            >>> lo_hi_from_all_3d6_rolls
            [((1, 1), 1), ((1, 2), 3), ((1, 2), 3), ..., ((5, 6), 3), ((5, 6), 3), ((6, 6), 1)]
            >>> lo_hi_from_all_3d6_rolls == sorted(
            ...     ((r[0], r[-1]), c) for r, c in p_3d6.rolls_with_counts()
            ... )
            True

        Collectively selecting everything with no overlaps is the same as the default.

            >>> p_2df = 2 @ P(H((-1, 0, 1)))
            >>> p_2df_rolls = sorted(p_2df.rolls_with_counts())
            >>> p_2df_rolls
            [((-1, -1), 1), ((-1, 0), 2), ((-1, 1), 2), ((0, 0), 1), ((0, 1), 2), ((1, 1), 1)]
            >>> sorted(p_2df.rolls_with_counts(0, 1)) == p_2df_rolls
            True
            >>> sorted(
            ...     p_2df.rolls_with_counts(slice(None, 1), slice(1, None))
            ... ) == p_2df_rolls
            True

        This method may yield the same roll more than once under certain conditions (e.g., non-contiguous *which* selections, where heterogeneous pools produce similar rolls for each group ordering):

            >>> sorted((3 @ P(H(2))).rolls_with_counts(0, -1))
            [((1, 1), 1), ((1, 2), 3), ((1, 2), 3), ((2, 2), 1)]
            >>> sorted(P(H(2), H(3)).rolls_with_counts())
            [((1, 1), 1), ((1, 2), 1), ((1, 2), 1), ((1, 3), 1), ((2, 2), 1), ((2, 3), 1)]

        No rolls will be produced with empty `#!python P` objects or where *which* selects no positions.

            >>> sorted(P(6).rolls_with_counts(slice(6, 7)))
            []
            >>> sorted(P().rolls_with_counts())
            []
        """
        n = len(self)
        if not which:
            sel: _SelectionResult = _SelectionUniform(times=1)
        else:
            sel = _analyze_selection(n, which)
        rolls_with_counts_iter: Iterable[RollCountT[_T | _MinFill | _MaxFill]]
        # Short-circuit: empty selection or empty pool
        if isinstance(sel, _SelectionEmpty) or n == 0:
            return
        groups = tuple((h, sum(1 for _ in hs)) for h, hs in groupby(self))
        # The fast path inclusion-exclusion algorithm in _rwc_heterogeneous_extremes
        # only supports (lo=1, hi=1). Otherwise, fall through and convert selection to
        # the integer k hint consumed by other lower-level functions:
        #
        # * positive k - take k from left (prefix)
        # * negative k - take k from right (suffix)
        # * None - full enumeration (uniform, extremes fallback, or arbitrary)
        if (
            isinstance(sel, _SelectionExtremes)
            and len(groups) > 1
            and sel.lo == 1
            and sel.hi == 1
        ):
            yield from _rwc_heterogeneous_extremes(groups, sel.lo, sel.hi)
            return
        elif isinstance(sel, _SelectionPrefix):
            k: int | None = sel.max_index if sel.max_index >= 0 else n + sel.max_index
        elif isinstance(sel, _SelectionSuffix):
            k = sel.min_index if sel.min_index < 0 else sel.min_index - n
        else:
            k = None
        if len(groups) == 1:
            h, hn = groups[0]
            assert hn == n
            if k is not None and abs(k) < n:
                rolls_with_counts_iter = _rwc_homogeneous_n_h_using_partial_selection(
                    n, h, k=k, fill=cast("_T", 0)
                )
            else:
                rolls_with_counts_iter = _rwc_homogeneous_n_h_using_partial_selection(
                    n, h, k=n
                )
        else:
            rolls_with_counts_iter = _rwc_heterogeneous_h_groups(groups, k)

        for sorted_outcomes_for_roll, roll_count in rolls_with_counts_iter:
            if which:
                taken_outcomes: RollT[_T] = cast(
                    "RollT[_T]", tuple(getitems(sorted_outcomes_for_roll, which))
                )
            else:
                taken_outcomes = cast("RollT[_T]", sorted_outcomes_for_roll)
            yield taken_outcomes, roll_count


# ---- Helpers -------------------------------------------------------------------------


class _MinFill:
    r"""
    Sentinel that compares less than any real outcome; used to pad heterogeneous rolls on the low end when a partial-right selection leaves unfilled low positions.
    """

    __slots__ = ()

    def __hash__(self) -> int:
        return hash(_MinFill)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __lt__(self, other: object) -> bool:
        return not isinstance(other, _MinFill)

    def __le__(self, _other: object) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _MinFill)

    def __ge__(self, other: object) -> bool:
        return isinstance(other, _MinFill)

    def __gt__(self, _other: object) -> bool:
        return False


class _MaxFill:
    r"""
    Sentinel that compares greater than any real outcome; used to pad heterogeneous rolls on the high end when a partial-left selection leaves unfilled high positions.
    """

    __slots__ = ()

    def __hash__(self) -> int:
        return hash(_MaxFill)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __lt__(self, _other: object) -> bool:
        return False

    def __le__(self, other: object) -> bool:
        return isinstance(other, _MaxFill)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _MaxFill)

    def __gt__(self, other: object) -> bool:
        return not isinstance(other, _MaxFill)

    def __ge__(self, _other: object) -> bool:
        return True


_MIN_FILL = _MinFill()
_MAX_FILL = _MaxFill()


def _analyze_selection(n: int, which: Iterable[GetItemT]) -> "_SelectionResult":
    r"""
    Examines the selection *which* as applied to the values `#!python range(n)` and returns one of:

    - [`_SelectionEmpty`][dyce.p._SelectionEmpty]: *which* selects zero positions
    - [`_SelectionUniform(times)`][dyce.p._SelectionUniform]: *which* selects every position exactly *times* times
    - [`_SelectionPrefix(max_index)`][dyce.p._SelectionPrefix]: *which* selects positions `#!python [0..max_index)` only
    - [`_SelectionSuffix(min_index)`][dyce.p._SelectionSuffix]: *which* selects positions `#!python [min_index..n)` only
    - [`_SelectionExtremes(lo, hi)`][dyce.p._SelectionExtremes]: *which* selects exactly the *lo* lowest and *hi* highest positions with at least one unselected interior position
    - `#!python None`: any other (arbitrary) selection
    """
    indexes = tuple(range(n))
    counts_by_index: Counter[int] = Counter(getitems(indexes, which))
    found_indexes = set(counts_by_index)
    if not found_indexes:
        return _SelectionEmpty()

    missing_indexes = set(indexes) - found_indexes
    distinct_counts = set(counts_by_index.values())
    min_index = min(found_indexes)
    max_index = max(found_indexes) + 1
    if max_index - min_index == n:
        if not missing_indexes and len(distinct_counts) == 1:
            return _SelectionUniform(times=distinct_counts.pop())
        elif len(distinct_counts) == 1:
            # Check for lo-from-left + hi-from-right pattern with a gap in the middle.
            # Because max_index - min_index == n we know min_index == 0 and max_index ==
            # n, so positions 0 and n-1 are both selected.
            sorted_found = sorted(found_indexes)
            lo = 0
            while lo < len(sorted_found) and sorted_found[lo] == lo:
                lo += 1
            hi = 0
            while hi < len(sorted_found) and sorted_found[-(hi + 1)] == n - 1 - hi:
                hi += 1
            if lo + hi == len(sorted_found):
                return _SelectionExtremes(lo=lo, hi=hi)
        return None
    elif min_index > n - max_index:
        return _SelectionSuffix(min_index=min_index - n)
    else:
        return _SelectionPrefix(max_index=max_index)


@lru_cache(maxsize=2048)
def _selected_distros_memoized(
    h: H[_T],
    n: int,
    k: int,
    *,
    from_right: bool,
) -> tuple[RollProbT[_T], ...]:
    r"""
    Memoized adaptation of `Ilmari Karonen’s optimization <https://rpg.stackexchange.com/a/166663/71245>`_ that yields three-tuples of `#!python (outcomes, numerator, denominator)` for selecting *k* outcomes from *n* rolls of *h*.
    `#!python numerator / denominator` is the probability of that specific outcome selection.

    Uses integer arithmetic throughout to avoid `#!python Fraction` overhead.
    """

    def _gen() -> Iterator[RollProbT]:
        if len(h) <= 1:
            yield tuple(h) * k, 1, 1
        else:
            this_total = h.total**n
            try:
                this_outcome = max(h) if from_right else min(h)  # type: ignore[type-var]
            except TypeError:
                this_outcome = (
                    max(h, key=natural_key) if from_right else min(h, key=natural_key)
                )
            c_outcome = h[this_outcome]
            rest_total = h.total - c_outcome
            next_h: H[_T] = H({o: c for o, c in h.items() if o != this_outcome})
            cumulative_nmr8r = 0

            for i in range(k + 1):
                head = (this_outcome,) * i
                if i < k:
                    head_count = comb(n, i) * c_outcome**i * rest_total ** (n - i)
                    cumulative_nmr8r += head_count
                    for tail, tail_nmr8r, tail_dnmn8r in _selected_distros_memoized(
                        next_h, n - i, k - i, from_right=from_right
                    ):
                        whole = tail + head if from_right else head + tail
                        nmr8r = head_count * tail_nmr8r
                        dnmn8r = this_total * tail_dnmn8r
                        g = gcd(nmr8r, dnmn8r)
                        yield whole, nmr8r // g, dnmn8r // g
                else:
                    nmr8r = this_total - cumulative_nmr8r
                    g = gcd(nmr8r, this_total)
                    yield head, nmr8r // g, this_total // g

    return tuple(_gen())


def _rwc_homogeneous_n_h_using_partial_selection(
    n: int,
    h: H[_T],
    k: int,
    fill: _T | None = None,
) -> Iterator[RollCountT[_T]]:
    r"""
    Yields `#!python (roll, count)` pairs for selecting *k* outcomes from *n* rolls of *h*.
    If *fill* is not _NoVal `#!python None` and `#!python abs(k) < n`, unselected positions in each roll are padded with *fill* to preserve positional indexing.
    """
    from_right = k < 0
    k = abs(k)
    if k == 0 or k > n:
        return  # pragma: no cover
    total_count = h.total**n
    for outcomes, prob_nmr8r, prob_dnmn8r in _selected_distros_memoized(
        h, n, k, from_right=from_right
    ):
        count = total_count * prob_nmr8r // prob_dnmn8r
        if fill is not None:
            outcomes = (  # noqa: PLW2901
                (fill,) * (n - k) + outcomes
                if from_right
                else outcomes + (fill,) * (n - k)
            )
        yield outcomes, count


@overload
def _rwc_heterogeneous_h_groups(
    h_groups: Iterable[tuple[H[_T], int]],
    k: None,
) -> Iterator[RollCountT[_T]]: ...
@overload
def _rwc_heterogeneous_h_groups(
    h_groups: Iterable[tuple[H[_T], int]],
    k: int,
) -> Iterator[RollCountT[_T | _MinFill | _MaxFill]]: ...
def _rwc_heterogeneous_h_groups(
    h_groups: Iterable[tuple[H[_T], int]],
    k: int | None,
) -> Iterator[RollCountT[_T | _MinFill | _MaxFill]]:
    r"""
    Given an iterable of `#!python (histogram, count)` pairs, yields `#!python (roll, count)` pairs for the Cartesian product of all groups.
    When *k* is not `#!python None`, it signals which outcomes are selected, enabling the homogeneous partial-selection optimization within each group.
    """
    groups = list(h_groups)
    total_n = sum(gn for _, gn in groups)
    for v in product(
        *(
            _rwc_homogeneous_n_h_using_partial_selection(
                gn, gh, k if k is not None and abs(k) < gn else gn
            )
            for gh, gn in groups
        )
    ):
        # It's possible v is () if h_groups is empty. See
        # <https://stackoverflow.com/questions/3154301/> for a detailed discussion.
        if not v:
            continue  # pragma: no cover

        rolls_by_group, counts_by_group = zip(*v, strict=True)
        total_count = prod(counts_by_group)
        sorted_roll_list = list(chain(*rolls_by_group))
        try:
            sorted_roll_list.sort()
        except TypeError:
            sorted_roll_list.sort(key=natural_key)
        sorted_roll = tuple(sorted_roll_list)
        if k is not None:
            if k < 0:
                sorted_roll = (_MIN_FILL,) * (total_n - len(sorted_roll)) + sorted_roll
            else:
                sorted_roll = sorted_roll + (_MAX_FILL,) * (total_n - len(sorted_roll))
        yield sorted_roll, total_count


def _rwc_heterogeneous_extremes(  # noqa: C901
    groups: Iterable[tuple[H[_T], int]],
    lo: int,
    hi: int,
) -> Iterator[RollCountT[_T]]:
    r"""
    Yields `#!python ((min_val, max_val), count)` pairs for a heterogeneous pool where exactly the single lowest (*lo* = 1) and single highest (*hi* = 1) sorted outcomes are selected.

    **Why this is fast**

    Naïve enumeration visits every element of the Cartesian product of all dice faces (`#!math O\!\left(\prod_i |\text{faces}_i\right)` outcomes) and sorts each roll.
    For `#!math P(d4, d6, d8, d10, d12, d20)` that is `#!math 4 \times 6 \times 8 \times 10 \times 12 \times 20 = 460{,}800` rolls.

    This function instead iterates over outcome *pairs* `#!math (a, b)` with `#!math a \le b` drawn from the union of all faces, and for each pair computes the count in `#!math O(n)` time using the inclusion-exclusion formula below.
    Total work is `#!math O(|V|^2 \times n)`, which is roughly 190&times; faster for the example above (~2,400 ops).

    **Inclusion-exclusion formula**

    For each pair `#!math (a, b)` with `#!math a \le b`, the number of ways to roll the pool such that the overall minimum is exactly `#!math a` and the overall maximum is exactly `#!math b` is:

    ```math
    \text{count}(\min{=}a,\,\max{=}b)
    = N[a,b] - N(a,b] - N[a,b) + N(a,b)
    ```

    where `#!math N(I)` denotes the product over all dice of the count of that die’s outcomes that fall in interval `#!math I`.
    The four terms correspond to the four ways of making each of the two boundary values strict or non-strict:

    | term                  | lower bound       | upper bound       | sign |
    |-----------------------|-------------------|-------------------|------|
    | `#!math N[a,b]`       | `#!math v \ge a`  | `#!math v \le b`  | +    |
    | `#!math N(a,b]`       | `#!math v > a`    | `#!math v \le b`  | −    |
    | `#!math N[a,b)`       | `#!math v \ge a`  | `#!math v < b`    | −    |
    | `#!math N(a,b)`       | `#!math v > a`    | `#!math v < b`    | +    |

    This works because "min `#!math > a`" is equivalent to "all dice `#!math > a`", and "max `#!math < b`" is equivalent to "all dice `#!math < b`".
    Each constraint reduces to an "all-dice-in-interval" event, which factorises as a product over dice.
    That factorisation is what makes the formula `#!math O(n)` per pair rather than `#!math O(n^k)`.

    **Why this does not extend cleanly to lo > 1 or hi > 1**

    For `#!math (lo, hi) = (2, 1)`, the analogous formula would need to handle the constraint "2nd-minimum `#!math > a_1`", which means "at most 1 die `#!math \le a_1`".
    That event does *not* factorise as a product over dice (it is a sum of `#!math n+1` product terms via a generating-function expansion), so the `#!math O(n)`-per-tuple structure breaks down.
    Extension to larger `#!math (lo, hi)` is theoretically possible using polynomial coefficient extraction, but requires substantially more complex machinery.

    **Why interior (arbitrary non-extremes) heterogeneous selections have no fast path**

    For selections that are neither a prefix, a suffix, nor the min+max extremes (e.g. the 2nd and 4th positions out of 5), the constraint on the selected positions involves interior order statistics ("exactly `#!math k` dice fall in region `#!math R`"), which cannot be expressed as an "all-dice-in-interval" product event for heterogeneous dice.
    The multinomial partition formula that works for homogeneous dice (see e.g. [math.stackexchange.com/q/4173084](https://math.stackexchange.com/questions/4173084)) does not factorise per-die when faces differ, so those cases fall back to full Cartesian-product enumeration.
    For homogeneous pools the existing `_rwc_homogeneous_n_h_using_partial_selection` path (Ilmari Karonen’s DP) already handles all selection patterns efficiently.
    """
    assert lo == 1 and hi == 1, "only (lo=1, hi=1) is currently supported"  # noqa: PT018

    all_dice: list[H[_T]] = [h for h, n in groups for _ in range(n)]
    all_outcome_set: set[Any] = {v for h in all_dice for v in h}
    all_outcomes = list(all_outcome_set)
    try:
        all_outcomes.sort()
        use_natural = False
    except TypeError:
        all_outcomes.sort(key=natural_key)
        use_natural = True

    for i_a, a in enumerate(all_outcomes):
        for b in all_outcomes[i_a:]:
            n_ab = n_slo = n_shi = n_sbo = 1
            for h in all_dice:
                c_ab = c_slo = c_shi = c_sbo = 0
                for v, c in h.items():
                    if use_natural:
                        nk_v, nk_a, nk_b = (
                            natural_key(v),
                            natural_key(a),
                            natural_key(b),
                        )
                        ge_a, le_b = nk_v >= nk_a, nk_v <= nk_b  # ty: ignore[unsupported-operator]
                        gt_a, lt_b = nk_v > nk_a, nk_v < nk_b  # ty: ignore[unsupported-operator]
                    else:
                        ge_a, le_b = v >= a, v <= b
                        gt_a, lt_b = v > a, v < b
                    if ge_a and le_b:
                        c_ab += c
                        if gt_a:
                            c_slo += c
                        if lt_b:
                            c_shi += c
                            if gt_a:
                                c_sbo += c
                n_ab *= c_ab
                n_slo *= c_slo
                n_shi *= c_shi
                n_sbo *= c_sbo
            count = n_ab - n_slo - n_shi + n_sbo
            if count > 0:
                yield (a, b), count

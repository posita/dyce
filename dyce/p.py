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
import warnings
from abc import ABC, abstractmethod
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from functools import cache, reduce
from itertools import product, starmap
from math import comb, prod
from typing import (
    Any,
    Generic,
    Literal,
    Never,
    SupportsIndex,
    SupportsInt,
    TypeVar,
    cast,
    overload,
)

import optype as ot

from .h import H, aggregate_weighted, sum_h
from .hable import HableOpsMixin
from .lifecycle import ExperimentalWarning, experimental
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
_StateT = TypeVar("_StateT")
_ConvolvableT = TypeVar("_ConvolvableT", bound=ot.CanAddSame)

RollT = tuple[_T, ...]
RollCountT = tuple[RollT[_T], int]
RollProbT = tuple[RollT[_T], int, int]


class SurveyorBase(ABC, Generic[_T, _StateT, _ResultT]):
    r"""
    Provides the four interfaces required for [`P.survey`][dyce.p.P.survey].
    """

    @property
    def initial(self) -> _StateT | None:
        r"By default, this is `None`."
        return None

    @abstractmethod
    def accumulate(self, state: _StateT | None, outcome: _T, count: int) -> _StateT: ...

    @abstractmethod
    def order(self, outcomes: Iterable[_T]) -> Iterable[_T]: ...

    def settle(self, state: _StateT) -> _ResultT:
        r"""
        By default, this is *state* (i.e., the terminal states are themselves the outcomes).

        This can be overridden if additional mutation is required.
        """
        return cast("_ResultT", state)


class AscendingSurveyorBase(SurveyorBase[_T, _StateT, _ResultT]):
    r"""
    Surveyor that uses [`survey_outcome_order_ascending`][dyce.p.survey_outcome_order_ascending] for ordering outcomes.
    """

    def order(self, outcomes: Iterable[_T]) -> Iterable[_T]:
        return survey_outcome_order_ascending(outcomes)


class DescendingSurveyorBase(SurveyorBase[_T, _StateT, _ResultT]):
    r"""
    Surveyor that uses [`survey_outcome_order_descending`][dyce.p.survey_outcome_order_descending] for ordering outcomes.
    """

    def order(self, outcomes: Iterable[_T]) -> Iterable[_T]:
        return survey_outcome_order_descending(outcomes)


class ParameterizedSurveyor(SurveyorBase[_T, _StateT, _ResultT]):
    @overload
    def __init__(  # pyrefly: ignore[invalid-annotation]
        self: "ParameterizedSurveyor[_T, _StateT, _StateT]",
        accumulate: Callable[[_StateT | None, _T, int], _StateT],
        order: Callable[[Iterable[_T]], Iterable[_T]],
        *,
        initial: _StateT | None = ...,
        settle: None = ...,
    ) -> None: ...
    @overload
    def __init__(  # pyrefly: ignore[invalid-annotation]
        self: "ParameterizedSurveyor[_T, _StateT, _ResultT]",
        accumulate: Callable[[_StateT | None, _T, int], _StateT],
        order: Callable[[Iterable[_T]], Iterable[_T]],
        *,
        initial: _StateT | None = ...,
        settle: Callable[[_StateT], _ResultT],
    ) -> None: ...
    def __init__(
        self,
        accumulate: Callable[[_StateT | None, _T, int], _StateT],
        order: Callable[[Iterable[_T]], Iterable[_T]],
        *,
        initial: _StateT | None = None,
        settle: Callable[[_StateT], _ResultT] | None = None,
    ) -> None:
        self._accumulate = accumulate
        self._order = order
        self._initial = initial
        self._settle = settle

    @property
    def initial(self) -> _StateT | None:
        return self._initial

    def accumulate(self, state: _StateT | None, outcome: _T, count: int) -> _StateT:
        return self._accumulate(state, outcome, count)

    def order(self, outcomes: Iterable[_T]) -> Iterable[_T]:
        return self._order(outcomes)

    def settle(self, state: _StateT) -> _ResultT:
        return self._settle(state) if self._settle else cast("_ResultT", state)


class _WhichSurveyor(SurveyorBase[_T, _StateT, _ResultT]):
    def __init__(self, p: "P[_T]", selected: tuple[int, ...]) -> None:
        if not selected:
            raise ValueError(f"{type(self).__name__} requires at least one selection")
        self._selected = selected
        self._selected_indices = tuple(sorted(set(selected)))
        self._p_len = len(p)
        self._ascending = (
            min(selected) - 0  # distance from left
            <= self._p_len - 1 - max(selected)  # distance from right
        )

    def order(self, outcomes: Iterable[_T]) -> Iterable[_T]:
        return (
            survey_outcome_order_ascending(outcomes)
            if self._ascending
            else survey_outcome_order_descending(outcomes)
        )

    def _selected_bounds(self, index: int, count: int) -> tuple[int, int]:
        start, stop = (
            (index, index + count)
            if self._ascending
            else (index - count + 1, index + 1)
        )
        return (
            bisect_left(self._selected_indices, start),
            bisect_left(self._selected_indices, stop),
        )


class _WhichHSurveyor(
    _WhichSurveyor[_ConvolvableT, tuple[_ConvolvableT | None, int], _ConvolvableT]
):
    def __init__(self, p: "P[_ConvolvableT]", selected: tuple[int, ...]) -> None:
        super().__init__(p, selected)
        self._counts_by_index: Counter[int] = Counter(selected)

    @property
    def initial(self) -> tuple[_ConvolvableT | None, int]:
        return None, (0 if self._ascending else self._p_len - 1)

    @nobeartype  # triggers on P[~_ConvolvableT].h(int), which technically works, because no addition is involved
    def accumulate(  # type: ignore[override] # ty: ignore[invalid-method-override]
        self,
        state: tuple[_ConvolvableT | None, int],
        outcome: _ConvolvableT,
        count: int,
    ) -> tuple[_ConvolvableT | None, int]:
        sum_so_far, index_so_far = state
        selected_start, selected_stop = self._selected_bounds(index_so_far, count)
        for selected_pos in range(selected_start, selected_stop):
            i = self._selected_indices[selected_pos]
            for _ in range(self._counts_by_index.get(i, 0)):
                sum_so_far = outcome if sum_so_far is None else sum_so_far + outcome
        index_so_far += count if self._ascending else -count
        return sum_so_far, index_so_far

    @nobeartype  # triggers on P[~_ConvolvableT].h(int), which technically works, because no addition is involved
    def settle(self, state: tuple[_ConvolvableT | None, int]) -> _ConvolvableT:
        total, _ = state
        assert total is not None
        return total


class _WhichRollSurveyor(
    _WhichSurveyor[_T, tuple[tuple[_T, ...], int], tuple[_T, ...]]
):
    def __init__(self, p: "P[_T]", selected: tuple[int, ...]) -> None:
        super().__init__(p, selected)
        self._selection_map = {s: i for i, s in enumerate(self._selected_indices)}

    @property
    def initial(self) -> tuple[tuple[_T, ...], int]:
        return (), (0 if self._ascending else self._p_len - 1)

    def accumulate(  # pyrefly: ignore[bad-override] # ty: ignore[invalid-method-override]
        self,
        state: tuple[tuple[_T, ...], int],  # type: ignore[override]
        outcome: _T,
        count: int,
    ) -> tuple[tuple[_T, ...], int]:
        roll_so_far, index_so_far = state
        selected_start, selected_stop = self._selected_bounds(index_so_far, count)
        if selected_start != selected_stop:
            selected_outcomes = (outcome,) * (selected_stop - selected_start)
            roll_so_far = (
                (*roll_so_far, *selected_outcomes)
                if self._ascending
                else (*selected_outcomes, *roll_so_far)
            )
        index_so_far += count if self._ascending else -count
        return roll_so_far, index_so_far

    def settle(self, state: tuple[tuple[_T, ...], int]) -> tuple[_T, ...]:
        roll, _ = state
        return tuple(roll[self._selection_map[s]] for s in self._selected)


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
        "_h_groups",
        "_hash",
        "_len",
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
        self._h_groups: dict[H[_T_co], int]
        h_counts: Counter[H[_T_co]] = Counter()

        for init_val in init_vals:
            if isinstance(init_val, H):
                h_counts[init_val] += 1
            elif isinstance(init_val, P):
                h_counts.update(dict(init_val._h_groups.items()))  # ruff: ignore[private-member-access]
            else:
                h_counts[H(init_val)] += 1

        try:
            self._h_groups = {
                h: h_counts[h]
                for h in sorted(h_counts, key=lambda h: tuple(h.items()))
                if h
            }
        except TypeError:
            # For Hs whose outcomes don't support direct comparisons (e.g. symbolic
            # types)
            self._h_groups = {
                h: h_counts[h]
                for h in sorted(h_counts, key=lambda h: natural_key(h.items()))
                if h
            }
        self._hash: int | None = None
        self._len = sum(self._h_groups.values())
        self._total: int | None = None

    # ---- Overrides -------------------------------------------------------------------

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((type(self), *self._h_groups.items()))
        return self._hash

    def __repr__(self) -> str:
        def _n_at(h: H[_T_co], n: int) -> str:
            return repr(h) if n == 1 else f"{n}@{type(self).__name__}({h!r})"

        if len(self._h_groups) == 1:
            h, hn = next(iter(self._h_groups.items()))
            return f"{type(self).__name__}({_n_at(h, 1)})" if hn == 1 else _n_at(h, hn)
        else:
            inner = ", ".join(starmap(_n_at, self._h_groups.items()))
            return f"{type(self).__name__}({inner})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, P):
            return self._h_groups == other._h_groups
        return NotImplemented

    # ---- Sequence abstract methods ---------------------------------------------------

    @overload
    def __getitem__(self: "P[_T]", key: SupportsIndex) -> H[_T]: ...
    @overload
    def __getitem__(self: "P[_T]", key: slice) -> "P[_T]": ...
    @nobeartype  # TODO(posita): <https://github.com/beartype/beartype/issues/636>
    def __getitem__(self: "P[_T]", key: SupportsIndex | slice) -> "P[_T] | H[_T]":

        def _selected_hs(*indices: int) -> Iterator[H[_T]]:
            offsets: list[int] = []
            hs: list[H[_T]] = []
            cum = 0
            for h, n in self._h_groups.items():
                offsets.append(cum)
                hs.append(h)
                cum += n
            for i in indices:
                g = bisect_right(offsets, i) - 1
                yield hs[g]

        if isinstance(key, slice):
            return P(*_selected_hs(*range(*key.indices(len(self)))))
        i = operator.index(key)
        if i >= len(self) or i < -len(self):
            raise IndexError("P index out of range")
        return next(_selected_hs(len(self) + i if i < 0 else i))

    def __iter__(self: "P[_T]") -> Iterator[H[_T]]:
        for h, hn in self._h_groups.items():
            yield from (h for _ in range(hn))

    def __len__(self) -> int:
        return self._len

    # ---- Operators -------------------------------------------------------------------

    @overload
    def __matmul__(self: "P[Any]", lhs: Literal[0]) -> "P[Never]": ...
    @overload
    def __matmul__(self: "P[_T]", lhs: SupportsInt) -> "P[_T]": ...
    def __matmul__(self: "P", lhs: SupportsInt) -> "P":
        try:
            n = lossless_int(lhs)
        except (TypeError, ValueError):
            return NotImplemented
        if n < 0:
            raise ValueError(
                f"{type(self).__name__} requires non-negative operand for @ operator (found {n!r})"
            )
        # TODO(posita): # ruff: ignore[missing-todo-link] - Put initialization logic in
        # an _init helper method and have both this and __init__ use that helper method
        # The slow and safe way
        # return P(*chain.from_iterable(repeat(self, n)))  # ruff: ignore[commented-out-code]
        # The dangerous and fast way (needs to know about __init__, __slots__,
        # initialization, etc.)
        p = P()
        if n:
            p._h_groups = {h: hn * n for h, hn in self._h_groups.items()}
            p._len = len(self) * n
            assert p._hash is None
            assert p._total is None
        return p

    @overload
    def __rmatmul__(self: "P[Any]", rhs: Literal[0]) -> "P[Never]": ...
    @overload
    def __rmatmul__(self: "P[_T]", rhs: SupportsInt) -> "P[_T]": ...
    def __rmatmul__(self: "P", rhs: SupportsInt) -> "P":
        return self.__matmul__(rhs)

    # ---- Properties ------------------------------------------------------------------

    @property
    def total(self) -> int:
        r"""
        Equivalent to `prod(h.total for h in self)`.
        Consistent with the empty product, this is `1` for an empty pool.
        The result is cached to avoid redundant computation with multiple accesses.
        """
        if self._total is None:
            self._total = prod(h.total**hn for h, hn in self._h_groups.items())
        return self._total

    # ---- Methods ---------------------------------------------------------------------

    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T], _ResultT],
        *,
        apply_to_each: bool = ...,
    ) -> "P[_ResultT]": ...
    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: "H[_OtherT]",
        *,
        apply_to_each: bool = ...,
    ) -> "P[_ResultT]": ...
    @overload
    def apply_to_each_h(
        self: "P[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: _OtherT,
        *,
        apply_to_each: bool = ...,
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

        *func* is assumed to be idempotent, meaning that for each distinct histogram `h`, calling `h.apply(func, other)` should return the same result regardless of context.
        This allows for *func* to be applied only once for each distinct `H` in `P`, and the result reused.
        If this is not desired, provide `True` for *apply_to_each* to ensure that *func* is actually run on each individual histogram.
        """

        def _h_counts_by_group() -> Iterator[tuple[H[_T], int]]:
            yield from self._h_groups.items()

        def _each_h_count_in_self() -> Iterator[tuple[H[_T], int]]:
            yield from ((h, 1) for h in self)

        def _applied_hs() -> Iterator[H[_ResultT]]:
            for h, count in (
                _each_h_count_in_self() if apply_to_each else _h_counts_by_group()
            ):
                new_h = h.apply(func, other)  # type: ignore[arg-type] # ty: ignore[no-matching-overload]
                yield from (new_h for _ in range(count))

        return P(*_applied_hs())

    @experimental
    def apply_to_each_roll(
        self: "P[_T]",
        func: Callable[[RollT[_T]], H[_ResultT] | _ResultT],
        *which: GetItemT,
    ) -> H[_ResultT]:
        r"""
        Return a new [`H`][dyce.H] by applying *func* to each roll.
        Shorthand for:

        ```python
        aggregate_weighted(
            (func(roll), count) for roll, count in self.rolls_with_counts(*which)
        )
        ```

        Note that there are often other, much more efficient ways to arrive at desired computations, but for a handful of small dice, this can be a more expressive way to get the job done.
        For example:

            >>> from dyce import P, H, RollT
            >>> d6 = H(6)
            >>> h3d6 = 3 @ d6
            >>> p3d6 = 3 @ P(d6)
            >>> p3d6.apply_to_each_roll(sum) == h3d6
            True

        <!-- -- >

            >>> best_three_of_4d6 = (4 @ P(6)).h(slice(-3, None))
            >>> (4 @ P(6)).apply_to_each_roll(sum, slice(-3, None)) == best_three_of_4d6
            True

        <!-- -- >

            >>> ones_rolled_in_3d6 = 3 @ (d6.eq(1))
            >>> def count_ones_in_roll(roll: RollT[int]) -> int:
            ...     return sum(1 for outcome in roll if outcome == 1)
            >>> p3d6.apply_to_each_roll(count_ones_in_roll) == ones_rolled_in_3d6
            True
        """
        return cast(
            "H[_ResultT]",
            aggregate_weighted(
                (func(roll), count) for roll, count in self.rolls_with_counts(*which)
            ),
        )

    @overload
    def h(self: "P[Never]", *which: GetItemT) -> H[Never]: ...
    @overload
    # See <https://github.com/jorenham/optype/discussions/574>
    def h(self: "P[ot.CanAddSame[int, int]]", *which: GetItemT) -> H[int]: ...
    @overload
    def h(self: "P[_ConvolvableT]", *which: GetItemT) -> H[_ConvolvableT]: ...
    @overload
    def h(self: "P[_T]", which: int) -> H[_T]: ...  # pyrefly: ignore[inconsistent-overload]
    def h(self: "P", *which: GetItemT) -> H:  # type: ignore[misc] # ty: ignore[invalid-method-override]
        r"""
        Combines (or “flattens”) all contained histograms into a single [`H`][dyce.H] in accordance with the [`HableT` protocol][dyce.HableT].

            >>> (2 @ P(6)).h()
            H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

        When one or more optional *which* identifiers is provided, this is roughly equivalent to `H((sum(roll), count) for roll, count in self.rolls_with_counts(*which))` with optimizations.
        Identifiers can be `int`s or `slice`s, and can be mixed.

        Taking the greatest of two six-sided dice can be modeled as:

            >>> p_2d6 = 2 @ P(6)
            >>> p_2d6.h(-1)
            H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
            >>> print(p_2d6.h(-1).format(width=65))
            avg |    4.47
            std |    1.40
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

        !!! note "On selection ordering"

            As an optimization, selected outcomes are summed in the order in which they appear in sorted rolls, regardless of the order they appear in *which*.
            Where addition over the outcomes’ type is commutative, equivalence holds as expected:

                >>> p_c = P(2, 3, 4)
                >>> p_c.h(
                ...     slice(None),  # select everything once
                ...     slice(None),  # then select everything again
                ... ) == 2 * p_c.h()
                True

            Where outcomes define `__add__` as non-commutative (e.g., strings, sequences, etc.), ordering can affect construction under certain circumstances:

                >>> p_nc = P(H(((1,), (2,))), H(((3,), (4,))), H(((5,), (6,))))
                >>> p_nc.h(
                ...     slice(None),  # select everything once, then again, like above
                ...     slice(None),  # pyright: ignore[reportCallIssue]
                ... )
                H({(1, 1, 3, 3, 5, 5): 1, (1, 1, 3, 3, 6, 6): 1, ..., (2, 2, 4, 4, 5, 5): 1, (2, 2, 4, 4, 6, 6): 1})
                >>> 2 * p_nc.h()  # type: ignore[operator]
                H({(1, 3, 5, 1, 3, 5): 1, (1, 3, 6, 1, 3, 6): 1, ..., (2, 4, 5, 2, 4, 5): 1, (2, 4, 6, 2, 4, 6): 1})
        """
        if not which:
            return H({}) if len(self._h_groups) == 0 else sum_h(self)
        n = len(self)
        indices = tuple(range(n))
        selected = tuple(getitems(indices, which or indices))
        if not selected:
            return H({})
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            if len(selected) == 1 and len(self._h_groups) == 1:
                h, count = next(iter(self._h_groups.items()))
                return h.order_stat_for_n_at_pos(count, selected[0])
            # Reducing each repeated group to its extreme strictly shrinks the pool,
            # so recursion terminates once every remaining group has count one.
            if (
                len(selected) == 1
                and selected[0] in (0, n - 1)
                and any(count > 1 for count in self._h_groups.values())
            ):
                from_right = selected[0] == n - 1
                reduced = P(
                    *(
                        h.order_stat_for_n_at_pos(count, count - 1 if from_right else 0)
                        for h, count in self._h_groups.items()
                    )
                )
                return reduced.h(-1 if from_right else 0)
            # Unlike rolls_with_counts, h can fold large selections directly without
            # materializing rolls, which becomes faster beyond roughly half the pool.
            if 1 < len(selected) <= n // 2 and len(self._h_groups) == 1:
                h, count = next(iter(self._h_groups.items()))
                if selected == tuple(range(len(selected))):
                    return H.from_counts(
                        (reduce(operator.add, roll), weight)
                        for roll, weight in _rwc_homogeneous_one_end(
                            count, h, len(selected), from_right=False
                        )
                    )
                if selected == tuple(range(n - len(selected), n)):
                    return H.from_counts(
                        (reduce(operator.add, roll), weight)
                        for roll, weight in _rwc_homogeneous_one_end(
                            count, h, len(selected), from_right=True
                        )
                    )
            return self.survey(_WhichHSurveyor(self, selected))

    @experimental
    def roll(self: "P[_T]") -> RollT[_T]:
        r"""
        Returns (weighted) random outcomes from contained histograms.

        !!! note "On ordering"

            This method “works” (i.e., falls back to a “natural” ordering of string representations) for outcomes whose relative values cannot be known (e.g., symbolic expressions).
            This is deliberate to allow random roll functionality where symbolic resolution is not needed or will happen later.
        """
        roll = [h.roll() for h in self]
        try:
            roll.sort()  # pyrefly: ignore[bad-specialization] # pyright: ignore[reportCallIssue]
        except TypeError:
            roll.sort(key=natural_key)
        return tuple(roll)

    def rolls_with_counts(self: "P[_T]", *which: GetItemT) -> Iterator[RollCountT[_T]]:
        r"""
        Returns an iterator yielding `(roll, count)` pairs that collectively enumerate all distinct rolls of the pool.
        Each *roll* is a sorted tuple of outcomes (least to greatest); *count* is the number of ways that roll occurs.

        If one or more *which* arguments are provided (as `SupportsIndex` or `slice` values), each roll is filtered to the selected positions before yielding.

            >>> from dyce import H, P
            >>> p_2d6 = 2 @ P(6)
            >>> H.from_counts(
            ...     (sum(roll), count) for roll, count in p_2d6.rolls_with_counts()
            ... ) == p_2d6.h()
            True

        *which* selects by sorted position.
        An inefficient way to take the highest outcome from 3d6:

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
            [((1, 1), 1), ((1, 2), 6), ((1, 3), 12), ..., ((5, 5), 1), ((5, 6), 6), ((6, 6), 1)]
            >>> H.from_counts(lo_hi_from_all_3d6_rolls) == H.from_counts(
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
            [((1, 1), 1), ((1, 2), 6), ((2, 2), 1)]
            >>> sorted(P(H(2), H(3)).rolls_with_counts())
            [((1, 1), 1), ((1, 2), 2), ((1, 3), 1), ((2, 2), 1), ((2, 3), 1)]

        No rolls will be produced with empty `P` objects or where *which* selects no positions.

            >>> sorted(P(6).rolls_with_counts(slice(6, 7)))
            []
            >>> sorted(P().rolls_with_counts())
            []
        """
        n = len(self)
        indices = tuple(range(n))
        selected = tuple(getitems(indices, which or indices))
        if len(selected) == 1 and len(self._h_groups) == 1:
            h, count = next(iter(self._h_groups.items()))
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ExperimentalWarning)
                order_stat_h = h.order_stat_for_n_at_pos(count, selected[0])
            yield from (
                ((outcome,), weight) for outcome, weight in order_stat_h.items()
            )
            return
        if len(selected) == 1 and len(self._h_groups) > 1 and selected[0] in (0, n - 1):
            extreme_h = self.h(-1 if selected[0] == n - 1 else 0)
            yield from (((outcome,), weight) for outcome, weight in extreme_h.items())
            return
        if 1 < len(selected) < n and len(self._h_groups) == 1:
            h, count = next(iter(self._h_groups.items()))
            if selected == tuple(range(len(selected))):
                yield from _rwc_homogeneous_one_end(
                    count, h, len(selected), from_right=False
                )
                return
            if selected == tuple(range(n - len(selected), n)):
                yield from _rwc_homogeneous_one_end(
                    count, h, len(selected), from_right=True
                )
                return
        yield from (
            self._survey_raw(_WhichRollSurveyor(self, selected)) if selected else ()
        )

    @overload
    def survey(
        self: "P[_T]",
        surveyor: SurveyorBase[_T, _StateT, _ResultT],
    ) -> H[_ResultT]: ...
    @overload
    def survey(
        self: "P[_T]",
        *,
        accumulate: Callable[[_StateT | None, _T, int], _StateT],
        initial: _StateT | None = ...,
        order: Callable[[Iterable[_T]], Iterable[_T]],
        settle: None = ...,
    ) -> H[_StateT]: ...
    @overload
    def survey(
        self: "P[_T]",
        *,
        accumulate: Callable[[_StateT | None, _T, int], _StateT],
        initial: _StateT | None = ...,
        order: Callable[[Iterable[_T]], Iterable[_T]],
        settle: Callable[[_StateT], _ResultT],
    ) -> H[_ResultT]: ...
    @experimental
    def survey(
        self: "P[_T]",
        surveyor: SurveyorBase[_T, _StateT, _ResultT] | None = None,
        *,
        accumulate: Callable[[_StateT | None, _T, int], _StateT] | None = None,
        initial: _StateT | None = None,
        order: Callable[[Iterable[_T]], Iterable[_T]] | None = None,
        settle: Callable[[_StateT], _ResultT] | None = None,
    ) -> H[_StateT | _ResultT]:
        r"""
        Return a new [`H`][dyce.H] by folding a transition function defined by *surveyor* over the pool one outcome at a time.

        This implements a state-collapsing dynamic program similar to Albert Julius Liu’s [`icepool`](https://github.com/HighDiceRoller/icepool).
        Rather than enumerating every distinct roll (as [`apply_to_each_roll`][dyce.P.apply_to_each_roll] does), it sweeps the shared outcome axis once, and at each distinct outcome branches on how many dice show it.
        Equivalent partial rolls that reach the same state are merged, so the cost scales with the number of reachable states rather than the number of rolls.

        If provided, *surveyor* bundles the *accumulate*, *order*, and *settle* methods as well as the *initial* property.
        Otherwise, each may be provided separately.
        *accumulate* and *order* are required.
        *initial* and *settle* are optional.

        *accumulate* is called as `accumulate(state, outcome, count)` and returns the successor state.
        On the first (seed) call, *state* is `surveyor.initial`.
        *count* is the number of dice showing *outcome*, aggregated across all of the pool’s (possibly heterogeneous) histograms, and is always at least `1`.
        *accumulate* is invoked only for outcomes that at least one die shows, never for absent ones.
        A mechanic that must reason about gaps in a sequence (e.g. the longest run of consecutive values) should therefore compare successive *outcome* values rather than expecting to be notified of the absent ones.
        *state* must be hashable, since equal states are merged.

        *order* selects the sweep order over the shared outcome set.

        If provided, *settle* maps each terminal state to the outcome recorded in the resulting [`H`][dyce.H].
        Otherwise, *accumulate*’s terminal states are themselves the outcomes.

        Summing three six-sided dice, cross-checked against [`h`][dyce.P.h] (note that *count* scales each outcome’s contribution):

            >>> from dyce import P
            >>> from dyce.p import survey_outcome_order_ascending
            >>> def running_sum(state, outcome, count):
            ...     return outcome * count if state is None else state + outcome * count
            >>> p_3d6 = 3 @ P(6)
            >>> p_3d6.survey(
            ...     accumulate=running_sum, order=survey_outcome_order_ascending
            ... ) == p_3d6.h()
            True

        Keeping the greatest two of four six-sided dice is order-sensitive, so it sweeps descending and uses *settle* to project the accumulated sum:

            >>> from dyce.p import survey_outcome_order_descending
            >>> def keep_highest_two(state, outcome, count):
            ...     kept, total = (0, 0) if state is None else state
            ...     take = min(count, 2 - kept)
            ...     return kept + take, total + outcome * take
            >>> p_4d6 = 4 @ P(6)
            >>> keep = p_4d6.survey(
            ...     accumulate=keep_highest_two,
            ...     order=survey_outcome_order_descending,
            ...     settle=lambda s: s[1],
            ... )
            >>> keep == p_4d6.h(slice(-2, None))
            True
        """
        if surveyor is None:
            if accumulate is None or order is None:
                raise ValueError("must provide a surveyor or an accumulate and order")
            survey_raw_iter = (
                # Without the convoluted ... if settle is None else ... structure below,
                # Mypy is confused whether the return type is H[_StateT] or H[_ResultT]
                self._survey_raw(
                    # settle is None, return type is H[_StateT]
                    ParameterizedSurveyor(
                        accumulate,
                        order,
                        initial=initial,
                    )
                )
                if settle is None
                else self._survey_raw(
                    # settle is not None, return type is H[_ResultT]
                    ParameterizedSurveyor(
                        accumulate,
                        order,
                        initial=initial,
                        settle=settle,
                    )
                )
            )
            return aggregate_weighted(survey_raw_iter)
        else:
            if (
                accumulate is not None
                or initial is not None
                or order is not None
                or settle is not None
            ):
                raise ValueError(
                    "must not provide an accumulate and order with a surveyor"
                )
            return aggregate_weighted(self._survey_raw(surveyor))

    def _survey_raw(  # ruff: ignore[complex-structure]
        self: "P[_T]",
        surveyor: SurveyorBase[_T, _StateT, _ResultT],
    ) -> Iterator[tuple[_ResultT, int]]:
        uniq_outcomes = list(
            surveyor.order(set().union(*(set(h) for h in self._h_groups)))
        )
        if not uniq_outcomes:
            return

        group_items = tuple(self._h_groups.items())
        n_groups = len(group_items)
        group_weights = tuple(
            tuple(h.get(outcome, 0) for outcome in uniq_outcomes)
            for h, _ in group_items
        )
        memo: dict[
            tuple[  # key
                int,  # current unique outcome index; outcomes[uniq_outcome_idx]
                tuple[int, ...],  # remaining split counts for outcome (one per group)
            ],
            dict[  # value
                _StateT,
                int,  # weight
            ],
        ] = {}

        def _solve(  # ruff: ignore[complex-structure]
            uniq_outcome_idx: int, group_split_counts: tuple[int, ...]
        ) -> dict[_StateT, int]:
            key = (uniq_outcome_idx, group_split_counts)
            if key in memo:
                return memo[key]
            outcome = uniq_outcomes[uniq_outcome_idx]
            result: dict[
                _StateT,
                int,  # weight
            ] = defaultdict(int)
            if uniq_outcome_idx == 0:
                # Base case: every remaining die must show the first outcome (lowest for
                # ascending, highest for descending)
                scale = prod(
                    group_weights[g][0] ** group_split_counts[g]
                    for g in range(n_groups)
                )
                if scale:
                    count = sum(group_split_counts)
                    seed = (
                        surveyor.accumulate(surveyor.initial, outcome, count)
                        if count
                        else cast("_StateT", surveyor.initial)
                    )
                    result[seed] += scale
            else:
                # For a heterogeneous pool, an outcome can come from different groups
                # ("splits"). accumulate only cares about the total, not which group
                # supplied them. So the code sums the weight of all splits sharing a
                # total into by_count first, then calls accumulate(state, outcome,
                # count) once instead of calling it redundantly for each split.
                state_weights_by_count: dict[
                    int,  # count of dice showing uniq_outcomes[uniq_outcome_idx]
                    dict[
                        _StateT,
                        int,  # weight
                    ],
                ] = defaultdict(lambda: defaultdict(int))
                # For each group g, establish a range of 0..group_split_counts[g] (0 up
                # to all its remaining dice). Then take the Cartesian product across
                # those group ranges, so split is a tuple (k_0, k_1, ...), one count per
                # group. For example, take 2 groups with the respective counts (2, 1).
                # This produces splits of (0,0), (0,1), (1,0), (1,1), (2,0), (2,1). Each
                # is one candidate allocation of dice to this outcome. The loop body
                # then weights it and recurses on the leftover.
                for split in product(
                    *(range(group_split_counts[g] + 1) for g in range(n_groups))
                ):
                    scale = 1
                    for g in range(n_groups):
                        scale *= (
                            comb(group_split_counts[g], split[g])
                            * group_weights[g][uniq_outcome_idx] ** split[g]
                        )
                    if scale == 0:
                        # This group has no such outcome (e.g., trying to role a 6 on a
                        # d4)
                        continue
                    remaining = tuple(
                        group_split_counts[g] - split[g] for g in range(n_groups)
                    )
                    for state, weight in _solve(
                        uniq_outcome_idx - 1, remaining
                    ).items():
                        state_weights_by_count[sum(split)][state] += weight * scale
                for count, states in state_weights_by_count.items():
                    if count:
                        for state, weight in states.items():
                            result[surveyor.accumulate(state, outcome, count)] += weight
                    else:
                        # States pass through unchanged
                        for state, weight in states.items():
                            result[state] += weight
            memo[key] = dict(result)
            return memo[key]

        final_states = _solve(len(uniq_outcomes) - 1, tuple(n for _, n in group_items))

        yield from (
            (surveyor.settle(state), weight) for state, weight in final_states.items()
        )


# ---- Helpers -------------------------------------------------------------------------


def _rwc_homogeneous_one_end(
    n: int,
    h: H[_T],
    k: int,
    *,
    from_right: bool,
) -> Iterator[RollCountT[_T]]:
    r"""
    Yield the lowest or highest *k* outcomes from *n* rolls of *h*.
    Once an outcome fills the remaining selected positions, a complementary binomial tail combines every possible assignment of the unselected dice.
    """
    ordered_outcomes = (
        survey_outcome_order_descending(h)
        if from_right
        else survey_outcome_order_ascending(h)
    )
    outcomes = tuple(outcome for outcome in ordered_outcomes if h[outcome])
    weights = tuple(h[outcome] for outcome in outcomes)
    remaining_total = sum(weights)
    remaining_totals_list: list[int] = []
    for weight in weights:
        remaining_total -= weight
        remaining_totals_list.append(remaining_total)
    remaining_totals = tuple(remaining_totals_list)

    @cache
    def _terminal_count(outcome_index: int, remaining: int, needed: int) -> int:
        weight = weights[outcome_index]
        remaining_total = remaining_totals[outcome_index]
        fewer_than_needed = sum(
            comb(remaining, count)
            * weight**count
            * remaining_total ** (remaining - count)
            for count in range(needed)
        )
        return (weight + remaining_total) ** remaining - fewer_than_needed

    def _generate(
        outcome_index: int,
        remaining: int,
        roll: RollT[_T],
        scale: int,
    ) -> Iterator[RollCountT[_T]]:
        if outcome_index >= len(outcomes):
            return
        outcome = outcomes[outcome_index]
        weight = weights[outcome_index]
        needed = k - len(roll)
        if remaining >= needed:
            terminal_count = _terminal_count(outcome_index, remaining, needed)
            if terminal_count:
                selected_roll = (*roll, *((outcome,) * needed))
                yield (
                    tuple(reversed(selected_roll)) if from_right else selected_roll,
                    scale * terminal_count,
                )
        for count in range(min(needed - 1, remaining) + 1):
            next_scale = scale * comb(remaining, count) * weight**count
            if next_scale:
                yield from _generate(
                    outcome_index + 1,
                    remaining - count,
                    (*roll, *((outcome,) * count)),
                    next_scale,
                )

    yield from _generate(0, n, (), 1)


def survey_outcome_order_ascending(outcomes: Iterable[_T]) -> list[_T]:
    r"""
    Sorts *outcomes* in ascending order using native comparison, falling back to [`natural_key`][dyce.types.natural_key] when outcomes are mutually incomparable.
    """
    result = list(outcomes)
    try:
        result.sort()  # pyrefly: ignore[bad-specialization] # pyright: ignore[reportCallIssue] # ty: ignore[invalid-argument-type]
    except TypeError:
        result.sort(key=natural_key)
    return result


def survey_outcome_order_descending(outcomes: Iterable[_T]) -> list[_T]:
    r"""
    Sorts *outcomes* in descending order using native comparison, falling back to [`natural_key`][dyce.types.natural_key] when outcomes are mutually incomparable.
    """
    result = list(outcomes)
    try:
        result.sort(reverse=True)  # pyrefly: ignore[bad-specialization,no-matching-overload] # pyright: ignore[reportCallIssue] # ty: ignore[invalid-argument-type]
    except TypeError:
        result.sort(key=natural_key, reverse=True)
    return result

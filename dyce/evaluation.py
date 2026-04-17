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

import sys
import warnings
from collections.abc import Callable, Iterable, Iterator
from contextvars import ContextVar
from enum import IntEnum, auto
from fractions import Fraction
from itertools import product as iproduct
from math import prod
from typing import Any, Generic, NamedTuple, TypeVar, overload

from dyce.types import natural_key, nobeartype

from .h import H
from .lifecycle import ExperimentalWarning, experimental, experimental_msg
from .p import P

__all__ = ("HResult", "PResult", "TruncationWarning", "expand", "explode_n")

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_ResultT = TypeVar("_ResultT")


class TruncationWarning(UserWarning):
    r"""
    Issued when results are truncated from [`expand`][dyce.expand] for whatever reason.
    """


class HResult(NamedTuple, Generic[_T]):
    r"""
    Container passed to an [`expand`][dyce.expand] callback when the corresponding source is an [`H`][dyce.H] object.
    """

    h: H[_T]
    outcome: _T


class PResult(NamedTuple, Generic[_T]):
    r"""
    Container passed to an [`expand`][dyce.expand] callback when the corresponding source is a [`P`][dyce.P] object.
    """

    p: P[_T]
    roll: tuple[_T, ...]


class _ExpandContext(NamedTuple):
    path_probability: Fraction
    precision: Fraction


class _TruncationReason(IntEnum):
    PROB_BDGT_EXHAUSTED = auto()
    RCRS_LMT_EXCEEDED = auto()


_DEFAULT_PRECISION: Fraction = Fraction(1, 0x7FFFFF)
_expand_ctxt: ContextVar[_ExpandContext] = ContextVar("_DYCE_EXPAND_CONTEXT")


@overload
def expand(
    callback: Callable[[HResult[_T]], H[_ResultT] | _ResultT],
    source: H[_T],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[[PResult[_T]], H[_ResultT] | _ResultT],
    source: P[_T],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[[HResult[_T1], HResult[_T2]], H[_ResultT] | _ResultT],
    source1: H[_T1],
    source2: H[_T2],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[[HResult[_T1], PResult[_T2]], H[_ResultT] | _ResultT],
    source1: H[_T1],
    source2: P[_T2],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[[PResult[_T1], HResult[_T2]], H[_ResultT] | _ResultT],
    source1: P[_T1],
    source2: H[_T2],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[[PResult[_T1], PResult[_T2]], H[_ResultT] | _ResultT],
    source1: P[_T1],
    source2: P[_T2],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [HResult[_T1], HResult[_T2], HResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: H[_T1],
    source2: H[_T2],
    source3: H[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [HResult[_T1], HResult[_T2], PResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: H[_T1],
    source2: H[_T2],
    source3: P[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [HResult[_T1], PResult[_T2], HResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: H[_T1],
    source2: P[_T2],
    source3: H[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [HResult[_T1], PResult[_T2], PResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: H[_T1],
    source2: P[_T2],
    source3: P[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [PResult[_T1], HResult[_T2], HResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: P[_T1],
    source2: H[_T2],
    source3: H[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [PResult[_T1], HResult[_T2], PResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: P[_T1],
    source2: H[_T2],
    source3: P[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [PResult[_T1], PResult[_T2], HResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: P[_T1],
    source2: P[_T2],
    source3: H[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[
        [PResult[_T1], PResult[_T2], PResult[_T3]], H[_ResultT] | _ResultT
    ],
    source1: P[_T1],
    source2: P[_T2],
    source3: P[_T3],
    *,
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[_ResultT]: ...
@overload
def expand(
    callback: Callable[..., Any],
    *sources: H[Any] | P[Any],
    precision: Fraction = ...,
    **state: Any,  # noqa: ANN401
) -> H[Any]: ...
def expand(
    callback: Callable[..., Any],
    *sources: H[Any] | P[Any],
    precision: Fraction = _DEFAULT_PRECISION,
    **state: Any,
) -> H[Any]:
    r"""
    !!! warning "Experimental"

        `expand` is experimental; its interface may change or it may be removed in a future release.

    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

       -- END MONKEY PATCH -->

    Evaluate *callback* over the Cartesian product of all *sources*, accumulating the results into an [`H`][dyce.H] object.

    For each combination of outcomes drawn from *sources*, *callback* is called with one positional [`HResult`][dyce.HResult] or [`PResult`][dyce.PResult] argument pe [`H`][dyce.H] or [`P`][dyce.P] source, respectively, plus any provided keyword arguments.
    The return value controls how the branch contributes to the accumulation:

    - **Scalar** — The outcome is recorded directly.
    - **[`H`][dyce.H]** — The histogram is expanded in place, meaning its outcomes are merged into the accumulation with their counts scaled to preserve the correct proportions.
    - **`#!python H({})` (the empty histogram)** — The branch is *eliminated*, meaning it contributes nothing to the accumulation and is silently discarded.
      This is the designated mechanism for signaling that an outcome is impossible or should be excluded from the result.

    This is useful for modeling mechanics where the outcome of one die affects how others are rolled
    Examples include: exploding dice, conditional re-rolls, or damage that depends on whether an attack hits.

    Re-roll an initial 1:

        >>> from dyce import H
        >>> from dyce.evaluation import HResult, expand

        >>> def reroll_first_one(result: HResult[int]) -> H[int] | int:
        ...     return result.h if result.outcome == 1 else result.outcome

        >>> expand(reroll_first_one, H(6))
        H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

    Returning an [`H`][dyce.H] expands the branch in place, with counts scaled to preserve proportions relative to the whole.
    Substituting a d00 for a 1 on a d6:

        >>> from fractions import Fraction
        >>> d00 = (H(10) - 1) * 10
        >>> set(H(6)) & set(d00)  # no outcomes in common
        set()

        >>> def roll_d00_on_one(result: HResult[int]) -> H[int] | int:
        ...     return d00 if result.outcome == 1 else result.outcome

        >>> d6_d00 = expand(roll_d00_on_one, H(6))
        >>> d6_d00
        H({0: 1, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10, 10: 1, 20: 1, 30: 1, 40: 1, 50: 1, 60: 1, 70: 1, 80: 1, 90: 1})

    The ten d00 outcomes together make up the same proportion of the total as the original 1 did in the d6:

        >>> Fraction(
        ...     sum(count for outcome, count in d6_d00.items() if outcome in d00),
        ...     d6_d00.total,
        ... )
        Fraction(1, 6)
        >>> Fraction(H(6)[1], H(6).total)
        Fraction(1, 6)

    When the intent is that a whole path be *eliminated* (not merely approximated), returning `#!python H({})` from a recursive call propagates naturally through arithmetic (`#!python H({}) + outcome` is `#!python H({})`), and no special check is needed.

    Re-roll *all* 1s:

        >>> def always_reroll_on_one(result: HResult[int]) -> H[int] | int:
        ...     return H({}) if result.outcome == 1 else result.outcome

        >>> expand(always_reroll_on_one, H(6))
        H({2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    **Precision and recursion limiting**

    The *precision* parameter controls when recursive expansion is stopped automatically.
    It represents the minimum path probability—the cumulative probability of reaching a branch—below which the callback is not invoked.
    Additionally, any branch that exceeds Python’s recursion limit is also dropped.
    In both cases, the branch is eliminated exactly as if the callback had returned `#!python H({})`.
    A [`TruncationWarning`][dyce.TruncationWarning] is emitted when any branch is dropped this way, distinguishing resource-limit elimination from intentional callback-driven elimination.

    *precision* is set by the outermost `expand` call and propagated automatically to all recursive calls via a context variable.

    !!! warning "*precision* is ***not*** overridden during recursion"

        Passing *precision* in a recursive call has no effect.
        The value from the outermost call is *always* used.

    Because *precision* is path-probability-based, the same threshold produces different recursion depths depending on how likely the exploding face is.
    A heavier exploding face keeps branches above the threshold longer:

        >>> from dyce import TruncationWarning

        >>> def explode_on_max(result: HResult[int]) -> H[int] | int:
        ...     if result.outcome == max(result.h):
        ...         inner = expand(explode_on_max, result.h)
        ...         return (inner + result.outcome) if inner else result.outcome
        ...     return result.outcome

        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always", category=TruncationWarning)
        ...     expand(
        ...         explode_on_max,
        ...         H({1: 1, 2: 3}),
        ...         precision=Fraction(1, 16),
        ...     )
        H({1: 256, 3: 192, 5: 144, 7: 108, 9: 81, 18: 243})
        >>> caught and all(w.category is TruncationWarning for w in caught)
        True

        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always", category=TruncationWarning)
        ...     expand(
        ...         explode_on_max,
        ...         H({1: 3, 2: 1}),
        ...         precision=Fraction(1, 16),
        ...     )
        H({1: 12, 3: 3, 4: 1})
        >>> caught and all(w.category is TruncationWarning for w in caught)
        True

    **Arbitrary state threading**

    Any keyword arguments beyond *precision* are forwarded verbatim to *callback* as keyword-only arguments.
    To pass updated state into recursive calls, include it explicitly:

        >>> def explode_on_max_up_to_n_times(
        ...     result: HResult, *, n: int
        ... ) -> H[int] | int:
        ...     if n > 0 and result.outcome == max(result.h):
        ...         inner = expand(explode_on_max_up_to_n_times, result.h, n=n - 1)
        ...         if inner:
        ...             return inner + result.outcome
        ...     return result.outcome

        >>> expand(
        ...     explode_on_max_up_to_n_times,
        ...     H(10),
        ...     n=0,  # just the first roll with zero explosions
        ... ) == H(10)
        True

        >>> expand(
        ...     explode_on_max_up_to_n_times,
        ...     H(10),
        ...     n=4,  # up to four explosions (five total rolls)
        ... )
        H({1: 10000, ..., 9: 10000, 11: 1000, ..., 19: 1000, 21: 100, ..., 29: 100, 31: 10, ..., 39: 10, 41: 1, ..., 49: 1, 50: 1})

    **Multiple sources**

    When multiple sources are provided, *callback* receives one positional argument per source.
    Counting how often a d6 beats each outcome of a 2d10 pool:

        >>> from dyce import P
        >>> from dyce.evaluation import PResult
        >>> p_2d10 = 2 @ P(10)

        >>> def times_d6_beats_two_d10s(
        ...     d6_result: HResult[int],
        ...     p_result: PResult[int],
        ... ) -> int:
        ...     return sum(
        ...         1 for outcome in p_result.roll if outcome < d6_result.outcome
        ...     )

        >>> expand(times_d6_beats_two_d10s, H(6), p_2d10)
        H({0: 71, 1: 38, 2: 11})

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->
    """
    if not sources:
        raise ValueError("expand requires at least one source")
    try:
        cur_ctxt = _expand_ctxt.get()
    except LookupError:
        # TODO(posita): https://github.com/astral-sh/ty/issues/2278 - try the
        # @experimental decorator instead once that issue is fixed
        warnings.warn(experimental_msg % "expand", ExperimentalWarning, stacklevel=2)
        cur_ctxt = _ExpandContext(
            path_probability=Fraction(1),
            precision=precision,
        )

    current_path_prob = cur_ctxt.path_probability
    effective_precision = cur_ctxt.precision
    total_product = prod(s.total for s in sources)
    truncation_reasons: set[_TruncationReason] = set()

    def _gen() -> Iterator[tuple[Any, int]]:
        for result_counts in iproduct(
            *(_source_to_result_iterable(s) for s in sources)
        ):
            results, counts = zip(*result_counts, strict=True)
            combined_count = prod(counts)
            branch_path_prob = current_path_prob * Fraction(
                combined_count, total_product
            )
            if branch_path_prob < effective_precision:
                truncation_reasons.add(_TruncationReason.PROB_BDGT_EXHAUSTED)
                continue
            new_ctxt = _ExpandContext(
                path_probability=branch_path_prob,
                precision=effective_precision,
            )
            token = _expand_ctxt.set(new_ctxt)
            try:
                result = callback(*results, **state)
            except RecursionError:
                truncation_reasons.add(_TruncationReason.RCRS_LMT_EXCEEDED)
                continue
            finally:
                _expand_ctxt.reset(token)
            yield result, combined_count

    h = aggregate_weighted(_gen())
    if _TruncationReason.PROB_BDGT_EXHAUSTED in truncation_reasons:
        warnings.warn(
            f"expand: some branches with path probability < {effective_precision!r} "
            f"were truncated",
            TruncationWarning,
            stacklevel=2,
        )
    if _TruncationReason.RCRS_LMT_EXCEEDED in truncation_reasons:
        warnings.warn(
            f"expand: some branches whose recursion depth exceeded "
            f"{sys.getrecursionlimit()} were truncated",
            TruncationWarning,
            stacklevel=2,
        )

    if current_path_prob == Fraction(1):
        return h.lowest_terms()
    return h


@nobeartype
def _explode_on_max(result: HResult[_T], _n_left: int, _n_done: int) -> H[_T] | _T:
    try:
        max_result = max(result.h)  # type: ignore[type-var]
    except TypeError:
        max_result = max(result.h, key=natural_key)
    return result.h if bool(result.outcome == max_result) else result.outcome


@experimental
def explode_n(
    source: H[_T],
    *,
    n: int = 1,
    precision: Fraction = Fraction(0),
    resolver: Callable[[HResult[_T], int, int], H[_T] | _T] = _explode_on_max,
) -> H[_T]:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
    >>> import sympy  # type: ignore [import-untyped]

       -- END MONKEY PATCH -->

    Convenience wrapper around [`expand`][dyce.expand] for exploding dice.
    *resolver* can return either a histogram to indicate the next die to be rolled and accumulated (up to *n* times) or an outcome.
    The default *resolver* explodes on the maximum face.

        >>> from dyce import H, HResult, explode_n
        >>> d6 = H(6)
        >>> explode_n(d6, n=2)
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})

    <!-- -->

        >>> import sympy
        >>> x = sympy.sympify("x")
        >>> explode_n(H({x: 1}), n=0)  # zero explosions is the starting roll
        H({x: 1})
        >>> explode_n(H({x: 1}), n=2)  # starting roll with up to two explosions
        H({3*x: 1})

    *precision* is forwarded to the outermost [`expand`][dyce.expand] call.
    (See that function for details.)
    With sufficient large values for *n*, a [`TruncationWarning`][dyce.TruncationWarning] will be emitted for branches dropped by exhausting any precision budget.

        >>> from dyce import TruncationWarning
        >>> import sys
        >>> from fractions import Fraction
        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always", TruncationWarning)
        ...     explode_n(
        ...         d6,
        ...         n=sys.maxsize,
        ...         precision=Fraction(1, 6**3),
        ...     )
        H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})
        >>> caught and all(w.category is TruncationWarning for w in caught)
        True

        >>> from typing import TypeVar
        >>> T = TypeVar("T")

        >>> def explode_on_even_resolver(
        ...     result: HResult[T], n_left: int, n_done: int
        ... ) -> H[T] | T:
        ...     return result.h if result.outcome % 2 == 0 else result.outcome  # type: ignore[operator] # ty: ignore[unsupported-operator]

        >>> with warnings.catch_warnings(record=True) as caught:
        ...     warnings.simplefilter("always", TruncationWarning)
        ...     explode_n(
        ...         d6,
        ...         n=sys.maxsize,
        ...         precision=Fraction(1, 6**3),
        ...         resolver=explode_on_even_resolver,
        ...     )
        H({1: 36, 3: 42, 5: 49, 6: 1, 7: 21, 8: 3, 9: 18, 10: 6, 11: 13, 12: 7, 13: 6, 14: 6, 15: 3, 16: 3, 17: 1, 18: 1})
        >>> caught and all(w.category is TruncationWarning for w in caught)
        True

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->
    """

    @nobeartype
    def _callback(result: HResult[_T], *, n_left: int) -> H[_T] | _T:
        if n_left <= 0:
            return result.outcome
        next_h_or_outcome = resolver(result, n_left, n - n_left)
        if isinstance(next_h_or_outcome, H):
            inner = expand(_callback, next_h_or_outcome, n_left=n_left - 1)
            return inner + result.outcome if inner else result.outcome
        return next_h_or_outcome

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ExperimentalWarning)
        return expand(_callback, source, n_left=n, precision=precision)


# ---- Helpers -------------------------------------------------------------------------


# TODO(posita): https://github.com/facebook/pyrefly/issues/3002> - weighted_sources
# should become `Iterable[tuple[H[_T] | _T, int]]` once that issue is fixed
@overload
def aggregate_weighted(
    weighted_sources: Iterable[tuple[H[_T] | _T, int]], /
) -> H[_T]: ...
@overload
def aggregate_weighted(weighted_sources: Iterable[tuple[Any, int]], /) -> H[Any]: ...
def aggregate_weighted(
    weighted_sources: Iterable[tuple[Any, int]],
) -> H[Any]:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

       -- END MONKEY PATCH -->

    Aggregate *weighted_sources* into an [`H`][dyce.H] object.

    Each element of *weighted_sources* is a two-tuple of either an `#!python (outcome, count)` pair or an `#!python (H, count)` pair.
    When a source is an [`H`][dyce.H], its total takes on the weight of *count*.
    When a source is the empty histogram (`#!python H({})`), it and its count are omitted without scaling.

    This function is the accumulation engine used by [`expand`][dyce.expand].

        >>> from dyce import H
        >>> from dyce.evaluation import aggregate_weighted
        >>> aggregate_weighted(
        ...     (
        ...         (H({1: 1}), 1),
        ...         (H({1: 1, 2: 2}), 2),
        ...     )
        ... )
        H({1: 5, 2: 4})
        >>> aggregate_weighted(((H(2), 1), (H({}), 20)))
        H({1: 1, 2: 1})

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->
    """
    aggregate_scalar = 1
    outcome_counts: list[tuple[Any, int]] = []

    for outcome_or_h, count in weighted_sources:
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

    return H.from_counts(outcome_counts)


def _source_to_result_iterable(
    source: H[Any] | P[Any],
) -> Iterator[tuple[HResult[Any] | PResult[Any], int]]:
    if isinstance(source, H):
        for outcome, count in source.items():
            yield HResult(source, outcome), count
    elif isinstance(source, P):
        for roll, count in source.rolls_with_counts():
            yield PResult(source, roll), count
    else:
        raise TypeError(
            f"unrecognized source type {type(source).__qualname__!r} ({source!r})"
        )

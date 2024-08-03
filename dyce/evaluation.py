# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import sys
from contextvars import ContextVar
from fractions import Fraction
from functools import wraps
from itertools import chain, product
from math import prod
from typing import (
    Callable,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from numerary import IntegralLike, RealLike
from numerary.bt import beartype
from numerary.types import (
    CachingProtocolMeta,
    Protocol,
    RationalLikeMixedT,
    RationalLikeMixedU,
    denominator,
    numerator,
)

from .h import H, HableT, HOrOutcomeT, _OutcomeCountT, _SourceT
from .lifecycle import experimental
from .p import P, RollT
from .types import _GetItemT, as_int

__all__ = ()


# ---- Types ---------------------------------------------------------------------------


class HResult(NamedTuple):
    h: H
    outcome: RealLike


class PResult(NamedTuple):
    p: P
    roll: RollT


class PWithSelection(NamedTuple):
    p: P
    which: Iterable[_GetItemT] = ()

    @property
    def total(self) -> int:
        return self.p.total


LimitT = Union[IntegralLike, RationalLikeMixedU, RealLike]
_NormalizedLimitT = Union[int, Fraction]
_ReturnsHOrOutcomeT = Callable[..., HOrOutcomeT]
_DependentTermT = TypeVar("_DependentTermT", bound=_ReturnsHOrOutcomeT)
_POrPWithSelectionOrSourceT = Union[P, PWithSelection, _SourceT]
_PredicateT = Callable[[HResult], bool]
_HResultCountT = Tuple[HResult, int]
_PResultCountT = Tuple[PResult, int]


class _Context(NamedTuple):
    normalized_limit: Optional[_NormalizedLimitT] = None
    contextual_depth: int = 0
    contextual_precision: Fraction = Fraction(1)


class _ForEachEvaluatorT(Protocol, metaclass=CachingProtocolMeta):
    def __call__(
        self,
        *args: _POrPWithSelectionOrSourceT,
        limit: Optional[LimitT] = None,
        **kw: _POrPWithSelectionOrSourceT,
    ) -> H: ...


# ---- Data ----------------------------------------------------------------------------


_DEFAULT_LIMIT: _NormalizedLimitT = 1
_DEFAULT_SENTINEL = H({0: 1})

_expandable_ctxt: ContextVar[_Context] = ContextVar("DYCE_EXPANDABLE_CONTEXT")


# ---- Decorators ----------------------------------------------------------------------


@overload
def expandable(
    *,
    sentinel: H = _DEFAULT_SENTINEL,
) -> Callable[[_DependentTermT], _ForEachEvaluatorT]: ...


@overload
def expandable(
    f: _DependentTermT,
    *,
    sentinel: H = _DEFAULT_SENTINEL,
) -> _ForEachEvaluatorT: ...


@experimental
@beartype
def expandable(
    f: Optional[_DependentTermT] = None,
    *,
    sentinel: H = _DEFAULT_SENTINEL,
) -> Union[Callable[[_DependentTermT], _ForEachEvaluatorT], _ForEachEvaluatorT]:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Calls ``#!python dependent_term`` for each set of outcomes from the product of any
    independent sources provided to the decorated function and accumulates the results.
    Independent sources are [``H`` objects][dyce.h.H], [``P`` objects][dyce.p.P], or
    [``PWithSelection`` wrapper objects][dyce.evaluation.PWithSelection]. Results are
    passed to ``#!python dependent_term`` via
    [``HResult`` objects][dyce.evaluation.HResult] or
    [``PResult`` objects][dyce.evaluation.PResult], corresponding to the respective
    independent term. This is useful for resolving dependent probabilities. Returned
    histograms are always reduced to their lowest terms.

    For example, let’s say we’re rolling a d20 but want to re-roll a ``#!python 1`` if
    it comes up, then keep the result.

    ``` python
    >>> from dyce import H
    >>> from dyce.evaluation import HResult, expandable

    >>> @expandable
    ... def reroll_on_one(h_result: HResult):
    ...   if h_result.outcome == 1:
    ...     return h_result.h
    ...   else:
    ...     return h_result.outcome

    >>> reroll_on_one(H(20))
    H({1: 1,
     2: 21,
     3: 21,
     4: 21,
     ...,
     18: 21,
     19: 21,
     20: 21})
    >>> reroll_on_one(H(6))
    H({1: 1, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7})

    ```

    When the decorated function returns an [``H`` object][dyce.h.H], that histogram’s
    outcomes are accumulated, but the counts retain their “scale” within the context of
    the evaluation. This becomes clearer when there is no overlap between the evaluated
    histogram and the other outcomes.

    ``` python
    >>> d6 = H(6)
    >>> d00 = (H(10) - 1) * 10 ; d00
    H({0: 1, 10: 1, 20: 1, 30: 1, 40: 1, 50: 1, 60: 1, 70: 1, 80: 1, 90: 1})
    >>> set(d6) & set(d00) == set()  # no outcomes in common
    True

    >>> @expandable
    ... def roll_d00_on_one(h_result: HResult):
    ...   # If a 1 comes up when rolling the d6,
    ...   # roll a d00 and take that result instead
    ...   return d00 if h_result.outcome == 1 else h_result.outcome

    >>> d6_d00 = roll_d00_on_one(d6) ; d6_d00
    H({0: 1,
     2: 10,
     3: 10,
     4: 10,
     5: 10,
     6: 10,
     10: 1,
     20: 1,
     30: 1,
     40: 1,
     50: 1,
     60: 1,
     70: 1,
     80: 1,
     90: 1})

    ```

    Note that the sum of the outcomes’ counts from the d00 make up the same
    proportion as the one’s outcome and count they replaced from the d6.

    ``` python
    >>> Fraction(
    ...   sum(count for outcome, count in d6_d00.items() if outcome in d00),
    ...   d6_d00.total,
    ... )
    Fraction(1, 6)
    >>> Fraction(d6[1], d6.total)
    Fraction(1, 6)

    ```

    We can leverage this to compute distributions for an “exploding” die (i.e.,
    re-rolling and adding when rolling its highest face).

    ``` python
    >>> @expandable
    ... def explode_once(h_result: HResult):
    ...   if h_result.outcome == max(h_result.h):
    ...     return h_result.h + h_result.outcome
    ...   else:
    ...     return h_result.outcome

    >>> explode_once(H(6))
    H({1: 6, 2: 6, 3: 6, 4: 6, 5: 6, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1})
    >>> explode_once(H(20))
    H({1: 20,
       2: 20,
       ...,
       18: 20,
       19: 20,
       21: 1,
       22: 1,
       ...,
       39: 1,
       40: 1})

    ```

    ``#!python @expandable`` functions can call themselves recursively. They take a
    *limit* keyword argument to control when such recursion should stop. The decorator
    itself takes an optional argument *sentinel*, which defines what is returned once
    *limit* is reached (or a ``#!python RecursionError`` is encountered, whichever comes
    first). The default value for *sentinel* is ``#!python H({0: 1})`` and the value
    ascribed to *limit*, if not provided, is ``#!python 1``.

    If *limit* is a whole number, it defines the maximum recursive evaluation “depth”.
    The way to express no recursion (i.e., merely return *sentinel*) is to set *limit*
    to an integral value of ``#!python 0``. An integral value of ``#!python -1`` is
    equivalent to setting it to ``#!python sys.maxsize``.[^1]

    [^1]:

        An integral *limit* in the low-to-mid single digits is often more than
        sufficient to exceed a useful precision. Consider starting small and edging up
        incrementally to avoid protracted execution times. Consider:

        ``` python
        >>> @expandable
        ... def wicked_explode(h_result: HResult):
        ...   if h_result.outcome == max(h_result.h):
        ...     # Replace a high roll with two recursively exploding dice
        ...     return wicked_explode(h_result.h) + wicked_explode(h_result.h)
        ...   else:
        ...     return h_result.outcome

        >>> h = wicked_explode(H(6), limit=6)
        >>> print(f"Likelihood of making {max(h)}: {h[max(h)] / h.total:.50%}")
        Likelihood of making 160: 0.00000000000000000000000000000000000000000000000947%

        ```

        The above *limit* is tolerable for modern computing devices, but much more might
        render it intractable.

    ``` python
    >>> def explode_recursive(h: H, limit=None) -> H:
    ...
    ...   @expandable(sentinel=h)  # return the original histogram at the recursion limit
    ...   def _expand(h_result: HResult):
    ...     return _expand(h_result.h) + h_result.outcome if h_result.outcome == max(h_result.h) else h_result.outcome
    ...
    ...   return _expand(h, limit=limit)

    >>> explode_recursive(H(6), limit=1) == explode_once(H(6))
    True
    >>> explode_recursive(H(6), limit=0) == H(6)  # return the sentinel without evaluation
    True
    >>> exploded_d6_h = explode_recursive(H(6), limit=2) ; exploded_d6_h
    H({1: 36,
     2: 36,
     3: 36,
     4: 36,
     5: 36,
     7: 6,
     8: 6,
     9: 6,
     10: 6,
     11: 6,
     13: 1,
     14: 1,
     15: 1,
     16: 1,
     17: 1,
     18: 1})

    ```

    If *limit* is a fractional value between zero and one, exclusive, recursion will
    halt on any branch whose “contextual precision” is less than or equal to that value.
    Recursion is attempted for all of the outcomes of a(n evaluated) histogram or none
    of them. The contextual precision of a returned histogram is its proportion to the
    whole.

    The contextual precision of the original (or top-level) execution is ``#!python
    Fraction(1, 1)`` or ``#!python 1.0``. A *limit* of either of those values would
    theoretically ensure no substitution. Similarly, a fractional value for *limit* of
    ``#!python Fraction(0, 1)`` or ``#!python 0.0`` would theoretically ensure there is
    no limit. However, These expressions would likely lead to confusion because they
    have different meanings than equivalent integral values for *limit*. This is why
    fractional types with values equivalent to zero and one are not allowed.

    ``` python
    >>> from fractions import Fraction
    >>> explode_recursive(H(6), limit=Fraction(1, 6 ** 2)) == exploded_d6_h
    True

    ```

    While whole number *limit* values will always cut off recursion at a constant depth,
    fractional *limit* values can skew results in favor of certain recursion branches.
    This is easily demonstrated when examining “unfair” dice (i.e., those
    disproportionately weighted toward particular faces).

    ``` python
    >>> explode_recursive(H({1: 1, 2: 19}), limit=3)
    H({1: 8000, 3: 7600, 5: 7220, 7: 6859, 8: 130321})
    >>> explode_recursive(H({1: 19, 2: 1}), limit=3)  # same depth
    H({1: 152000, 3: 7600, 5: 380, 7: 19, 8: 1})

    >>> explode_recursive(H({1: 1, 2: 19}), limit=Fraction(9, 10))
    H({1: 8000, 3: 7600, 5: 7220, 7: 6859, 8: 130321})
    >>> explode_recursive(H({1: 19, 2: 1}), limit=Fraction(9, 10))  # same limit, different depth
    H({1: 380, 3: 19, 4: 1})

    ```

    Be aware that some recursions are guaranteed to result in maxing out the stack, even
    with fractional values for *limit* that are very close to one. We can often guard
    against this by short-circuiting recursion where we know the evaluated contextual
    probabilities do not asymptotically approach zero (e.g., where an entire branch
    reliably generates histograms with precisely one outcome).

    ``` python
    >>> def guarded_explode(h: H, limit=None) -> H:
    ...
    ...   @expandable(sentinel=h)
    ...   def _expand(h_result: HResult):
    ...     if len(h_result.h) == 1:
    ...       raise ValueError("cannot explode a histogram with a single outcome")
    ...     elif h_result.outcome == max(h_result.h):
    ...       return _expand(h_result.h) + h_result.outcome
    ...     else:
    ...       return h_result.outcome
    ...
    ...   return _expand(h, limit=limit)

    >>> guarded_explode(H(1), limit=Fraction(999_999, 1_000_000))
    Traceback (most recent call last):
      ...
    ValueError: cannot explode a histogram with a single outcome

    ```

    We can also evaluate multiple independent sources. For example, let’s say we want to
    understand when a d6 will beat each face on two d10s. We can use a nested function
    to also allow for a penalty or bonus modifier to the d6.

    ``` python
    >>> from dyce import P
    >>> from dyce.evaluation import PResult
    >>> p_2d10 = 2@P(10)

    >>> def times_a_modded_d6_beats_two_d10s(mod: int = 0) -> H:
    ...
    ...   @expandable
    ...   def _expand(d6: HResult, p_2d10: PResult):
    ...     return sum(1 for outcome in p_2d10.roll if outcome < d6.outcome + mod)
    ...
    ...   return _expand(H(6), p_2d10)

    >>> times_a_modded_d6_beats_two_d10s()
    H({0: 71, 1: 38, 2: 11})
    >>> times_a_modded_d6_beats_two_d10s(mod=-1)
    H({0: 43, 1: 14, 2: 3})
    >>> times_a_modded_d6_beats_two_d10s(mod=+2)
    H({0: 199, 1: 262, 2: 139})

    ```

    Now let’s say we want to introduce the concept of an “advantage” or “disadvantage”
    to the above, meaning we roll an extra d10 that can further penalize or benefit us.
    We *could* just roll 3d10 and look at the best or worst two of each roll.


    ``` python
    >>> from enum import Enum, auto
    >>> p_3d10 = 3@P(10)

    >>> class Advantage(Enum):
    ...   DISADVANTAGE = auto()
    ...   NORMAL = auto()
    ...   ADVANTAGE = auto()

    >>> def times_a_modded_d6_beats_two_d10s_w_adv_brute_force(mod: int = 0, adv: Advantage = Advantage.NORMAL) -> H:
    ...
    ...   @expandable
    ...   def _expand(d6: HResult, p_d10s: PResult):
    ...     if adv is Advantage.ADVANTAGE:
    ...       roll = p_d10s.roll[:2]  # try to beat the worst two values
    ...     elif adv is Advantage.DISADVANTAGE:
    ...       roll = p_d10s.roll[-2:]  # try to beat the best two values
    ...     else:
    ...       roll = p_d10s.roll
    ...     return sum(1 for outcome in roll if outcome < d6.outcome + mod)
    ...
    ...   if adv is Advantage.NORMAL:
    ...     return _expand(H(6), p_2d10)
    ...   else:
    ...     return _expand(H(6), p_3d10)

    >>> times_a_modded_d6_beats_two_d10s_w_adv_brute_force() == times_a_modded_d6_beats_two_d10s()
    True
    >>> times_a_modded_d6_beats_two_d10s_w_adv_brute_force(adv=Advantage.ADVANTAGE)
    H({0: 39, 1: 25, 2: 16})
    >>> times_a_modded_d6_beats_two_d10s_w_adv_brute_force(adv=Advantage.DISADVANTAGE)
    H({0: 64, 1: 13, 2: 3})

    ```

    However, we could be more computationally more efficient by narrowing our selection
    before we get to our evaluation function. We do this using
    [``PWithSelection`` objects][dyce.evaluation.PWithSelection] whose ``#!python
    PWithSelection.which`` values are passed to the
    [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts] method when enumerating the
    rolls.

    ``` python
    >>> from dyce.evaluation import PWithSelection

    >>> def times_a_modded_d6_beats_two_d10s_w_adv(mod: int = 0, adv: Advantage = Advantage.NORMAL) -> H:
    ...
    ...   @expandable
    ...   def _expand(d6: HResult, p_d10s: PResult):
    ...     return sum(1 for outcome in p_d10s.roll if outcome < d6.outcome + mod)
    ...
    ...   if adv is Advantage.ADVANTAGE:
    ...     return _expand(H(6), PWithSelection(p_3d10, (0, 1)))  # pass only the worst two values
    ...   elif adv is Advantage.DISADVANTAGE:
    ...     return _expand(H(6), PWithSelection(p_3d10, (-2, -1)))  # pass only the best two values
    ...   else:
    ...     return _expand(H(6), p_2d10)

    >>> times_a_modded_d6_beats_two_d10s_w_adv() == times_a_modded_d6_beats_two_d10s()
    True
    >>> times_a_modded_d6_beats_two_d10s_w_adv(adv=Advantage.ADVANTAGE)
    H({0: 39, 1: 25, 2: 16})
    >>> times_a_modded_d6_beats_two_d10s_w_adv(adv=Advantage.DISADVANTAGE)
    H({0: 64, 1: 13, 2: 3})

    ```

    This function uses the [``aggregate_weighted``][dyce.evaluation.aggregate_weighted]
    function in its implementation. As such, if the empty histogram (``H({})``) is
    returned at any point, the corresponding branch and its count is omitted from the
    result without substitution or scaling. A silly example is modeling a d5 by
    indefinitely re-rolling a d6 until something other than a 6 comes up.

    ``` python
    >>> @expandable
    ... def omit_6s(h_result: HResult):
    ...   return H({}) if h_result.outcome == 6 else h_result.outcome

    >>> omit_6s(H(6))
    H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1})

    ```

    This technique is more useful when modeling re-rolling certain derived outcomes,
    like ties in a contest.

    ``` python
    >>> @expandable
    ... def vs(attack: HResult, defend: HResult):
    ...   return (attack.outcome > defend.outcome) - (attack.outcome < defend.outcome)

    >>> vs(3@H(6), 2@H(8))
    H({-1: 4553, 0: 1153, 1: 8118})

    >>> @expandable
    ... def vs_reroll_ties(attack: HResult, defend: HResult):
    ...   res = (attack.outcome > defend.outcome) - (attack.outcome < defend.outcome)
    ...   return H({}) if res == 0 else res

    >>> vs_reroll_ties(3@H(6), 2@H(8))
    H({-1: 4553, 1: 8118})

    ```

    Expandables are quite flexible and well suited to modeling logical progressions with
    dependent variables. Consider the following mechanic:

      1. Start with a total of zero.

      2. Roll a six-sided die. If the face was a six, go to step 3. Otherwise, add the
         face to the total and stop.

      3. Roll a four-sided die. Add the face to the total. If the face was a one, go to
         step 2. Otherwise, stop.

    What is the likelihood of an even final tally? This can be approximated by:

    ``` python
    >>> def alternating_d6_d4_mechanic(limit=None) -> H:
    ...   d4, d6 = H(4), H(6)
    ...
    ...   @expandable
    ...   def _expand(h_result: HResult):
    ...     if h_result.h == d6 and h_result.outcome == 6:
    ...       return _expand(d4)
    ...     elif h_result.h == d4 and h_result.outcome == 1:
    ...       return h_result.outcome + _expand(d6)
    ...     else:
    ...       return h_result.outcome
    ...
    ...   return _expand(d6, limit=limit)

    >>> h = alternating_d6_d4_mechanic(limit=Fraction(1, 5_000))
    >>> print(h.format(scaled=True))
    avg |    3.04
    std |    1.37
    var |    1.87
      1 |  16.67% |######################################
      2 |  21.53% |#################################################
      3 |  21.74% |##################################################
      4 |  21.74% |##################################################
      5 |  17.57% |########################################
      6 |   0.73% |#
      7 |   0.03% |
    >>> h_even = h.is_even()
    >>> print(f"{h_even[True] / h_even.total:.2%}")
    44.00%

    ```

    We can also use this decorator to help model expected damage from a single attack in
    d20-like role playing games.

    ``` python
    >>> def expected_dmg_from_attack_roll(dmg_h, dmg_bonus, target):
    ...   normal_dmg = dmg_h + dmg_bonus
    ...   crit_dmg = 2@dmg_h + dmg_bonus
    ...
    ...   @expandable
    ...   def _expand(attack: HResult):
    ...     if attack.outcome == 20:
    ...       return crit_dmg
    ...     elif attack.outcome >= target:
    ...       return normal_dmg
    ...     else:
    ...       return 0
    ...
    ...   return _expand(H(20))

    >>> h = expected_dmg_from_attack_roll(dmg_h=H(8), dmg_bonus=+1, target=14)
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

    !!! info "On the current implementation"

        This decorator relies on [context
        variables](https://docs.python.org/3/library/contextvars.html) for enforcing
        limits without requiring decorated functions to explicitly propagate additional
        state.
    """

    def _decorator(f):
        @wraps(f)
        def _f(
            *args: _POrPWithSelectionOrSourceT,
            limit: Optional[LimitT] = None,
            **kw: _POrPWithSelectionOrSourceT,
        ) -> H:
            try:
                cur_ctxt = _expandable_ctxt.get()
            except LookupError:
                cur_ctxt = _Context()

            callback = f

            if limit is None:
                new_norm_limit = (
                    _DEFAULT_LIMIT
                    if cur_ctxt.normalized_limit is None
                    else _normalize_limit(cur_ctxt.normalized_limit)
                )
            else:
                new_norm_limit = _normalize_limit(limit)

            if (
                isinstance(new_norm_limit, int)
                and cur_ctxt.contextual_depth >= new_norm_limit
                or isinstance(new_norm_limit, Fraction)
                and cur_ctxt.contextual_precision <= new_norm_limit
            ):
                res = sentinel
            else:
                # Mixing these requires dictionaries' orders to be durable across state
                # mutations. We're relying on args and kw to remain constant and
                # ordered.
                objs: Tuple[Union[H, P, PWithSelection], ...] = tuple(
                    _source_to_h_or_p_or_p_with_selection(arg)
                    for arg in chain(args, kw.values())
                )

                total = sum(obj.total for obj in objs)

                def _expand_if_we_can_can_can() -> Iterator[Tuple[HOrOutcomeT, int]]:
                    for result_counts in product(
                        *(
                            _h_or_p_or_p_with_selection_to_result_iterable(obj)
                            for obj in objs
                        )
                    ):
                        results, counts = zip(*result_counts)
                        combined_count = prod(counts)
                        token = _expandable_ctxt.set(
                            _Context(
                                normalized_limit=new_norm_limit,
                                contextual_depth=cur_ctxt.contextual_depth + 1,
                                contextual_precision=Fraction(
                                    cur_ctxt.contextual_precision.numerator
                                    * combined_count,
                                    cur_ctxt.contextual_precision.denominator * total,
                                ),
                            )
                        )

                        try:
                            # Remember how we signaled our reliance on the ordering
                            # above? Here's why. We're going to take the first part as
                            # the args, and the second part as the ordered kw values,
                            # then zip them back up with the ordered kw keys.
                            callback_args = results[: len(args)]
                            callback_kw = dict(zip(kw.keys(), results[len(args) :]))

                            # This is either our callback or our sentinel function (if
                            # we hit our limit above)
                            evaluated = callback(*callback_args, **callback_kw)
                        except RecursionError:
                            # We bottomed out the system stack when calling our
                            # callback, so return our sentinel
                            evaluated = sentinel
                        finally:
                            _expandable_ctxt.reset(token)

                        yield evaluated, combined_count

                res = aggregate_weighted(_expand_if_we_can_can_can())

            if cur_ctxt.contextual_depth == 0:
                res = res.lowest_terms()

            return res

        return _f

    assert callable(f) or f is None

    return _decorator(f) if callable(f) else _decorator


# ---- Functions -----------------------------------------------------------------------


@beartype
def aggregate_weighted(
    weighted_sources: Iterable[Tuple[HOrOutcomeT, int]],
    h_type: Type[H] = H,
) -> H:
    r"""
    Aggregates *weighted_sources* into an [``H`` object][dyce.h.H]. Each of
    *weighted_sources* is a two-tuple of either an outcome-count pair or a
    histogram-count pair. This function is used in the implementation of the
    [``expandable`` decorator][dyce.evaluation.expandable] and derivatives (like the
    [``foreach`` function][dyce.evaluation.foreach]) as well as the (deprecated)
    [``H.substitute``][dyce.h.H.substitute] and [``P.foreach``][dyce.p.P.foreach]
    methods. Unlike those, the histogram returned from this function is *not* reduced to
    its lowest terms.

    In nearly all cases, when a source contains a histogram, its total takes on the
    corresponding count’s weight. In other words, the sum of the counts of the histogram
    retains the same proportion to other outcomes as its corresponding count. This
    becomes clearer when there is no overlap between the histogram and the other
    outcomes.

    ``` python
    >>> from dyce.evaluation import aggregate_weighted
    >>> weighted_sources = ((H({1: 1}), 1), (H({1: 1, 2: 2}), 2))
    >>> h = aggregate_weighted(weighted_sources).lowest_terms() ; h
    H({1: 5, 2: 4})

    ```

    !!! note "An important exception"

        If a source is the empty histogram (``H({})``), it and its count is omitted from
        the result without scaling.

        ``` python
        >>> weighted_sources = ((H(2), 1), (H({}), 20))
        >>> aggregate_weighted(weighted_sources)
        H({1: 1, 2: 1})

        ```
    """
    aggregate_scalar = 1
    outcome_counts: List[_OutcomeCountT] = []

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

    return h_type(outcome_counts)


@experimental
@beartype
def foreach(
    callback: _DependentTermT,
    *args: _POrPWithSelectionOrSourceT,
    limit: Optional[LimitT] = None,
    sentinel: H = _DEFAULT_SENTINEL,
    **kw: _POrPWithSelectionOrSourceT,
) -> H:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Shorthand for ``#!python expandable(callback, sentinel=sentinel)(*args, limit=limit,
    **kw)``.

    Many common cases do not need the full flexibility of the
    [``expandable``][dyce.evaluation.expandable]. This wrapper that strives to be
    simpler or more readable under those circumstances (e.g., where the callback is a
    ``#!python lambda`` function).

    ``` python
    >>> from dyce.evaluation import foreach
    >>> foreach(lambda d8, d12: d8.outcome + d12.outcome, d8=H(8), d12=H(12))
    H({2: 1,
     3: 2,
     4: 3,
     5: 4,
     6: 5,
     7: 6,
     8: 7,
     9: 8,
     10: 8,
     11: 8,
     12: 8,
     13: 8,
     14: 7,
     15: 6,
     16: 5,
     17: 4,
     18: 3,
     19: 2,
     20: 1})

    ```
    """
    return expandable(callback, sentinel=sentinel)(*args, limit=limit, **kw)


@experimental
@beartype
def explode(
    source: _SourceT,
    predicate: _PredicateT = lambda result: result.outcome == max(result.h),
    limit: Optional[LimitT] = None,
    inf=float("inf"),
) -> H:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Approximates an “exploding” die (i.e., one where a running total is accumulated
    and re-rolls are allowed so long as *predicate* returns ``#!python True``).
    *predicate* takes two arguments: *outcome* is the outcome being considered and *h*
    is the histogram from which it originated. The default *predicate* returns
    ``#!python True`` if its *outcome* is ``#!python max(h)``, and ``#!python False``
    otherwise. *limit* shares the same semantics as with the
    [``expandable`` decorator][dyce.evaluation.expandable].

    ``` python
    >>> from dyce.evaluation import HResult, explode
    >>> explode(H(6), limit=2)
    H({1: 36,
     2: 36,
     3: 36,
     4: 36,
     5: 36,
     7: 6,
     8: 6,
     9: 6,
     10: 6,
     11: 6,
     13: 1,
     14: 1,
     15: 1,
     16: 1,
     17: 1,
     18: 1})

    >>> from fractions import Fraction
    >>> # approximates d20 that explodes when rolling any even number (to a precision of 0.0001 or better)

    >>> def is_even_predicate(h_result: HResult):
    ...   return h_result.outcome % 2 == 0

    >>> explode(H(20), is_even_predicate, limit=Fraction(1, 10_000))
    H({1: 160000,
     3: 168000,
     5: 176400,
     7: 185220,
     9: 194481,
     10: 1,
     11: 204205,
     12: 5,
     13: 214415,
     14: 15,
     15: 225135,
     ...,
     95: 15,
     96: 15,
     97: 5,
     98: 5,
     99: 1,
     100: 1})

    ```

    Where *h* has a single outcome that satisfies *predicate* and *limit* is a
    fractional value, this function returns special histograms, possibly leveraging the
    *inf* parameter. The default for *inf* is ``#!python float("inf")``.

    ``` python
    >>> explode(H({3: 1}), is_even_predicate, limit=Fraction(1, 10_000))  # returns h
    H({3: 1})
    >>> explode(H({2: 1}), is_even_predicate, limit=Fraction(1, 10_000))  # extrapolated to positive infinity
    H({inf: 1})
    >>> explode(H({0: 1}), is_even_predicate, limit=Fraction(1, 10_000))  # returns h
    H({0: 1})
    >>> explode(H({-2: 1}), is_even_predicate, limit=Fraction(1, 10_000))  # extrapolated to negative infinity
    H({-inf: 1})
    >>> explode(H({-2: 1}), is_even_predicate, limit=Fraction(1, 10_000), inf=1_000_000)
    H({-2000000: 1})

    ```

    ``` python
    >>> import sympy
    >>> x = sympy.sympify("x")
    >>> explode(H({x: 1}), limit=Fraction(1, 10_000))
    H({oo*x: 1})

    ```
    """
    h = source if isinstance(source, H) else H(source)

    @expandable(sentinel=h)
    def _explode(h_result: HResult) -> HOrOutcomeT:
        if predicate(h_result):
            if len(h_result.h) == 1 and not isinstance(
                limit, (type(None), IntegralLike)
            ):
                if h_result.outcome == h_result.outcome - h_result.outcome:
                    return H({h_result.outcome: 1})
                else:
                    return H({inf * h_result.outcome: 1})
            else:
                return _explode(h_result.h) + h_result.outcome
        else:
            return h_result.outcome

    return _explode(h, limit=limit)


@beartype
def _h_or_p_or_p_with_selection_to_result_iterable(
    source: Union[H, P, PWithSelection]
) -> Union[Iterable[_HResultCountT], Iterable[_PResultCountT]]:
    if isinstance(source, H):
        return (
            (HResult(h=source, outcome=outcome), count)
            for outcome, count in source.items()
        )
    elif isinstance(source, P):
        return (
            (PResult(p=source, roll=roll), count)
            for roll, count in source.rolls_with_counts()
        )
    elif isinstance(source, PWithSelection):
        return (
            (PResult(p=source.p, roll=roll), count)
            for roll, count in source.p.rolls_with_counts(*source.which)
        )
    else:
        raise TypeError(f"unrecognized source type {source}")


@beartype
def _normalize_limit(
    limit: LimitT,
) -> _NormalizedLimitT:
    normalized_limit: _NormalizedLimitT

    if isinstance(limit, IntegralLike):
        normalized_limit = as_int(limit)
    elif isinstance(limit, RationalLikeMixedT):
        normalized_limit = Fraction(numerator(limit), denominator(limit))
    elif isinstance(limit, RealLike):
        normalized_limit = Fraction(float(limit))
    else:
        raise TypeError(f"unrecognized limit type {limit}")

    if isinstance(normalized_limit, int):
        if normalized_limit == -1:
            normalized_limit = sys.maxsize
        elif normalized_limit < 0:
            raise ValueError(
                "limit cannot be an arbitrary negative integral (use -1 explicitly to indicate no limit)"
            )
    elif isinstance(normalized_limit, Fraction):
        if normalized_limit <= 0 or normalized_limit >= 1:
            raise ValueError("fractional limit must be between zero and one, exclusive")

    return normalized_limit


@beartype
def _source_to_h_or_p_or_p_with_selection(
    source: _POrPWithSelectionOrSourceT,
) -> Union[H, P, PWithSelection]:
    if isinstance(source, (H, P, PWithSelection)):
        return source
    elif isinstance(source, HableT):
        return source.h()
    else:
        return H(source)

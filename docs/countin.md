<!---
  Copyright and other protections apply.
  Please see the accompanying LICENSE file for rights and restrictions governing use of this software.
  All rights not expressly waived or licensed are reserved.
  If that file is missing or appears to be modified from its original, then please contact the author before viewing or using this software in any capacity.

  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!
-->
<!-- BEGIN MONKEY PATCH --
For typing.

    >>> import sympy  # type: ignore[import-untyped]
    >>> import sympy.abc  # type: ignore[import-untyped]
    >>> import sympy.solvers  # type: ignore[import-untyped]
    >>> import sympy.solvers.inequalities  # type: ignore[import-untyped]

  -- END MONKEY PATCH -->

`dyce` provides two core primitives for enumeration.

<!-- TODO(posita): Figure out what we're doing with dyce.r -->
<!--
[^1].

[^1]:

    `dyce` also provides additional primitives ([`R` objects][dyce.r.R] and their kin) which are useful for producing weighted randomized rolls without the overhead of enumeration.
    These are covered [separately](rollin.md).
-->

[`H` objects][dyce.H] represent histograms for modeling discrete outcomes.
They encode finite discrete probability distributions as integer counts without any denominator.
[`P` objects][dyce.P] represent pools (ordered sequences) of histograms.
If all you need is to aggregate outcomes (sums) from rolling a bunch of dice (or perform calculations on aggregate outcomes), [`H` objects][dyce.H] are probably sufficient.
If you need to *select* certain histograms from a group prior to computing aggregate outcomes (e.g., taking the highest and lowest of each possible roll of *n* dice), that’s where [`P` objects][dyce.P] come in.

As a wise person whose name has been lost to history once said: “Language is imperfect. If at all possible, shut up and point.”
So with that illuminating (or perhaps impenetrable) introduction out of the way, let’s dive into some examples!

## Basic examples

`#!python H(n)` is shorthand for explicitly enumerating outcomes `#!math [{ {1} .. {n} }]`, each with a frequency of 1.
A normal, six-sided die (d6) can be modeled as:

    >>> from dyce import H
    >>> H(6)
    H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

Tuples with repeating outcomes are accumulated.
A six-sided “2, 3, 3, 4, 4, 5” die can be modeled as:

    >>> H((2, 3, 3, 4, 4, 5))
    H({2: 1, 3: 2, 4: 2, 5: 1})

A fudge die can be modeled as:

    >>> H((-1, 0, 1))
    H({-1: 1, 0: 1, 1: 1})

Python’s matrix multiplication operator (`@`) is used to express the number of a particular die (roughly equivalent to the “`d`” operator in common notations).
The outcomes of rolling and summing two six-sided dice (2d6) are:

    >>> 2 @ H(6)
    H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})

[`dyce.d`][dyce.d] has some convenient abbreviations for commonly found dice:

    >>> from dyce.d import d6, h2d6
    >>> d6 == H(6)
    True
    >>> h2d6 == 2 @ d6
    True

A pool of two six-sided dice is:

    >>> from dyce import P
    >>> P(d6, d6)
    2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))

Where `#!python n` is an integer, `#!python P(n, ...)` is shorthand for `#!python P(H(n), ...)`.
Python’s matrix multiplication operator (`#!python @`) can also be used with pools.
The above can be expressed more succinctly.

    >>> from dyce.d import p2d6
    >>> 2 @ P(6) == P(d6, d6) == p2d6
    True

Pools (in this case, [Sicherman dice](https://en.wikipedia.org/wiki/Sicherman_dice)) can be compared to histograms.

    >>> d_sicherman = P(H((1, 2, 2, 3, 3, 4)), H((1, 3, 4, 5, 6, 8)))
    >>> d_sicherman == h2d6
    True

Both histograms and pools support arithmetic operations.
`3×(2d6+4)` is:

    >>> 3 * (2 @ H(6) + 4)
    H({18: 1, 21: 2, 24: 3, 27: 4, 30: 5, 33: 6, 36: 5, 39: 4, 42: 3, 45: 2, 48: 1})

The results show there is one way to make `#!python 18`, two ways to make `#!python 21`, three ways to make `#!python 24`, etc.

Histograms provide rudimentary formatting for convenience.

    >>> print(h2d6.format(width=65))
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

The [Miwin-Distribution](https://en.wikipedia.org/wiki/Intransitive_dice#Miwin's_dice) is:

    >>> miwin_iii = H((1, 2, 5, 6, 7, 9))
    >>> from typing import reveal_type
    >>> miwin_iv = H((1, 3, 4, 5, 8, 9))
    >>> from typing import reveal_type
    >>> miwin_v = H((2, 3, 4, 6, 7, 8))
    >>> from typing import reveal_type
    >>> miwin_dist = miwin_iii + miwin_iv + miwin_v
    >>> miwin_dist
    H({4: 1, 5: 2, 6: 3, 7: 4, 8: 7, ..., 22: 7, 23: 4, 24: 3, 25: 2, 26: 1})
    >>> print((miwin_dist).format(width=65, scaled=True))
    avg |   15.00
    std |    4.47
    var |   20.00
      4 |   0.46% |##
      5 |   0.93% |#####
      6 |   1.39% |#######
      7 |   1.85% |##########
      8 |   3.24% |##################
      9 |   4.17% |#######################
     10 |   4.63% |##########################
     11 |   5.09% |############################
     12 |   7.87% |############################################
     13 |   8.80% |#################################################
     14 |   8.33% |###############################################
     15 |   6.48% |####################################
     16 |   8.33% |###############################################
     17 |   8.80% |#################################################
     18 |   7.87% |############################################
     19 |   5.09% |############################
     20 |   4.63% |##########################
     21 |   4.17% |#######################
     22 |   3.24% |##################
     23 |   1.85% |##########
     24 |   1.39% |#######
     25 |   0.93% |#####
     26 |   0.46% |##

One way to model the outcomes of subtracting the lesser of two six-sided dice from the greater is:

    >>> abs(H(6) - H(6))
    H({0: 6, 1: 10, 2: 8, 3: 6, 4: 4, 5: 2})

Arithmetic operations implicitly “flatten” pools into histograms.

    >>> 3 * (2 @ P(6) + 4)
    H({18: 1, 21: 2, 24: 3, 27: 4, 30: 5, 33: 6, 36: 5, 39: 4, 42: 3, 45: 2, 48: 1})
    >>> abs(P(6) - P(6))
    H({0: 6, 1: 10, 2: 8, 3: 6, 4: 4, 5: 2})

Histograms should be sufficient for most calculations.
However, pools are useful for “keeping” or “taking” (selecting) only some of each roll’s outcomes.
This is done by providing one or more index arguments to the [`P.h` method][dyce.P.h] or the [`P.rolls_with_counts` method][dyce.P.rolls_with_counts].
Indexes can be integers, slices, or a mix thereof.
Outcome indexes in rolls are ordered from least to greatest with negative values counting from the right, as one would expect (i.e., `#!python [0]`, `#!python [1]`, …, `#!python [-2]`, `#!python [-1]`).
Summing the least two faces when rolling three six-sided dice would be:

    >>> 3 @ P(6)
    3@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))
    >>> (3 @ P(6)).h(0, 1)  # see warning below about parentheses
    H({2: 16, 3: 27, 4: 34, 5: 36, 6: 34, 7: 27, 8: 19, 9: 12, 10: 7, 11: 3, 12: 1})

!!! bug "Mind your parentheses"

    Parentheses are needed in the above example because `#!python @` has a [lower precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence) than `#!python .` and `#!python […]`.

            >>> 2 @ P(6).h(1)  # equivalent to 2@(P(6).h(1))
            Traceback (most recent call last):
            ...
            IndexError: tuple index out of range
            >>> (2 @ P(6)).h(1)
            H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})

Taking the least, middle, or greatest face when rolling three six-sided dice would be:

    >>> p3d6 = 3 @ P(6)
    >>> p3d6.h(0)  # least
    H({1: 91, 2: 61, 3: 37, 4: 19, 5: 7, 6: 1})
    >>> print(p3d6.h(0).format(width=65))
    avg |    2.04
    std |    1.14
    var |    1.31
      1 |  42.13% |#####################
      2 |  28.24% |##############
      3 |  17.13% |########
      4 |   8.80% |####
      5 |   3.24% |#
      6 |   0.46% |

<!-- -->

    >>> p3d6.h(1)  # middle
    H({1: 16, 2: 40, 3: 52, 4: 52, 5: 40, 6: 16})
    >>> print(p3d6.h(1).format(width=65))
    avg |    3.50
    std |    1.37
    var |    1.88
      1 |   7.41% |###
      2 |  18.52% |#########
      3 |  24.07% |############
      4 |  24.07% |############
      5 |  18.52% |#########
      6 |   7.41% |###

<!-- -->

    >>> p3d6.h(2)  # greatest (p3d6.h(-1) would also work)
    H({1: 1, 2: 7, 3: 19, 4: 37, 5: 61, 6: 91})
    >>> print(p3d6.h(-1).format(width=65))
    avg |    4.96
    std |    1.14
    var |    1.31
      1 |   0.46% |
      2 |   3.24% |#
      3 |   8.80% |####
      4 |  17.13% |########
      5 |  28.24% |##############
      6 |  42.13% |#####################

Summing the greatest and the least faces when rolling a typical six-die polygonal set would be:

    >>> d10 = H(10) - 1
    >>> d10  # a common “d10” with faces [0 .. 9]
    H({0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1})
    >>> h = P(4, 6, 8, d10, 12, 20).h(0, -1)
    >>> print(h.format(width=65, scaled=True))
    avg |   13.48
    std |    4.40
    var |   19.39
      1 |   0.00% |
      2 |   0.01% |
      3 |   0.06% |
      4 |   0.30% |#
      5 |   0.92% |#####
      6 |   2.03% |###########
      7 |   3.76% |####################
      8 |   5.57% |##############################
      9 |   7.78% |###########################################
     10 |   8.99% |##################################################
     11 |   8.47% |###############################################
     12 |   8.64% |################################################
     13 |   8.66% |################################################
     14 |   6.64% |####################################
     15 |   5.62% |###############################
     16 |   5.16% |############################
     17 |   5.00% |###########################
     18 |   5.00% |###########################
     19 |   5.00% |###########################
     20 |   5.00% |###########################
     21 |   4.50% |#########################
     22 |   2.01% |###########
     23 |   0.73% |####
     24 |   0.18% |

Pools are ordered and iterable.

    >>> list(2 @ P(8, 4, 6))
    [H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1})]


Slicing creates a new pool with the selected histograms.

    >>> 2 @ P(4, 6, 8)
    P(2@P(H({1: 1, 2: 1, 3: 1, 4: 1})), 2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})), 2@P(H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1})))
    >>> (2 @ P(4, 6, 8))[:2]
    2@P(H({1: 1, 2: 1, 3: 1, 4: 1}))
    >>> P(4, 6, 8, 10)[::3]
    P(H({1: 1, 2: 1, 3: 1, 4: 1}), H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1}))


An inefficient way to enumerate all possible rolls is:

    >>> import itertools
    >>> list(itertools.product(*P(-3, 3)))
    [(-3, 1), (-3, 2), (-3, 3), (-2, 1), (-2, 2), (-2, 3), (-1, 1), (-1, 2), (-1, 3)]


Both histograms and pools support various comparison operations.
The odds of observing all even faces when rolling `#!math n` six-sided dice, for `#!math n` in `#!math [1 .. 6]` is:

    >>> d6_even = H(6).apply(lambda outcome: outcome % 2 == 0)
    >>> d6_even  # basically a fair coin whose sides are False and True
    H({False: 3, True: 3})
    >>> for n in range(6, 0, -1):
    ...     number_of_evens_in_nd6 = n @ d6_even
    ...     all_even = number_of_evens_in_nd6.eq(n)
    ...     print(f"{n: >2}d6: {all_even[1] / all_even.total: >6.2%}")
     6d6:  1.56%
     5d6:  3.12%
     4d6:  6.25%
     3d6: 12.50%
     2d6: 25.00%
     1d6: 50.00%


The odds of scoring at least one nine or higher for any one of `#!math n` “[exploding][dyce.explode_n]” six-sided dice, for `#!math n` in `#!math [1 .. 10]` is:

<!-- BEGIN MONKEY PATCH --
>>> import warnings
>>> from dyce.lifecycle import ExperimentalWarning
>>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

   -- END MONKEY PATCH -->

    >>> from dyce import explode_n
    >>> # By the time we're exploding to a third die, we're guaranteed
    >>> # a nine or higher, so we don't need to explode past that
    >>> # TODO(posita): <https://github.com/facebook/pyrefly/issues/3236>
    >>> exploding_d6 = explode_n(H(6), n=2)  # pyrefly: ignore[no-matching-overload]
    >>> for n in range(10, 0, -1):
    ...     d6e_ge_9 = exploding_d6.ge(9)
    ...     number_of_nines_or_higher_in_nd6e = n @ d6e_ge_9
    ...     at_least_one_9 = number_of_nines_or_higher_in_nd6e.ge(1)
    ...     print(f"{n: >2}d6-exploding: {at_least_one_9[1] / at_least_one_9.total: >6.2%}")
    10d6-exploding: 69.21%
     9d6-exploding: 65.36%
     8d6-exploding: 61.03%
     7d6-exploding: 56.15%
     6d6-exploding: 50.67%
     5d6-exploding: 44.51%
     4d6-exploding: 37.57%
     3d6-exploding: 29.77%
     2d6-exploding: 20.99%
     1d6-exploding: 11.11%


<!-- BEGIN MONKEY PATCH --
>>> warnings.resetwarnings()

   -- END MONKEY PATCH -->

## Dependent probabilities

<!-- BEGIN MONKEY PATCH --
>>> import warnings
>>> from dyce.lifecycle import ExperimentalWarning
>>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

   -- END MONKEY PATCH -->

Probabilities involving dependent terms can be expressed via a callback passed to [`expand`][dyce.expand].
First, we express independent terms as histograms or pools.
Second, we express the dependent term as a function that will be called once for each of the Cartesian product of the results from each independent term.
Outcomes from independent histogram terms are passed to the dependent function as [`HResult` objects][dyce.HResult].
Rolls from independent pool terms are passed as [`PResult` objects][dyce.PResult].
Finally, we pass the dependent function to [`expand`][dyce.expand], along with the independent terms.

To illustrate, say we want to roll a six-sided die and compare whether the result is strictly greater than its distance from some constant.

    >>> from dyce.evaluation import HResult, expand

    >>> d6 = H(6)  # independent term
    >>> constant = 4

    >>> def outcome_strictly_greater_than_constant(h_result: HResult[int]) -> bool:
    ...     return h_result.outcome > abs(h_result.outcome - constant)  # dependent term

    >>> print(expand(outcome_strictly_greater_than_constant, d6).format(width=65))
      avg |    0.67
      std |    0.47
      var |    0.22
    False |  33.33% |################
     True |  66.67% |################################


Instead of a constant, let’s use another die as a second independent term.
We’ll roll a four-sided die (d4) and a six-sided die and compare whether the six-sided roll is strictly greater than the absolute difference between the dice.


    >>> d4 = H(4)  # first independent term
    >>> d6 = H(6)  # second independent term

    >>> def second_is_strictly_greater_than_first(
    ...     first: HResult[int], second: HResult[int]
    ... ) -> bool:
    ...     return second.outcome > abs(first.outcome - second.outcome)  # dependent term

    >>> second_gt_first_h = expand(second_is_strictly_greater_than_first, d4, d6)
    >>> print(second_gt_first_h.format(width=65))
      avg |    0.83
      std |    0.37
      var |    0.14
    False |  16.67% |########
     True |  83.33% |########################################


In the alternative, one could nest the [`expand`][dyce.expand] call, where the innermost holds the dependent term, and the outer functions each establish the scope of their respective independent outcomes.
However, this isn’t very readable, and is often less efficient than using a single function.

    >>> def sub_first(first: HResult[int], *, second_h: H[int]) -> H[bool]:
    ...
    ...     def sub_second(second: HResult[int]) -> bool:
    ...         res = second.outcome > abs(first.outcome - second.outcome)
    ...         return res
    ...
    ...     return expand(sub_second, second_h)

    >>> expand(sub_first, d4, second_h=d6) == second_gt_first_h
    True


This technique also works where the dependent term requires inspection of *rolls* from one or more pools as independent terms.
Let’s say we have two pools.
A roll from the first pool wins if it shows no duplicates but a roll from the second does.
A roll from the second pool wins if it shows no duplicates but a roll from the first does.
Otherwise, it’s a tie (i.e., if neither or both rolls show duplicates).
Let’s compare how three six-sided dice fair against two four-sided dice.

    >>> from dyce.evaluation import PResult
    >>> from enum import IntEnum

    >>> class DupeVs(IntEnum):
    ...     SECOND_WINS = -1  # where second.roll shows no duplicates, but first.roll does
    ...     DRAW = 0  # where both rolls show no duplicates or rolls pools have duplicates
    ...     FIRST_WINS = 1  # where first.roll shows no duplicates, but second.roll does

    >>> def compare_duplicates(first: PResult[int], second: PResult[int]) -> DupeVs:
    ...     return DupeVs(
    ...         (len(set(first.roll)) == len(first.roll))
    ...         - (len(set(second.roll)) == len(second.roll))
    ...     )

    >>> dupe_vs_h = expand(compare_duplicates, P(6, 6, 6), P(4, 4))
    >>> dupe_vs_h
    H({<DupeVs.SECOND_WINS: -1>: 12, <DupeVs.DRAW: 0>: 19, <DupeVs.FIRST_WINS: 1>: 5})
    >>> print(dupe_vs_h.format(width=65))
                         avg |   -0.19
                         std |    0.66
                         var |    0.43
    <DupeVs.SECOND_WINS: -1> |  33.33% |#########
            <DupeVs.DRAW: 0> |  52.78% |###############
      <DupeVs.FIRST_WINS: 1> |  13.89% |####


<!-- BEGIN MONKEY PATCH --
>>> warnings.resetwarnings()

   -- END MONKEY PATCH -->

### Expansion and recursion

<!-- BEGIN MONKEY PATCH --
>>> import warnings
>>> from dyce import TruncationWarning
>>> from dyce.lifecycle import ExperimentalWarning
>>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
>>> warnings.filterwarnings("ignore", category=TruncationWarning)

   -- END MONKEY PATCH -->

Explosion is a great way to illustrate use of the [`expand` interface][dyce.expand].
One way to approximate an exploding die is to recursively re-roll and add to a running total whenever the outcome is the die’s highest.
This framing is intuitive because it maps to well to reality.
We might start with the following implementation:

    >>> from dyce import HResult, expand

    >>> def naive_explode(result: HResult[int]) -> H[int] | int:
    ...     if result.outcome == max(result.h):
    ...         # If we've rolled the max for this die, add another die roll
    ...         # to our existing outcome
    ...         return result.outcome + expand(naive_explode, result.h)
    ...     return result.outcome

    >>> d6 = H(6)
    >>> h = expand(naive_explode, d6)
    >>> print(h.format(width=65, scaled=True))
    avg |    4.20
    std |    3.26
    var |   10.64
      1 |  16.67% |#################################################
      2 |  16.67% |#################################################
      3 |  16.67% |#################################################
      4 |  16.67% |#################################################
      5 |  16.67% |#################################################
      7 |   2.78% |########
      8 |   2.78% |########
      9 |   2.78% |########
     10 |   2.78% |########
     11 |   2.78% |########
     13 |   0.46% |#
     14 |   0.46% |#
     15 |   0.46% |#
     16 |   0.46% |#
     17 |   0.46% |#
     19 |   0.08% |
     ...
     23 |   0.08% |
     25 |   0.01% |
     ...
     29 |   0.01% |
     31 |   0.00% |
     ...
     47 |   0.00% |
    >>> h
    H({1: 233280, ..., 5: 233280, ..., 43: 1, ..., 47: 1})


```linenums="0"
TruncationWarning: expand: some branches with path probability < Fraction(1, 8388607) were truncated
```

What just happened?
It appears that we went no further than eight rolls (a first roll plus up to seven explosions).
Folks familiar with this domain might recognize the distribution looks *mostly* correct, but the counts are a bit…*off*.
We’re also missing the final outcome of `#!python 48`.
We also got a [`TruncationWarning`][dyce.TruncationWarning], which provides a hint.

The way to eliminate a branch from consideration when recursing with [`expand`][dyce.expand] is to explicitly return the empty histogram `#!python H({})` from our function.
(See the `#!always_reroll_on_one` example from [`expand`’s docstring][dyce.expand].)
We’re not explicitly returning `#!python H({})` in our function, but there are two scenarios where that is done automatically.
The first is when we’ve exhausted our precision budget (which is what happened in our example above).
And the second is when we’ve exhausted the call stack:

    >>> import sys
    >>> from fractions import Fraction
    >>> fair_coin = H({0: 1, 1: 1})
    >>> expand(
    ...     naive_explode,
    ...     fair_coin,
    ...     precision=Fraction(0),
    ... )  # these numbers get *big*
    H({0: ...})


```linenums="0"
TruncationWarning: expand: some branches whose recursion depth exceeded 1000 were truncated
```

When either of those things happen, [`expand`][dyce.expand] returns `#!python H({})`.
Let’s take a closer look at our implementation now that we know that might happen:

```python linenums="7"
       return result.outcome + expand(naive_explode, result.h)
```

For the above line, if [`expand`][dyce.expand] returns `#!python H({})`, our function will also return `#!python H({})` for that branch.
This is because adding `#!python H({})` to anything is `#!python H({})`:

    >>> H({}) + 1024
    H({})


This explains why `#!python 48` is missing from our results above.
A more illustrative case is trying to “explode” a one-sided die (d1), where no branch is “settled” before exhaustion occurs:

    >>> expand(naive_explode, H(1))
    H({})


How do we fix this?
Great question!
Thanks for asking!

It’s easy.
We can check.

    >>> def guarded_explode(result: HResult[int]) -> H[int] | int:
    ...     if result.outcome == max(result.h):
    ...         inner = expand(guarded_explode, result.h)
    ...         if inner:
    ...             # Only return another histogram if we weren't truncated
    ...             # somewhere down the line
    ...             return result.outcome + inner
    ...     # Every other case returns our current outcome
    ...     return result.outcome

    >>> expand(guarded_explode, d6)
    H({..., 19: 1296, ..., 23: 1296, 25: 216, ..., 29: 216, 31: 36, ..., 35: 36, 37: 6, ..., 41: 6, 43: 1, ..., 48: 1})


*Much* better.
We can now recognize the counts as powers of our maximum face.

But how can we control the number of explosions?
Sure, we *could* do some math and fiddle with [`expand`][dyce.expand]’s `#!python precision` parameter.

    >>> num_faces = 6
    >>> explosions = 3
    >>> expand(
    ...     guarded_explode,
    ...     H(num_faces),
    ...     precision=Fraction(1, num_faces ** (explosions + 1)),
    ... )
    H({1: 216, 2: 216, 3: 216, ..., 22: 1, 23: 1, 24: 1})


But that’s fragile and highly domain-specific.
Instead, we can take advantage of [`expand`][dyce.expand]’s ability to pass down arbitrary keyword arguments to make our depth counting explicit.

    >>> def guarded_explode_n(result: HResult[int], n: int = 0) -> H[int] | int:
    ...     if n > 0 and result.outcome == max(result.h):
    ...         inner = expand(guarded_explode_n, result.h, n=n - 1)
    ...         if inner:
    ...             return result.outcome + inner
    ...     # Every other case returns our current outcome
    ...     return result.outcome

    >>> expand(guarded_explode_n, d6, n=3)
    H({1: 216, 2: 216, 3: 216, ..., 22: 1, 23: 1, 24: 1})
    >>> expand(guarded_explode_n, d6, n=0) == d6
    True


Our function is still implicitly limited by the `#!python precision` parameter, but we can make that go away by setting it to `#!python Fraction(0)` as we did in our recursion exhaustion illustration above.
If we wanted to make that the default, we could create a simple wrapper.

    >>> from collections.abc import Callable
    >>> from typing import TypeVar
    >>> T = TypeVar("T")

    >>> def proper_explode_n(
    ...     source: H[T],
    ...     *,
    ...     n: int = 0,
    ...     precision: Fraction = Fraction(0),
    ... ) -> H[T]:
    ...
    ...     def _callback(result: HResult[T], *, n_left: int) -> H[T] | T:
    ...         if n_left > 0 and result.outcome == max(result.h):  # type: ignore[type-var]
    ...             inner = expand(_callback, result.h, n_left=n_left - 1)
    ...             if inner:
    ...                 return result.outcome + inner
    ...         return result.outcome
    ...
    ...     return expand(_callback, source, n_left=n, precision=precision)

    >>> proper_explode_n(d6, n=3)
    H({1: 216, 2: 216, 3: 216, ..., 22: 1, 23: 1, 24: 1})
    >>> proper_explode_n(d6, n=0) == d6
    True


The above is very nearly the implementation for [`explode_n`][dyce.explode_n], which offers an additional `#!python resolver` parameter that allows for some additional flexibility.

Let’s say we’re considering a new exploding mechanic where, to explode, one must roll the highest outcome on a given die.
However, on the second explosion, re-explosion occurs if either the highest or second highest outcome is rolled.
On the third explosion, anything greater than or equal to the third highest outcome will re-explode, etc.
In order to have somewhere to stop, we’ll never allow explosions if the minimum outcome is rolled.

    >>> from dyce import explode_n

    >>> def explosions_get_easier_resolver(
    ...     result: HResult[T], n_left: int, n_done: int
    ... ) -> H[T] | T:
    ...     return (
    ...         result.h
    ...         # Explode only maximum value if we haven't exploded yet,
    ...         # on [max - 1..max] if we've already exploded once, on
    ...         # [max - 2..max] if we've already exploded twice, etc.
    ...         # ...
    ...         if (
    ...             result.outcome >= max(result.h) - n_done  # type: ignore[operator,type-var]
    ...             and
    ...             # ... but never explode on the minimum
    ...             result.outcome > min(result.h)  # type: ignore[operator,type-var]
    ...         )
    ...         else result.outcome
    ...     )

    >>> d10 = H(10)
    >>> h = explode_n(
    ...     d10,
    ...     n=3,
    ...     resolver=explosions_get_easier_resolver,
    ... )
    >>> print(h.format(width=65, scaled=True))
    avg |    6.19
    std |    4.71
    var |   22.17
      1 |  10.00% |##################################################
      2 |  10.00% |##################################################
      3 |  10.00% |##################################################
      4 |  10.00% |##################################################
      5 |  10.00% |##################################################
      6 |  10.00% |##################################################
      7 |  10.00% |##################################################
      8 |  10.00% |##################################################
      9 |  10.00% |##################################################
     11 |   1.00% |#####
     12 |   1.00% |#####
     13 |   1.00% |#####
     14 |   1.00% |#####
     15 |   1.00% |#####
     16 |   1.00% |#####
     17 |   1.00% |#####
     18 |   1.00% |#####
     20 |   0.10% |
     21 |   0.20% |#
     22 |   0.20% |#
     23 |   0.20% |#
     24 |   0.20% |#
     25 |   0.20% |#
     26 |   0.20% |#
     27 |   0.10% |
     28 |   0.01% |
     29 |   0.03% |
     30 |   0.05% |
     31 |   0.06% |
     32 |   0.06% |
     33 |   0.06% |
     34 |   0.06% |
     35 |   0.06% |
     36 |   0.06% |
     37 |   0.06% |
     38 |   0.05% |
     39 |   0.03% |
     40 |   0.01% |


Now let’s consider a “diminishing returns” explosion mechanic, where standard polygonal dice “degrade” into their next smallest die for the next explosion.

    >>> from dyce import explode_n
    >>> from functools import partial

    >>> def diminishing_returns_resolver(
    ...     result: HResult[T],
    ...     n_left: int,
    ...     n_done: int,
    ...     *,
    ...     pool: P[T],
    ... ) -> H[T] | T:
    ...     if result.h in pool:
    ...         which = pool.index(result.h)
    ...         if which > 0 and result.outcome == max(result.h):  # type: ignore[type-var]
    ...             return pool[which - 1]
    ...     return result.outcome

    >>> standard_set = P(4, 6, 8, 10, 12, 20)
    >>> for d in standard_set:
    ...     explode_n(
    ...         d,
    ...         n=sys.maxsize,
    ...         resolver=partial(
    ...             diminishing_returns_resolver,
    ...             pool=standard_set,
    ...         ),
    ...     )
    H({1: 1, 2: 1, 3: 1, 4: 1})
    H({1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 7: 1, 8: 1, 9: 1, 10: 1})
    H({1: 24, ..., 7: 24, 9: 4, ...: 4, 15: 1, ..., 18: 1})
    H({1: 192, ..., 9: 192, 11: 24, ..., 17: 24, 19: 4, ..., 23: 4, 25: 1, ..., 28: 1})
    H({1: 1920, ..., 11: 1920, 13: 192, ..., 21: 192, 23: 24, ..., 29: 24, 31: 4, ..., 34: 4, 35: 4, 37: 1, ..., 40: 1})
    H({1: 23040, ..., 19: 23040, 21: 1920, ..., 31: 1920, 33: 192, ..., 41: 192, 43: 24, ..., 49: 24, 51: 4, ..., 55: 4, 57: 1, ..., 60: 1})


<!-- BEGIN MONKEY PATCH --
>>> warnings.resetwarnings()

   -- END MONKEY PATCH -->

## Visualization

[`H.probability_items`][dyce.H.probability_items] eases integration with plotting packages.
If [Matplotlib](https://matplotlib.org/stable/api/index.html) is installed [`dyce.viz`][dyce.viz] provides plotting conveniences.
For something more sophisticated, [`anydyce`](https://github.com/posita/anydyce/) provides additional interactive visualization tools.

Visualization using [`dyce.viz`][dyce.viz] with [Matplotlib](https://matplotlib.org/stable/api/index.html): <a href="../jupyter/lab/?path=histogram.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_histogram.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_histogram_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_histogram_light.svg">
  <img alt="Plot: Distribution for 3d6" src="../assets/plot_histogram_light.svg">
</picture>

## Time to get meta-evil on those outcomes!

Thanks to ~~[`numerary`](https://pypi.org/project/numerary/)~~ *[`optype`](https://jorenham.github.io/optype/)*, `dyce` offers typing support for arbitrary number-like outcomes, including primitives from symbolic expression packages such as [SymPy](https://www.sympy.org/).

    >>> import sympy.abc
    >>> d6x = H(6) + sympy.abc.x
    >>> d8y = H(8) + sympy.abc.y
    >>> P(d6x, d8y, d6x).h()
    H({2*x + y + 3: 1, 2*x + y + 4: 3, 2*x + y + 5: 6, ..., 2*x + y + 18: 6, 2*x + y + 19: 3, 2*x + y + 20: 1})


[![Miss you, Doris!](assets/doris.png)](https://me.me/i/shnomf-nomf-hormf-hom-ive-gots-to-get-my-rib-22441186)

!!! note

    Be aware that, depending on implementation, performance can suffer quite a bit when using symbolic primitives.

For histograms and pools, `dyce` remains opinionated about ordering.
For non-critical contexts where relative values are indeterminate, `dyce` will attempt a “natural” ordering based on the string representation of each outcome.
This is to accommodate symbolic expressions whose relative values are often unknowable.

    >>> expr = sympy.abc.x < sympy.abc.x * 3
    >>> expr
    x < 3*x
    >>> bool(expr)  # nope
    Traceback (most recent call last):
      ...
    TypeError: cannot determine truth value of Relational...


SymPy does not even attempt simple relative comparisons between symbolic expressions, even where they are unambiguously resolvable.
Instead, it relies on the caller to invoke its proprietary solver APIs.

    >>> bool(sympy.abc.x < sympy.abc.x + 1)
    Traceback (most recent call last):
      ...
    TypeError: cannot determine truth value of Relational...
    >>> import sympy.solvers.inequalities
    >>> sympy.solvers.inequalities.reduce_inequalities(
    ...     sympy.abc.x < sympy.abc.x + 1, [sympy.abc.x]
    ... )
    True


`dyce`, of course, is happily ignorant of all that keenness.
(As it should be.)
In practice, that means that certain operations won’t work with symbolic expressions where correctness depends on ordering outcomes according to relative value (e.g., dice selection from pools).

Flattening pools works.

    >>> d3x = H(3) * sympy.abc.x
    >>> d3x
    H({2*x: 1, 3*x: 1, x: 1})
    >>> p = P(d3x / 3, (d3x + 1) / 3, (d3x + 2) / 3)
    >>> p.h()
    H({2*x + 1: 7, 3*x + 1: 1, 4*x/3 + 1: 3, 5*x/3 + 1: 6, 7*x/3 + 1: 6, 8*x/3 + 1: 3, x + 1: 1})


Selecting the “lowest” die works

    >>> p.h(0)
    H({2*x/3: 9, 2*x/3 + 1/3: 6, 2*x/3 + 2/3: 4, x: 4, x + 1/3: 2, x + 2/3: 1, x/3: 1})


Selecting all dice works, since it’s equivalent to flattening (no sorting is required).

    >>> p.h(slice(None))
    H({2*x + 1: 7, 3*x + 1: 1, 4*x/3 + 1: 3, 5*x/3 + 1: 6, 7*x/3 + 1: 6, 8*x/3 + 1: 3, x + 1: 1})


Enumerating rolls works.

    >>> list(p.rolls_with_counts())
    [((x/3, x/3 + 1/3, x/3 + 2/3), 1), ((x, x/3 + 1/3, x/3 + 2/3), 1), ((2*x/3, x/3 + 1/3, x/3 + 2/3), 1), ..., ((2*x/3 + 1/3, 2*x/3 + 2/3, x/3), 1), ((2*x/3 + 1/3, 2*x/3 + 2/3, x), 1), ((2*x/3, 2*x/3 + 1/3, 2*x/3 + 2/3), 1)]


[`P.roll`][dyce.P.roll] “works” (i.e., falls back to natural ordering of outcomes), but that is a deliberate compromise of convenience.

<!-- BEGIN MONKEY PATCH --
For deterministic outcomes.

>>> import random
>>> from dyce import rng
>>> rng.RNG = random.Random(1776137574)

  -- END MONKEY PATCH -->

    >>> p.roll()
    (2*x/3, 2*x/3 + 2/3, x + 1/3)


[`P.apply_to_each_h`][dyce.P.apply_to_each_h] can help pave the way back to concrete outcomes.

    >>> f = lambda outcome: outcome.subs({sympy.abc.x: sympy.Rational(1, 3)})
    >>> p.apply_to_each_h(f)
    P(H({1/9: 1, 2/9: 1, 1/3: 1}), H({4/9: 1, 5/9: 1, 2/3: 1}), H({7/9: 1, 8/9: 1, 1: 1}))
    >>> p.apply_to_each_h(f).h(-1)
    H({7/9: 9, 8/9: 9, 1: 9})


## Further exploration

Consider delving into some [applications and translations](translations.md) for more sophisticated examples, or jump right into the [API](dyce.md).

Anywhere you see a JupyterLite logo ![JupyterLite](https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg), you can click on it to immediately start tinkering with a temporal instance of that example.
Just be aware that changes are stored in browser memory, so make sure to download any notebooks you want to preserve.

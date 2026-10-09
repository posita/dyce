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

# Checking Angry’s math on the [Tension Pool](https://theangrygm.com/definitive-tension-pool/)

In the [Angry GM](https://theangrygm.com/)’s publication of the [PDF version of his Tension Pool mechanic](https://theangrygm.com/wp-content/uploads/The-Tension-Pool.pdf), he includes some probabilities.
Can `dyce` check his work?
You bet!

Let’s reproduce his tables (with slightly different names to provide context).

| d6s in pool | Angry’s probability of at least one `1` showing |
|:-----------:|:-----------------------------------------------:|
| 1           | 16.7%                                           |
| 2           | 30.6%                                           |
| 3           | 42.1%                                           |
| 4           | 51.8%                                           |
| 5           | 59.8%                                           |
| 6           | 66.5%                                           |

How do we do compute these results using `dyce`?

    >>> from dyce import H
    >>> one_in_d6 = H(6).eq(1)
    >>> for n in range(1, 7):  # (1)!
    ...     ones_in_nd6 = n @ one_in_d6
    ...     at_least_one_one_in_nd6 = ones_in_nd6.ge(1)
    ...     print(f"{n}: {at_least_one_one_in_nd6[1] / at_least_one_one_in_nd6.total:6.2%}")
    1: 16.67%
    2: 30.56%
    3: 42.13%
    4: 51.77%
    5: 59.81%
    6: 66.51%

1. Iterates `n` over the range ${1..6}$

So far so good.
Let’s keep going.

| 1d8 + 1d12 | Rarity or Severity   |
|:----------:|:--------------------:|
| 2-4        | Very Rare or Extreme |
| 5-6        | Rare or Major        |
| 7-8        | Uncommon or Moderate |
| 9-13       | Common or Minor      |
| 14-15      | Uncommon or Moderate |
| 16-17      | Rare or Major        |
| 18-20      | Very Rare or Extreme |

We need to map semantic outcomes to numbers (and back again).
How can we represent those in `dyce`?
One way is [`IntEnum`](https://docs.python.org/3/library/enum.html#intenum)s.
`IntEnum`s have a property that allows them to substitute directly for `int`s, which, with a little nudging, is very convenient.

    >>> from enum import IntEnum

    >>> class Complication(IntEnum):
    ...     NONE = 0  # this will come in handy later
    ...     COMMON = 1
    ...     UNCOMMON = 2
    ...     RARE = 3
    ...     VERY_RARE = 4

    >>> OUTCOME_TO_RARITY_MAP = {
    ...     2: Complication.VERY_RARE,
    ...     3: Complication.VERY_RARE,
    ...     4: Complication.VERY_RARE,
    ...     5: Complication.RARE,
    ...     6: Complication.RARE,
    ...     7: Complication.UNCOMMON,
    ...     8: Complication.UNCOMMON,
    ...     9: Complication.COMMON,
    ...     10: Complication.COMMON,
    ...     11: Complication.COMMON,
    ...     12: Complication.COMMON,
    ...     13: Complication.COMMON,
    ...     14: Complication.UNCOMMON,
    ...     15: Complication.UNCOMMON,
    ...     16: Complication.RARE,
    ...     17: Complication.RARE,
    ...     18: Complication.VERY_RARE,
    ...     19: Complication.VERY_RARE,
    ...     20: Complication.VERY_RARE,
    ... }

Now let’s use our map to validate the probabilities of a particular outcome using that d8 and d12.

| Rarity or impact     | Angry’s probability of a Complication arising |
|:--------------------:|:---------------------------------------------:|
| Common or Minor      | 41.7%                                         |
| Uncommon or Moderate | 27.1%                                         |
| Rare or Major        | 18.8%                                         |
| Very Rare or Extreme | 12.5%                                         |

    >>> from dyce import H, HResult, expand
    >>> from pprint import pprint
    >>> d8d12 = H(8) + H(12)

    >>> def rarity(h_result: HResult[int]) -> Complication:
    ...     return OUTCOME_TO_RARITY_MAP[h_result.outcome]

    >>> prob_of_complication: H[Complication] = expand(rarity, d8d12)
    >>> pprint(
    ...     {
    ...         outcome: f"{float(prob):5.1%}"
    ...         for outcome, prob in prob_of_complication.probability_items()
    ...     }
    ... )
    {<Complication.COMMON: 1>: '41.7%',
     <Complication.UNCOMMON: 2>: '27.1%',
     <Complication.RARE: 3>: '18.8%',
     <Complication.VERY_RARE: 4>: '12.5%'}

Lookin’ good!
Now let’s put everything together.

| d6s in pool | None  | Common | Uncommon | Rare  | Very Rare |
|:-----------:|:-----:|:------:|:--------:|:-----:|:---------:|
| 1           | 83.3% | 7.0%   | 4.5%     | 3.1%  | 2.1%      |
| 2           | 69.4% | 12.7%  | 8.3%     | 5.7%  | 3.8%      |
| 3           | 57.9% | 17.6%  | 11.4%    | 7.9%  | 5.3%      |
| 4           | 48.2% | 21.6%  | 14.0%    | 9.7%  | 6.5%      |
| 5           | 40.2% | 24.9%  | 16.2%    | 11.2% | 7.5%      |
| 6           | 33.5% | 27.7%  | 18.0%    | 12.5% | 8.3%      |

    >>> for n in range(1, 7):
    ...     ones_in_nd6 = n @ one_in_d6
    ...     at_least_one_one_in_nd6 = ones_in_nd6.ge(1)
    ...     prob_complication_in_nd6 = at_least_one_one_in_nd6 * prob_of_complication
    ...     complications_for_nd6 = {
    ...         Complication(outcome).name: f"{float(prob):5.1%}"
    ...         for outcome, prob in (prob_complication_in_nd6).probability_items()
    ...     }
    ...     print("{} -> {}".format(n, complications_for_nd6))
    1 -> {'NONE': '83.3%', 'COMMON': ' 6.9%', 'UNCOMMON': ' 4.5%', 'RARE': ' 3.1%', 'VERY_RARE': ' 2.1%'}
    2 -> {'NONE': '69.4%', 'COMMON': '12.7%', 'UNCOMMON': ' 8.3%', 'RARE': ' 5.7%', 'VERY_RARE': ' 3.8%'}
    3 -> {'NONE': '57.9%', 'COMMON': '17.6%', 'UNCOMMON': '11.4%', 'RARE': ' 7.9%', 'VERY_RARE': ' 5.3%'}
    4 -> {'NONE': '48.2%', 'COMMON': '21.6%', 'UNCOMMON': '14.0%', 'RARE': ' 9.7%', 'VERY_RARE': ' 6.5%'}
    5 -> {'NONE': '40.2%', 'COMMON': '24.9%', 'UNCOMMON': '16.2%', 'RARE': '11.2%', 'VERY_RARE': ' 7.5%'}
    6 -> {'NONE': '33.5%', 'COMMON': '27.7%', 'UNCOMMON': '18.0%', 'RARE': '12.5%', 'VERY_RARE': ' 8.3%'}

Well butter my butt, and call me a biscuit! 🤠
That Angry guy sure knows his math!

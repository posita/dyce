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

The following examples and translations are intended to showcase `dyce`’s flexibility.
If you have exposure to another tool, they may also help with transition.

<!-- BEGIN MONKEY PATCH --
>>> import warnings
>>> from dyce import TruncationWarning
>>> from dyce.lifecycle import ExperimentalWarning
>>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
>>> warnings.filterwarnings("ignore", category=TruncationWarning)

   -- END MONKEY PATCH -->

## Checking Angry’s math on the [Tension Pool](https://theangrygm.com/definitive-tension-pool/)

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
    >>> for n in range(1, 7):
    ...     ones_in_nd6 = n @ one_in_d6
    ...     at_least_one_one_in_nd6 = ones_in_nd6.ge(1)
    ...     print(f"{n}: {at_least_one_one_in_nd6[1] / at_least_one_one_in_nd6.total:6.2%}")
    1: 16.67%
    2: 30.56%
    3: 42.13%
    4: 51.77%
    5: 59.81%
    6: 66.51%

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

Well butter my butt, and call me a biscuit!
That Angry guy sure knows his math!

## Modeling *Ironsworn*’s core mechanic

[Shawn Tomlin’s *Ironsworn*](https://www.ironswornrpg.com/) melds a number of different influences in a fresh way.
Its core mechanic involves rolling an *action die* (a d6), adding a modifier, and comparing the result to two *challenge dice* (d10s).
If the modified value from the action die is strictly greater than both challenge dice, the result is a strong success.
If it is strictly greater than only one challenge die, the result is a weak success.
If it is equal to or less than both challenge dice, it’s a failure.

A verbose way to model this is to enumerate the product of the three dice and then perform logical comparisons.
However, if we recognize that our problem involves a [dependent probability](countin.md#dependent-probabilities), we can craft a solution in terms of [`expand`][dyce.expand].
We can also deploy a counting trick with the two d10s.

    >>> from dyce import H, HResult, expand
    >>> from enum import IntEnum, auto
    >>> d6 = H(6)
    >>> d10 = H(10)
    >>> action_mods = list(range(-1, 4))

    >>> class IronResult(IntEnum):
    ...     FAILURE = 0
    ...     WEAK_SUCCESS = 1
    ...     STRONG_SUCCESS = 2

    >>> def iron_dependent_term(action: HResult[int]) -> H[int]:
    ...     return 2 @ d10.lt(action.outcome)

    >>> iron_distributions_by_action_mod = {
    ...     action_mod: expand(iron_dependent_term, d6 + action_mod).zero_fill(IronResult)
    ...     for action_mod in action_mods
    ... }
    >>> for action_mod, iron_distribution in iron_distributions_by_action_mod.items():
    ...     print(
    ...         "{:+} -> {}".format(
    ...             action_mod,
    ...             {
    ...                 IronResult(outcome).name: f"{float(prob):6.2%}"
    ...                 for outcome, prob in iron_distribution.probability_items()
    ...             },
    ...         )
    ...     )
    -1 -> {'FAILURE': '71.67%', 'WEAK_SUCCESS': '23.33%', 'STRONG_SUCCESS': ' 5.00%'}
    +0 -> {'FAILURE': '59.17%', 'WEAK_SUCCESS': '31.67%', 'STRONG_SUCCESS': ' 9.17%'}
    +1 -> {'FAILURE': '45.17%', 'WEAK_SUCCESS': '39.67%', 'STRONG_SUCCESS': '15.17%'}
    +2 -> {'FAILURE': '33.17%', 'WEAK_SUCCESS': '43.67%', 'STRONG_SUCCESS': '23.17%'}
    +3 -> {'FAILURE': '23.17%', 'WEAK_SUCCESS': '43.67%', 'STRONG_SUCCESS': '33.17%'}

!!! question "What’s with that `#!python 2 @ d10.lt(action.outcome)`?"

    Let’s break it down.
    `#!python H(10).lt(value)` will tell us how often a single d10 is less than `#!python value`.

            >>> H(10).lt(5)  # how often a d10 is strictly less than 5
            H({False: 6, True: 4})

    By taking advantage of the fact that, in Python, `#!python bool`s act like `#!python int`s when it comes to arithmetic operators, we can count how often that happens with more than one interchangeable d10 by “summing” them.

            >>> d10_lt5 = H(10).lt(5)
            >>> d10_lt5 + d10_lt5
            H({0: 36, 1: 48, 2: 16})
            >>> (d10_lt5 + d10_lt5).total
            100


    How do we interpret those results?
    36 times out of a hundred, neither d10 will be strictly less than five.
    48 times out of a hundred, exactly one of the d10s will be strictly less than five.
    16 times out of a hundred, both d10s will be strictly less than five.

    [`H`][dyce.H]’s `#!python @` operator provides a shorthand.

            >>> 2 @ d10_lt5 == d10_lt5 + d10_lt5
            True

!!! question "Why doesn’t `#!python 2 @ H(6).gt(H(10)` work?"

    `#!python H(6).gt(H(10))` will compute how often a six-sided die is strictly greater than a ten-sided die.
    `#!python 2 @ H(6).gt(H(10))` will show the frequencies that a first six-sided die is strictly greater than a first ten-sided die and a second six-sided die is strictly greater than a second ten-sided die.
    This isn’t quite what we want, since the mechanic calls for rolling a single six-sided die and comparing that result to each of two ten-sided dice.

Now for a *twist*.
A failure or success is particularly spectacular when the d10s come up doubles.
The key to mapping that to `dyce` internals is recognizing that we have a dependent probability that involves *three* independent variables: the (modded) d6, a first d10, and a second d10.

[`expand`][dyce.expand] is especially useful where there are multiple independent terms.

```python
--8<-- "docs/assets/plot_ironsworn.py:core"
```

By defining our dependent term function to include `#!python mod` as a keyword-only parameter, we can pass values to it via [`expand`][dyce.expand], which is helpful for visualization.

Table:

```python
--8<-- "docs/assets/plot_ironsworn.py:table"
```

<style type="text/css">
</style>
<table id="T_ironsworn">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ironsworn_level0_col0" class="col_heading level0 col0" >SPECTACULAR_FAILURE</th>
      <th id="T_ironsworn_level0_col1" class="col_heading level0 col1" >FAILURE</th>
      <th id="T_ironsworn_level0_col2" class="col_heading level0 col2" >WEAK_SUCCESS</th>
      <th id="T_ironsworn_level0_col3" class="col_heading level0 col3" >STRONG_SUCCESS</th>
      <th id="T_ironsworn_level0_col4" class="col_heading level0 col4" >SPECTACULAR_SUCCESS</th>
    </tr>
    <tr>
      <th class="index_name level0" >Action Modifier</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ironsworn_level0_row0" class="row_heading level0 row0" >-1</th>
      <td id="T_ironsworn_row0_col0" class="data row0 col0" >8.33%</td>
      <td id="T_ironsworn_row0_col1" class="data row0 col1" >63.33%</td>
      <td id="T_ironsworn_row0_col2" class="data row0 col2" >23.33%</td>
      <td id="T_ironsworn_row0_col3" class="data row0 col3" >3.33%</td>
      <td id="T_ironsworn_row0_col4" class="data row0 col4" >1.67%</td>
    </tr>
    <tr>
      <th id="T_ironsworn_level0_row1" class="row_heading level0 row1" >0</th>
      <td id="T_ironsworn_row1_col0" class="data row1 col0" >7.50%</td>
      <td id="T_ironsworn_row1_col1" class="data row1 col1" >51.67%</td>
      <td id="T_ironsworn_row1_col2" class="data row1 col2" >31.67%</td>
      <td id="T_ironsworn_row1_col3" class="data row1 col3" >6.67%</td>
      <td id="T_ironsworn_row1_col4" class="data row1 col4" >2.50%</td>
    </tr>
    <tr>
      <th id="T_ironsworn_level0_row2" class="row_heading level0 row2" >1</th>
      <td id="T_ironsworn_row2_col0" class="data row2 col0" >6.50%</td>
      <td id="T_ironsworn_row2_col1" class="data row2 col1" >38.67%</td>
      <td id="T_ironsworn_row2_col2" class="data row2 col2" >39.67%</td>
      <td id="T_ironsworn_row2_col3" class="data row2 col3" >11.67%</td>
      <td id="T_ironsworn_row2_col4" class="data row2 col4" >3.50%</td>
    </tr>
    <tr>
      <th id="T_ironsworn_level0_row3" class="row_heading level0 row3" >2</th>
      <td id="T_ironsworn_row3_col0" class="data row3 col0" >5.50%</td>
      <td id="T_ironsworn_row3_col1" class="data row3 col1" >27.67%</td>
      <td id="T_ironsworn_row3_col2" class="data row3 col2" >43.67%</td>
      <td id="T_ironsworn_row3_col3" class="data row3 col3" >18.67%</td>
      <td id="T_ironsworn_row3_col4" class="data row3 col4" >4.50%</td>
    </tr>
    <tr>
      <th id="T_ironsworn_level0_row4" class="row_heading level0 row4" >3</th>
      <td id="T_ironsworn_row4_col0" class="data row4 col0" >4.50%</td>
      <td id="T_ironsworn_row4_col1" class="data row4 col1" >18.67%</td>
      <td id="T_ironsworn_row4_col2" class="data row4 col2" >43.67%</td>
      <td id="T_ironsworn_row4_col3" class="data row4 col3" >27.67%</td>
      <td id="T_ironsworn_row4_col4" class="data row4 col4" >5.50%</td>
    </tr>
  </tbody>
</table>

Visualization: <a href="../jupyter/lab/?path=ironsworn.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_ironsworn.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_ironsworn_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_ironsworn_light.svg">
  <img alt="Plot: Ironsworn distributions" src="../assets/plot_ironsworn_light.svg">
</picture>

## Modeling “[The Probability of 4d6, Drop the Lowest, Reroll 1s](http://prestonpoulter.com/2010/11/19/the-probability-of-4d6-drop-the-lowest-reroll-1s/)”

```python
--8<-- "docs/assets/plot_4d6_variants.py:core"
```

Visualization: <a href="../jupyter/lab/?path=4d6_variants.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_4d6_variants.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_4d6_variants_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_4d6_variants_light.svg">
  <img alt="Plot: Comparing various take-three-of-4d6 methods" src="../assets/plot_4d6_variants_light.svg">
</picture>

## Translating one example from [`markbrockettrobson/python_dice`](https://github.com/markbrockettrobson/python_dice#usage)

Source:

    # …
    program = [
      "VAR save_roll = d20",
      "VAR burning_arch_damage = 10d6 + 10",
      "VAR pass_save = ( save_roll >= 10 ) ",
      "VAR damage_half_on_save = burning_arch_damage // (pass_save + 1)",
      "damage_half_on_save"
    ]
    # …

Translation:

```python
--8<-- "docs/assets/plot_burning_arch.py:core"
```

Visualization: <a href="../jupyter/lab/?path=burning_arch.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_burning_arch.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_burning_arch_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_burning_arch_light.svg">
  <img alt="Plot: Attack with saving throw for half damage" src="../assets/plot_burning_arch_light.svg">
</picture>

An alternative using [`expand`][dyce.expand]:

    >>> from dyce import H, expand
    >>> import operator
    >>> save_roll = H(20)
    >>> burning_arch_damage = 10 @ H(6) + 10
    >>> damage_half_on_save = burning_arch_damage // (save_roll.ge(10) + 1)
    >>> expand(
    ...     lambda h_result: (
    ...         burning_arch_damage // 2
    ...         if operator.__ge__(h_result.outcome, 10)
    ...         else burning_arch_damage
    ...     ),
    ...     save_roll,
    ... ) == damage_half_on_save
    True

## More translations from [`markbrockettrobson/python_dice`](https://github.com/markbrockettrobson/python_dice#usage)

    >>> # VAR name = 1 + 2d3 - 3 * 4d2 // 5
    >>> name = 1 + (2 @ H(3)) - 3 * (4 @ H(2)) // 5
    >>> print(name.format_short())
    {avg: 1.75, -1:  3.47%, 0: 13.89%, 1: 25.00%, 2: 29.17%, 3: 19.44%, 4:  8.33%, 5:  0.69%}

<!-- -->

    >>> # VAR out = 3 * ( 1 + 1d4 )
    >>> out = 3 * (1 + 2 @ H(4))
    >>> print(out.format_short())
    {avg: 18.00, 9:  6.25%, 12: 12.50%, 15: 18.75%, 18: 25.00%, 21: 18.75%, 24: 12.50%, 27:  6.25%}

<!-- -->

    >>> # VAR g = (1d4 >= 2) AND !(1d20 == 2)
    >>> g = H(4).ge(2) & H(20).ne(2)
    >>> print(g.format_short())
    {..., False: 28.75%, True: 71.25%}

<!-- -->

    >>> # VAR h = (1d4 >= 2) OR !(1d20 == 2)
    >>> h_bool = H(4).ge(2) | H(20).ne(2)
    >>> print(h_bool.format_short())
    {..., False:  1.25%, True: 98.75%}

<!-- -->

    >>> # VAR abs = ABS( 1d6 - 1d6 )
    >>> abs_h = abs(H(6) - H(6))
    >>> print(abs_h.format_short())
    {avg: 1.94, 0: 16.67%, 1: 27.78%, 2: 22.22%, 3: 16.67%, 4: 11.11%, 5:  5.56%}

<!-- -->

    >>> # MAX(4d7, 2d10)

    >>> # this takes the max of a pool of four d7s and two d10s
    >>> from dyce import P
    >>> max_h = P(4 @ P(7), 2 @ P(10)).h(-1)
    >>> print(max_h.format_short())
    {avg: 7.78, 1:  0.00%, 2:  0.03%, 3:  0.28%, 4:  1.40%, 5:  4.80%, 6: 12.92%, 7: 29.57%, 8: 15.00%, 9: 17.00%, 10: 19.00%}

    >>> # this takes the max of pool of a first die behaving like the sum of
    >>> # 4d7 and a second die behaving like a the sum of 2d10, which is a
    >>> # very different thing
    >>> max_h = P(4 @ H(7), 2 @ H(10)).h(-1)
    >>> print(max_h.format_short())
    {avg: 16.60, 4:  0.00%, 5:  0.02%, 6:  0.07%, 7:  0.21%, ..., 25:  0.83%, 26:  0.42%, 27:  0.17%, 28:  0.04%}

<!-- -->

    >>> # MIN(50, d%)
    >>> min_h = P(H((50,)), P(100)).h(0)
    >>> print(min_h.format_short())
    {avg: 37.75, 1:  1.00%, 2:  1.00%, 3:  1.00%, ..., 47:  1.00%, 48:  1.00%, 49:  1.00%, 50: 51.00%}

## Translations from [`LordSembor/DnDice`](https://github.com/LordSembor/DnDice#examples)

Example 1 source:

    from DnDice import d, gwf
    single_attack = 2*d(6) + 5
    # …
    great_weapon_fighting = gwf(2*d(6)) + 5
    # …
    # comparison of the probability
    print(single_attack.expectancies())
    print(great_weapon_fighting.expectancies())
    # [ 0.03,  0.06, 0.08, 0.11, 0.14, 0.17, 0.14, ...] (single attack)
    # [0.003, 0.006, 0.03, 0.05, 0.10, 0.15, 0.17, ...] (gwf attack)
    # …

Example 1 translation:

```python
--8<-- "docs/assets/plot_great_weapon_fighting.py:core"
```

Example 1 table:

<details>
<summary>
  Table source code
</summary>

```python
--8<-- "docs/assets/plot_great_weapon_fighting.py:table"
```
</details>

<style type="text/css">
</style>
<table id="T_gwf">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_gwf_level0_col0" class="col_heading level0 col0" >7</th>
      <th id="T_gwf_level0_col1" class="col_heading level0 col1" >8</th>
      <th id="T_gwf_level0_col2" class="col_heading level0 col2" >9</th>
      <th id="T_gwf_level0_col3" class="col_heading level0 col3" >10</th>
      <th id="T_gwf_level0_col4" class="col_heading level0 col4" >11</th>
      <th id="T_gwf_level0_col5" class="col_heading level0 col5" >12</th>
      <th id="T_gwf_level0_col6" class="col_heading level0 col6" >13</th>
      <th id="T_gwf_level0_col7" class="col_heading level0 col7" >14</th>
      <th id="T_gwf_level0_col8" class="col_heading level0 col8" >15</th>
      <th id="T_gwf_level0_col9" class="col_heading level0 col9" >16</th>
      <th id="T_gwf_level0_col10" class="col_heading level0 col10" >17</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_gwf_level0_row0" class="row_heading level0 row0" >Normal attack</th>
      <td id="T_gwf_row0_col0" class="data row0 col0" >3%</td>
      <td id="T_gwf_row0_col1" class="data row0 col1" >6%</td>
      <td id="T_gwf_row0_col2" class="data row0 col2" >8%</td>
      <td id="T_gwf_row0_col3" class="data row0 col3" >11%</td>
      <td id="T_gwf_row0_col4" class="data row0 col4" >14%</td>
      <td id="T_gwf_row0_col5" class="data row0 col5" >17%</td>
      <td id="T_gwf_row0_col6" class="data row0 col6" >14%</td>
      <td id="T_gwf_row0_col7" class="data row0 col7" >11%</td>
      <td id="T_gwf_row0_col8" class="data row0 col8" >8%</td>
      <td id="T_gwf_row0_col9" class="data row0 col9" >6%</td>
      <td id="T_gwf_row0_col10" class="data row0 col10" >3%</td>
    </tr>
    <tr>
      <th id="T_gwf_level0_row1" class="row_heading level0 row1" >“GWF” (2014)</th>
      <td id="T_gwf_row1_col0" class="data row1 col0" >0%</td>
      <td id="T_gwf_row1_col1" class="data row1 col1" >1%</td>
      <td id="T_gwf_row1_col2" class="data row1 col2" >3%</td>
      <td id="T_gwf_row1_col3" class="data row1 col3" >5%</td>
      <td id="T_gwf_row1_col4" class="data row1 col4" >10%</td>
      <td id="T_gwf_row1_col5" class="data row1 col5" >15%</td>
      <td id="T_gwf_row1_col6" class="data row1 col6" >17%</td>
      <td id="T_gwf_row1_col7" class="data row1 col7" >20%</td>
      <td id="T_gwf_row1_col8" class="data row1 col8" >15%</td>
      <td id="T_gwf_row1_col9" class="data row1 col9" >10%</td>
      <td id="T_gwf_row1_col10" class="data row1 col10" >5%</td>
    </tr>
    <tr>
      <th id="T_gwf_level0_row2" class="row_heading level0 row2" >“GWF” (2024)</th>
      <td id="T_gwf_row2_col0" class="data row2 col0" >nan%</td>
      <td id="T_gwf_row2_col1" class="data row2 col1" >nan%</td>
      <td id="T_gwf_row2_col2" class="data row2 col2" >nan%</td>
      <td id="T_gwf_row2_col3" class="data row2 col3" >nan%</td>
      <td id="T_gwf_row2_col4" class="data row2 col4" >25%</td>
      <td id="T_gwf_row2_col5" class="data row2 col5" >17%</td>
      <td id="T_gwf_row2_col6" class="data row2 col6" >19%</td>
      <td id="T_gwf_row2_col7" class="data row2 col7" >22%</td>
      <td id="T_gwf_row2_col8" class="data row2 col8" >8%</td>
      <td id="T_gwf_row2_col9" class="data row2 col9" >6%</td>
      <td id="T_gwf_row2_col10" class="data row2 col10" >3%</td>
    </tr>
  </tbody>
</table>

Example 1 visualization: <a href="../jupyter/lab/?path=great_weapon_fighting.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

<details>
<summary>
  Visualization source code
</summary>

```python
--8<-- "docs/assets/plot_great_weapon_fighting.py:viz"
```
</details>

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_great_weapon_fighting_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_great_weapon_fighting_light.svg">
  <img alt="Plot: Comparing a normal attack to an enhanced one" src="../assets/plot_great_weapon_fighting_light.svg">
</picture>

Example 2 source:

    from DnDice import d, advantage, plot

    normal_hit = 1*d(12) + 5
    critical_hit = 3*d(12) + 5

    result = d()
    for value, probability in advantage():
      if value == 20:
        result.layer(critical_hit, weight=probability)
      elif value + 5 >= 14:
        result.layer(normal_hit, weight=probability)
      else:
        result.layer(d(0), weight=probability)
    result.normalizeExpectancies()
    # …

Example 2 translation:

```python
--8<-- "docs/assets/plot_advantage.py:core"
```

Example 2 visualization: <a href="../jupyter/lab/?path=advantage.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_advantage.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_advantage_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_advantage_light.svg">
  <img alt="Plot: Advantage-weighted attack with critical hits" src="../assets/plot_advantage_light.svg">
</picture>

## Translation of the accepted answer to “[Roll and Keep in Anydice?](https://rpg.stackexchange.com/a/166637)”

Source:

```
\ How best to model this in a way that allows testing 1k1 to 10k5? \
output [highest 3 of 10d [explode d10]] named "10k3"
```

Translation:

```python
--8<-- "docs/assets/plot_d10_explode.py:core"
```

Visualization: <a href="../jupyter/lab/?path=d10_explode.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

<details>
<summary>
  Visualization source code
</summary>

```python
--8<-- "docs/assets/plot_d10_explode.py:viz"
```
</details>

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_d10_explode_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_d10_explode_light.svg">
  <img alt="Plot: Taking the *k* highest of *n* exploding d10s" src="../assets/plot_d10_explode_light.svg">
</picture>

## Translation of the accepted answer to “[How do I count the number of duplicates in anydice?](https://rpg.stackexchange.com/a/111421)”

Source:

```
function: dupes in DICE:s {
  D: 0
  loop X over {2..#DICE} {
    if ((X-1)@DICE = X@DICE) { D: D + 1}
  }
  result: D
}
```

Translation:

```python
--8<-- "docs/assets/plot_dupes.py:core"
```

Visualization: <a href="../jupyter/lab/?path=dupes.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_dupes.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_dupes_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_dupes_light.svg">
  <img alt="Plot: Chances of rolling *n* duplicates" src="../assets/plot_dupes_light.svg">
</picture>

## Translation of “[How do I implement this specialized roll-and-keep mechanic in AnyDice?](https://rpg.stackexchange.com/a/190806)”

Source:

```
function: N:n of SIZE:n keep K:n extras add {
    result: [helper NdSIZE SIZE K]
}

function: helper ROLL:s SIZE:n K:n {
    COUNT: [count SIZE in ROLL]
    if COUNT > K { result: K*SIZE - K + COUNT }
    result: {1..K}@ROLL
}

D: 6
K: 3

loop N over {K+1..K+8} {
  output [N of D keep K extras add] named "[N]d[D] keep [K] extras add +1"
}
loop N over {K+1..K+8} {
  output {1..K}@NdD named "[N]d[D] keep [K]"
}
```

Translation:

```python
--8<-- "docs/assets/plot_roll_and_keep.py:core"
```

Visualization: <a href="../jupyter/lab/?path=roll_and_keep.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_roll_and_keep.py:viz"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_roll_and_keep_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_roll_and_keep_light.svg">
  <img alt="Plot: Roll-and-keep mechanic comparison" src="../assets/plot_roll_and_keep_light.svg">
</picture>

## Translation of the accepted answer to “[Modelling opposed dice pools with a swap](https://rpg.stackexchange.com/a/112951)”

Source of basic `brawl`:

```
function: brawl A:s vs B:s {
  SA: A >= 1@B
  SB: B >= 1@A
  if SA-SB=0 {
    result:(A > B) - (A < B)
  }
  result:SA-SB
}
output [brawl 3d6 vs 3d6] named "A vs B Damage"
```

Translation:

    >>> from dyce.evaluation import PResult

    >>> def brawl(p_result_a: PResult[int], p_result_b: PResult[int]):
    ...     a_successes = sum(1 for v in p_result_a.roll if v >= p_result_b.roll[-1])
    ...     b_successes = sum(1 for v in p_result_b.roll if v >= p_result_a.roll[-1])
    ...     return a_successes - b_successes

Rudimentary textual visualization using built-in methods:

    >>> from dyce import P, expand
    >>> p3d6 = 3 @ P(6)
    >>> res = expand(brawl, p3d6, p3d6)
    >>> print(res.format(width=65))
    avg |    0.00
    std |    1.73
    var |    2.99
     -3 |   7.86% |###
     -2 |  15.52% |#######
     -1 |  16.64% |########
      0 |  19.96% |#########
      1 |  16.64% |########
      2 |  15.52% |#######
      3 |   7.86% |###

Source of `brawl` with an optional dice swap:

```
function: set element I:n in SEQ:s to N:n {
  NEW: {}
  loop J over {1 .. #SEQ} {
    if I = J { NEW: {NEW, N} }
    else { NEW: {NEW, J@SEQ} }
  }
  result: NEW
}
function: brawl A:s vs B:s with optional swap {
  if #A@A >= 1@B {
    result: [brawl A vs B]
  }
  AX: [sort [set element #A in A to 1@B]]
  BX: [sort [set element 1 in B to #A@A]]
  result: [brawl AX vs BX]
}
output [brawl 3d6 vs 3d6 with optional swap] named "A vs B Damage"
```

Translation:

    >>> def brawl_w_optional_swap(p_result_a: PResult[int], p_result_b: PResult[int]):
    ...     roll_a, roll_b = p_result_a.roll, p_result_b.roll
    ...     if roll_a[0] < roll_b[-1]:
    ...         roll_a, roll_b = roll_a[1:] + roll_b[-1:], roll_a[:1] + roll_b[:-1]
    ...         # Sort greatest-to-least after the swap
    ...         roll_a = tuple(sorted(roll_a, reverse=True))
    ...         roll_b = tuple(sorted(roll_b, reverse=True))
    ...     else:
    ...         # Reverse to be greatest-to-least
    ...         roll_a = roll_a[::-1]
    ...         roll_b = roll_b[::-1]
    ...     a_successes = sum(1 for v in roll_a if v >= roll_b[0])
    ...     b_successes = sum(1 for v in roll_b if v >= roll_a[0])
    ...     return a_successes - b_successes or (roll_a > roll_b) - (roll_a < roll_b)

Rudimentary visualization using built-in methods:

    >>> res = expand(brawl_w_optional_swap, p3d6, p3d6)
    >>> print(res.format(width=65))
    avg |    2.36
    std |    0.88
    var |    0.77
     -1 |   1.42% |
      0 |   0.59% |
      1 |  16.65% |########
      2 |  23.19% |###########
      3 |  58.15% |#############################

    >>> p4d6 = 4 @ P(6)
    >>> res = expand(brawl_w_optional_swap, p4d6, p4d6)
    >>> print(res.format(width=65))
    avg |    2.64
    std |    1.28
    var |    1.64
     -2 |   0.06% |
     -1 |   2.94% |#
      0 |   0.31% |
      1 |  18.16% |#########
      2 |  19.97% |#########
      3 |  25.19% |############
      4 |  33.37% |################

## Advanced topic—modeling *Risis*

[S. John Ross’s *Risus*](https://www.risusiverse.com/) and its many [community-developed alternative rules](http://www.risusiverse.com/home/optional-rules) not only make for entertaining reading, but are fertile ground for stressing ergonomics and capabilities of any discrete outcome modeling tool.
We can easily model the first round of its opposed combat system for various starting configurations.
Our first step is a callback for [`H.apply`][dyce.H.apply] for refereeing a head-to-head contest of values:

```python
--8<-- "docs/assets/plot_risus.py:base"
```

!!! note

    As an aside, this reasonably common “versus” pattern can be characterized in a more concise (albeit less readable) way:

            >>> from dyce.d import d6
            >>> ours = 2 @ d6
            >>> theirs = 3 @ d6
            >>> (ours - theirs).apply(
            ...     lambda outcome: outcome // abs(outcome) if outcome else outcome
            ... ).lowest_terms()
            H({-1: 1009, 0: 90, 1: 197})

Example use for a single round of combat:

```python
--8<-- "docs/assets/plot_risus.py:base-use"
```

```linenums="0"
--8<-- "docs/assets/plot_risus_evens_up_base_use.txt"
```

This highlights the mechanic’s notorious “death spiral”, which we can visualize as a heat map.

```python
--8<-- "docs/assets/plot_risus.py:display"
```

<details>
<summary>
  Visualization source code
</summary>

```python
--8<-- "docs/assets/plot_risus.py:display-detail"
```
</details>

Visualization: <a href="../jupyter/lab/?path=risus.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_risus.py:viz-first-round"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_risus_first_round_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_risus_first_round_light.svg">
  <img alt="Plot: Modeling the Risus combat mechanic after the first roll" src="../assets/plot_risus_first_round_light.svg">
</picture>

### Modeling entire multi-round combats

With a little ~~elbow~~ *finger* grease, we can roll up our … erm … fingerless gloves and even model how various starting conditions affect combat completion (in this case, applying dynamic programming to avoid redundant computations).

```python
--8<-- "docs/assets/plot_risus.py:driver"
```

There’s lot going on there.
Thankfully, it’s heavily annotated.
It’s worth going back and dissecting as a fairly nuanced application of [`expand`][dyce.expand].

!!! note

    This is a complicated example that involves some fairly sophisticated programming techniques (recursion, memoization, nested functions, etc.).
    The point is not to suggest that such techniques are required to be productive.
    However, it is useful to show that `dyce` is flexible enough to model these types of outcomes in a couple dozen lines of code.
    It is high-level enough to lean on for nuanced number crunching without a lot of detailed knowledge, while still being low-level enough that authors knowledgeable of advanced programming techniques are not precluded from using them.

When called with its default arguments, `#!python risus_combat_driver` satisfies the `#!python VersusFuncT` interface.
This means we can use it directly with our `#!python vs_scenarios_dataframes` helper to enumerate resolution outcomes from various starting positions.

Visualization: <a href="../jupyter/lab/?path=risus.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_risus.py:viz-multi-round-standard"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_risus_multi_round_standard_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_risus_multi_round_standard_light.svg">
  <img alt="Plot: Modeling the Risus combat mechanic after the first roll" src="../assets/plot_risus_multi_round_standard_light.svg">
</picture>

### Modeling different combat resolution methods

Using our `#!python risus_combat_driver` from above, we can craft a alternative resolution function to model the less death-spirally “Best of Set” alternative mechanic from *[The Risus Companion](https://i.4pcdn.org/tg/1366392953060.pdf)* (free with membership to the [IOR](https://www.risusiverse.com/home/ior-charter)) with the optional “Goliath Rule” for resolving ties.


```python
--8<-- "docs/assets/plot_risus.py:goliath-rule"
```

```python
--8<-- "docs/assets/plot_risus.py:vs-best-of-set"
```

Python’s [`#!python functools.partial`](https://docs.python.org/3/library/functools.html#functools.partial) allows us to override individual function details, but still leverage our current callback machinery.
This pattern will come up again below, so we’ll capture it in a helper function.

```python
--8<-- "docs/assets/plot_risus.py:viz-multi-round-goliath-helper"
```

<details>
<summary>
  Visualization Goliath Rule helper source code
</summary>

```python
--8<-- "docs/assets/plot_risus.py:viz-multi-round-goliath-helper-detail"
```
</details>

We’ll use that Goliath Rule helper to approximate a complete “Best-of-Set” combat and compare it to a “standard” one.

Visualization: <a href="../jupyter/lab/?path=risus.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_risus.py:viz-multi-round-best-of-set"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_risus_multi_round_best_of_set_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_risus_multi_round_best_of_set_light.svg">
  <img alt="Plot: Modeling the Risus combat mechanic after the first roll" src="../assets/plot_risus_multi_round_best_of_set_light.svg">
</picture>

The “[Evens Up](http://www.risusiverse.com/home/optional-rules/evens-up)” alternative dice mechanic presents some challenges.

First, `dyce`’s substitution mechanism only resolves outcomes through a fixed number of iterations, so it can only approximate probabilities for infinite series.
Most of the time, the implications are largely theoretical for a sufficient number of iterations.
This is no exception.

Another limitation is that `dyce` only provides a mechanism to directly expand outcomes, not counts.
This means we can’t arbitrarily *increase* the likelihood of achieving a particular outcome through replacement.
With some creativity, we can work around that, too.

In the case of “Evens Up”, we need to keep track of whether an even number was rolled, but we also need to keep rolling (and accumulating) as long as sixes are rolled.
This behaves a lot like an exploding die with three values (miss, hit, and hit-and-explode).
Further, we can observe that every “run” will be zero or more exploding hits terminated by either a miss or a non-exploding hit.

If we choose our values carefully, we can encode how many times we’ve encountered relevant events as we explode.

```python
--8<-- "docs/assets/plot_risus.py:evens-up-base"
```

```linenums="0"
--8<-- "docs/assets/plot_risus_evens_up_base.txt"
```

For every value that is even, we ended in a miss.
For every value that is odd, we ended in a hit that will need to be tallied.
Dividing by two and ignoring any remainder will tell us how many exploding hits we had along the way.

```python
--8<-- "docs/assets/plot_risus.py:evens-up-decode-hits"
```

```linenums="0"
--8<-- "docs/assets/plot_risus_evens_up_decode_hits.txt"
```

Now we can craft an “Evens Up” implementation suitable for passing to our `#!python risus_combat_driver`.

```python
--8<-- "docs/assets/plot_risus.py:evens-up"
```

We’ll use that to approximate a complete “Evens Up” combat, continuing to leveraging our Goliath Rule helper from above.

Visualization: <a href="../jupyter/lab/?path=risus.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>

```python
--8<-- "docs/assets/plot_risus.py:viz-multi-round-evens-up"
```

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_risus_multi_round_evens_up_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/plot_risus_multi_round_evens_up_light.svg">
  <img alt="Plot: Modeling the Risus combat mechanic after the first roll" src="../assets/plot_risus_multi_round_evens_up_light.svg">
</picture>

*Phew!*
What a journey!
Hopefully this highlights some of `dyce`’s flexibility and capabilities.
If you’d like help using `dyce` with modeling your own complicated mechanics, [drop me a line](https://posita.github.io/dyce/latest/contrib/#starting-discussions-and-filing-issues)!

<!-- BEGIN MONKEY PATCH --
>>> warnings.resetwarnings()

   -- END MONKEY PATCH -->

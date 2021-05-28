<!-- -*- encoding: utf-8 -*-
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!

  WARNING: THIS DOCUMENT MUST BE SELF-CONTAINED.
  ALL LINKS MUST BE ABSOLUTE.
  This file is used on GitHub and PyPi (via setup.py).
  There is no guarantee that other docs/resources will be available where this content is displayed.
-->

*Copyright and other protections apply.
Please see the accompanying `LICENSE` file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its original, then please contact the author before viewing or using this software in any capacity.*

[![v0.2.1 Version](https://img.shields.io/pypi/v/dycelib/0.2.1.svg)](https://pypi.python.org/pypi/dycelib/0.2.1)
[![v0.2.1 Development Stage](https://img.shields.io/pypi/status/dycelib/0.2.1.svg)](https://pypi.python.org/pypi/dycelib/0.2.1)
[![v0.2.1 License](https://img.shields.io/pypi/l/dycelib/0.2.1.svg)](http://opensource.org/licenses/MIT)
[![v0.2.1 Supported Python Versions](https://img.shields.io/pypi/pyversions/dycelib/0.2.1.svg)](https://pypi.python.org/pypi/dycelib/0.2.1)
[![v0.2.1 Supported Python Implementations](https://img.shields.io/pypi/implementation/dycelib/0.2.1.svg)](https://pypi.python.org/pypi/dycelib/0.2.1)

# `dyce` - simple Python tools for dice-based probabilities

[![Build Status](https://travis-ci.com/posita/dyce.svg?version=v0.2.1)](https://travis-ci.com/posita/dyce?version=v0.2.1)

> :point_up: *Curious about integrating your project with the above services?
  Jeff Knupp ([**@jeffknupp**](https://github.com/jeffknupp)) [describes how](https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/).*

``dyce`` is a pure-Python library for exploring dice probabilities designed to be immediately and broadly useful with minimal additional investment beyond basic knowledge of Python.
``dyce`` is an [AnyDice](https://anydice.com/) replacement that leverages Pythonic syntax and operators for rolling dice and computing weighted outcomes.
While Python is not as terse as a dedicated grammar, it is quite sufficient, and often more expressive.
Those familiar with various [game notations](https://en.wikipedia.org/wiki/Dice_notation) should be able to adapt quickly.

``dyce`` is fairly low level by design, prioritizing ergonomics and composability.
While any AnyDice generously affords a very convenient platform for simple computations, its idiosyncrasies can lead to [confusion](https://duckduckgo.com/?q=site%3Astackexchange.com+title%3Aanydice) and complicated workarounds.
Like AnyDice, it avoids stochastic simulation, but instead determines outcomes through enumeration and discrete computation.
Unlike AnyDice, however, it is an open source library that can be run locally and modified as desired.
Because it exposes Python primitives rather than defining a dedicated grammar and interpreter, one can easily integrate it with other Python tools and libraries.
In an intentional departure from [RFC 1925, § 2.2](https://datatracker.ietf.org/doc/html/rfc1925#section-2), it provides minor computation optimizations (e.g., the [``H.lowest_terms`` method](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.lowest_terms) and various shorthands) and formatting conveniences (e.g., the [``H.data``](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.data), [``H.data_xy``](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.data_xy), and [``H.format``](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.format) methods) for casual tinkering.
However, it really shines when used in larger contexts such as with [Matplotlib](https://matplotlib.org/) or [Jupyter](https://jupyter.org/).

``dyce`` should be sufficient to replicate or replace AnyDice and most other dice probability modeling libraries.
It strives to be [fully documented](https://posita.github.io/dyce/0.2/) and relies heavily on examples to develop understanding.
If you find its functionality or documentation confusing or lacking in any way, please consider [contributing an issue](docs/contrib.md) to start a discussion.

`dyce` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the accompanying ``LICENSE`` file for details.
Source code is [available on GitHub](https://github.com/posita/dyce).

## A taste

``dyce`` provides two key primitives.
``H`` objects represent histograms for modeling individual dice and outcomes.
``P`` objects represent pools (ordered sequences) of histograms.
Both support a variety of operations.

```python
>>> from dyce import H
>>> d6 = H(6)  # a standard six-sided die
>>> 2@d6 + 4  # 2d6 + 4
H({6: 1, 7: 2, 8: 3, 9: 4, 10: 5, 11: 6, 12: 5, 13: 4, 14: 3, 15: 2, 16: 1})
>>> d6.lt(d6)  # how often a first six-sided die shows a face less than a second
H({0: 21, 1: 15})
>>> abs(d6 - d6)  # subtract the least of two six-sided dice from the greatest
H({0: 6, 1: 10, 2: 8, 3: 6, 4: 4, 5: 2})

```

```python
>>> from dyce import P
>>> p_2d6 = 2@P(d6)  # a pool of two six-sided dice
>>> p_2d6.h()  # pools can be collapsed into histograms
H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
>>> p_2d6 == 2@d6  # pools and histograms are comparable
True

```

One can "take" individual dice from pools, ordered least to greatest. (The [``H.format`` method](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.format) provides rudimentary visualization for convenience.)

```python
>>> p_2d6.h(0)
H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})
>>> print(_.format(width=65))
avg |    2.53
  1 |  30.56% |###############
  2 |  25.00% |############
  3 |  19.44% |#########
  4 |  13.89% |######
  5 |   8.33% |####
  6 |   2.78% |#

```

```python
>>> p_2d6.h(-1)
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

See [the docs](https://posita.github.io/dyce/0.2/) for a much more thorough treatment, including detailed examples.

### Applications and translations

#### Modeling “[The Probability of 4d6, Drop the Lowest, Reroll 1s](http://prestonpoulter.com/2010/11/19/the-probability-of-4d6-drop-the-lowest-reroll-1s/)”

```python
>>> p_4d6 = 4@P(6)
>>> _ = p_4d6.h(slice(1, None))  # discard the lowest die (index 0)
>>> print(_.format(width=65))
 avg |   12.24
   3 |   0.08% |
   4 |   0.31% |
   5 |   0.77% |
   6 |   1.62% |
   7 |   2.93% |#
   8 |   4.78% |##
   9 |   7.02% |###
  10 |   9.41% |####
  11 |  11.42% |#####
  12 |  12.89% |######
  13 |  13.27% |######
  14 |  12.35% |######
  15 |  10.11% |#####
  16 |   7.25% |###
  17 |   4.17% |##
  18 |   1.62% |

```

```python
>>> d6_reroll_first_one = H(6).substitute(lambda h, f: H(6) if f == 1 else f)
>>> p_4d6_reroll_first_one = (4@P(d6_reroll_first_one))
>>> _ = p_4d6_reroll_first_one.h(slice(1, None))  # discard the lowest
>>> print(_.format(width=65))
avg |   13.27
  3 |   0.00% |
  4 |   0.00% |
  5 |   0.02% |
  6 |   0.26% |
  7 |   0.87% |
  8 |   1.99% |
  9 |   3.91% |#
 10 |   6.73% |###
 11 |   9.81% |####
 12 |  12.88% |######
 13 |  14.93% |#######
 14 |  15.52% |#######
 15 |  13.83% |######
 16 |  10.50% |#####
 17 |   6.25% |###
 18 |   2.51% |#

```

```python
>>> p_4d6_reroll_all_ones = 4@P(H(range(2, 7)))
>>> _ = p_4d6_reroll_all_ones.h(slice(1, None))  # discard the lowest
>>> print(_.format(width=65))
 avg |   13.43
   6 |   0.16% |
   7 |   0.64% |
   8 |   1.60% |
   9 |   3.36% |#
  10 |   6.08% |###
  11 |   9.28% |####
  12 |  12.64% |######
  13 |  15.04% |#######
  14 |  16.00% |########
  15 |  14.56% |#######
  16 |  11.20% |#####
  17 |   6.72% |###
  18 |   2.72% |#

```

#### Translating one example from [`markbrockettrobson/python_dice`](https://github.com/markbrockettrobson/python_dice#usage)

Source:

```python
# …
program = [
  "VAR save_roll = d20",
  "VAR burning_arch_damage = 10d6 + 10",
  "VAR pass_save = ( save_roll >= 10 ) ",
  "VAR damage_half_on_save = burning_arch_damage // (pass_save + 1)",
  "damage_half_on_save"
]
# …
```

Translation:

```python
>>> save_roll = H(20)
>>> burning_arch_damage = 10@H(6) + 10
>>> pass_save = save_roll.ge(10)
>>> damage_half_on_save = burning_arch_damage // (pass_save + 1)
>>> res = damage_half_on_save
>>> print(res.format(width=0))
{avg: 32.49, 10:  0.00%, ..., 18:  2.44%, 19:  4.02%, 20:  5.75%, 21:  7.21%, 22:  7.93%, 23:  7.68%, 24:  6.55%, 25:  4.89%, 26:  3.19%, ..., 41:  2.53%, 42:  2.83%, 43:  3.07%, 44:  3.22%, 45:  3.27%, 46:  3.22%, 47:  3.07%, 48:  2.83%, 49:  2.53%, ..., 70:  0.00%}

```

An alternative using the [``H.substitute`` method](https://posita.github.io/dyce/latest/dyce/#dyce.h.H.substitute):

```python
>>> _ = save_roll.substitute(
...   lambda h, f:
...     burning_arch_damage // 2 if f >= 10
...     else burning_arch_damage
... )
>>> save_roll.substitute(
...   lambda h, f:
...     burning_arch_damage // 2 if f >= 10
...     else burning_arch_damage
... ) == res
True

```

#### More translations from [`markbrockettrobson/python_dice`](https://github.com/markbrockettrobson/python_dice#usage)

```python
>>> # VAR name = 1 + 2d3 - 3 * 4d2 // 5
>>> name = 1 + (2@H(3)) - 3 * (4@H(2)) // 5
>>> print(name.format(width=0))
{avg: 1.75, -1:  3.47%, 0: 13.89%, 1: 25.00%, 2: 29.17%, 3: 19.44%, 4:  8.33%, 5:  0.69%}

```

```python
>>> # VAR out = 3 * ( 1 + 1d4 )
>>> out = 3 * (1 + 2@H(4))
>>> print(out.format(width=0))
{avg: 18.00, 9:  6.25%, 12: 12.50%, 15: 18.75%, 18: 25.00%, 21: 18.75%, 24: 12.50%, 27:  6.25%}

```

```python
>>> # VAR g = (1d4 >= 2) AND !(1d20 == 2)
>>> g = H(4).ge(2) & H(20).ne(2)
>>> print(g.format(width=0))
{..., 0: 28.75%, 1: 71.25%}

```

```python
>>> # VAR h = (1d4 >= 2) OR !(1d20 == 2)
>>> h = H(4).ge(2) | H(20).ne(2)
>>> print(h.format(width=0))
{..., 0:  1.25%, 1: 98.75%}

```

```python
>>> # VAR abs = ABS( 1d6 - 1d6 )
>>> abs_ = abs(H(6) - H(6))
>>> print(abs_.format(width=0))
{avg: 1.94, 0: 16.67%, 1: 27.78%, 2: 22.22%, 3: 16.67%, 4: 11.11%, 5:  5.56%}

```

```python
>>> # MAX(4d7, 2d10)
>>> _ = P(4@H(7), 2@H(10)).h(-1)
>>> print(_.format(width=0))
{avg: 16.60, 4:  0.00%, 5:  0.02%, 6:  0.07%, 7:  0.21%, ..., 25:  0.83%, 26:  0.42%, 27:  0.17%, 28:  0.04%}

```

```python
>>> # MIN(50, d%)
>>> _ = P(H((50,)), P(100)).h(0)
>>> print(_.format(width=0))
{avg: 37.75, 1:  1.00%, 2:  1.00%, 3:  1.00%, ..., 47:  1.00%, 48:  1.00%, 49:  1.00%, 50: 51.00%}

```

#### Translations from [`LordSembor/DnDice`](https://github.com/LordSembor/DnDice#examples)

Example 1 source:

```python
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
```

Example 1 translation:

```python
>>> single_attack = 2@H(6) + 5
>>> print(single_attack.format(width=0))
{avg: 12.00, 7:  2.78%, 8:  5.56%, 9:  8.33%, 10: 11.11%, 11: 13.89%, 12: 16.67%, 13: 13.89%, 14: 11.11%, 15:  8.33%, 16:  5.56%, 17:  2.78%}

>>> def gwf(h: H, face: int):  # type: (...) -> Union[int, H]
...   return h if face in (1, 2) else face

>>> great_weapon_fighting = 2@(H(6).substitute(gwf)) + 5  # reroll either die if it's a one or two
>>> print(great_weapon_fighting.format(width=0))
{avg: 13.33, 7:  0.31%, 8:  0.62%, 9:  2.78%, 10:  4.94%, 11:  9.88%, 12: 14.81%, 13: 17.28%, 14: 19.75%, 15: 14.81%, 16:  9.88%, 17:  4.94%}

```

Example 2 source:

```python
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
```

Example 2 translation:

```python
>>> normal_hit = H(12) + 5
>>> print(normal_hit.format(width=0))
{avg: 11.50, 6:  8.33%, 7:  8.33%, 8:  8.33%, ..., 16:  8.33%, 17:  8.33%}

>>> critical_hit = 3@H(12) + 5
>>> print(critical_hit.format(width=0))
{avg: 24.50, 8:  0.06%, 9:  0.17%, 10:  0.35%, 11:  0.58%, ..., 38:  0.58%, 39:  0.35%, 40:  0.17%, 41:  0.06%}

>>> advantage = (2@P(20)).h(-1)

>>> def crit(h: H, f: int):  # type: (...) -> Union[int, H]
...   if f == 20: return critical_hit
...   elif f + 5 >= 14: return normal_hit
...   else: return 0

>>> print(advantage.substitute(crit).format(width=0))
{avg: 10.93, 0: 16.00%, 6:  6.19%, 7:  6.19%, ..., 16:  6.44%, 17:  6.50%, 18:  0.37%, 19:  0.44%, ..., 40:  0.02%, 41:  0.01%}

```

#### Translation of the accepted answer to “[How to count near duplicates in a mixed pool using AnyDice?](https://rpg.stackexchange.com/questions/179046/how-to-count-near-duplicates-in-a-mixed-pool-using-anydice)”

Source:

```
function: near dupes in A:s B:s C:s {
  DICE: {A, B, C}
  DUPES: 0
  loop DIE over DICE {
    SAME: [count DIE in DICE]
    NEAR: [count {DIE-1, DIE+1} in DICE]
    if SAME > 1 | NEAR > 0 { DUPES: DUPES + 1 }
  }
  result: DUPES
}
output [near dupes in 1d12 2d10 1d8]
```

Translation:

```python
>>> def near_dupes(p: P):  # type: (...) -> Iterator[Tuple[int, int]]
...   for roll, count in p.rolls_with_counts():
...     dupes = set()
...     for i in range(1, len(roll)):
...       # Faces are ordered, so we only have to look at one neighbor
...       if roll[i - 1] >= roll[i] - 1:
...         dupes.update((i - 1, i))
...     yield len(dupes), count

>>> _ = H(near_dupes(P(H(8), H(10), H(10), H(12)))).lowest_terms()
>>> print(_.format(width=0))
{..., 0: 11.50%, 2: 46.50%, 3: 24.62%, 4: 17.38%}

```

#### Translation of the accepted answer to “[Modelling \[sic\] opposed dice pools with a swap](https://rpg.stackexchange.com/questions/112735/modelling-opposed-dice-pools-with-a-swap/112951#112951)”:

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

```python
>>> from itertools import product

>>> def brawl(a: P, b: P):  # type: (...) -> Iterator[Tuple[int, int]]
...   for (roll_a, count_a), (roll_b, count_b) in product(
...       a.rolls_with_counts(),
...       b.rolls_with_counts(),
...   ):
...     a_successes = sum(1 for f in roll_a if f >= roll_b[-1])
...     b_successes = sum(1 for f in roll_b if f >= roll_a[-1])
...     yield a_successes - b_successes, count_a * count_b

>>> _ = H(brawl(3@P(6), 3@P(6))).lowest_terms()
>>> print(_.format(width=0))
{avg: 0.00, -3:  7.86%, -2: 15.52%, -1: 16.64%, 0: 19.96%, 1: 16.64%, 2: 15.52%, 3:  7.86%}

```

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

```python
>>> def brawl_w_optional_swap(a: P, b: P):  # type: (...) -> Iterator[Tuple[int, int]]
...   for (roll_a, count_a), (roll_b, count_b) in product(
...       a.rolls_with_counts(),
...       b.rolls_with_counts(),
...   ):
...     if roll_a[0] < roll_b[-1]:
...       roll_a, roll_b = roll_a[1:] + roll_b[-1:], roll_a[:1] + roll_b[:-1]
...     roll_a = sorted(roll_a, reverse=True)
...     roll_b = sorted(roll_b, reverse=True)
...     a_successes = sum(1 for f in roll_a if f >= roll_b[0])
...     b_successes = sum(1 for f in roll_b if f >= roll_a[0])
...     result = a_successes - b_successes or int(roll_a > roll_b) - int(roll_a < roll_b)
...     yield result, count_a * count_b

>>> _ = H(brawl_w_optional_swap(3@P(6), 3@P(6))).lowest_terms()
>>> print(_.format(width=0))
{avg: 2.36, -1:  1.42%, 0:  0.59%, 1: 16.65%, 2: 23.19%, 3: 58.15%}

>>> _ = H(brawl_w_optional_swap(4@P(6), 4@P(6))).lowest_terms()
>>> print(_.format(width=0))
{avg: 2.64, -2:  0.06%, -1:  2.94%, 0:  0.31%, 1: 18.16%, 2: 19.97%, 3: 25.19%, 4: 33.37%}

```

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

[![v0.2.2 Version](https://img.shields.io/pypi/v/dycelib/0.2.2.svg)](https://pypi.python.org/pypi/dycelib/0.2.2)
[![v0.2.2 Development Stage](https://img.shields.io/pypi/status/dycelib/0.2.2.svg)](https://pypi.python.org/pypi/dycelib/0.2.2)
[![v0.2.2 License](https://img.shields.io/pypi/l/dycelib/0.2.2.svg)](http://opensource.org/licenses/MIT)
[![v0.2.2 Supported Python Versions](https://img.shields.io/pypi/pyversions/dycelib/0.2.2.svg)](https://pypi.python.org/pypi/dycelib/0.2.2)
[![v0.2.2 Supported Python Implementations](https://img.shields.io/pypi/implementation/dycelib/0.2.2.svg)](https://pypi.python.org/pypi/dycelib/0.2.2)

# `dyce` - simple Python tools for dice-based probabilities

[![Build Status](https://travis-ci.com/posita/dyce.svg?version=v0.2.2)](https://travis-ci.com/posita/dyce?version=v0.2.2)

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
In an intentional departure from [RFC 1925, § 2.2](https://datatracker.ietf.org/doc/html/rfc1925#section-2), it provides minor computation optimizations (e.g., the [``H.lowest_terms`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.lowest_terms) and various shorthands) and formatting conveniences (e.g., the [``H.data``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.data), [``H.data_xy``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.data_xy), and [``H.format``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.format) methods) for casual tinkering.
However, it really shines when used in larger contexts such as with [Matplotlib](https://matplotlib.org/) or [Jupyter](https://jupyter.org/).

``dyce`` should be sufficient to replicate or replace AnyDice and most other dice probability modeling libraries.
It strives to be [fully documented](https://posita.github.io/dyce/0.2/) and relies heavily on examples to develop understanding.
If you find its functionality or documentation confusing or lacking in any way, please consider [contributing an issue](docs/contrib.md) to start a discussion.

`dyce` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the accompanying ``LICENSE`` file for details.
Source code is [available on GitHub](https://github.com/posita/dyce).

## A taste

``dyce`` provides two key primitives.
[``H`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H) represent histograms for modeling individual dice and outcomes.
[``P`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.p.P) objects represent pools (ordered sequences) of histograms.
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

One can "take" individual dice from pools, ordered least to greatest. (The [``H.format`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.format) provides rudimentary visualization for convenience.)

```python
>>> p_2d6.h(0)
H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})
>>> print(_.format(width=65))
avg |    2.53
std |    1.40
var |    1.97
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
std |    1.40
var |    1.97
  1 |   2.78% |#
  2 |   8.33% |####
  3 |  13.89% |######
  4 |  19.44% |#########
  5 |  25.00% |############
  6 |  30.56% |###############

```

[``H`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H) provide a [``data`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.data) and a [``data_xy`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.data_xy) to ease integration with plotting packages like [``matplotlib``](https://matplotlib.org/stable/api/index.html):

```python
>>> matplotlib.pyplot.style.use("dark_background")  # doctest: +SKIP

>>> faces, probabilities = p_2d6.h(0).data_xy(relative=True)
>>> matplotlib.pyplot.bar(
...   [str(f) for f in faces],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Lowest die of 2d6",
... )  # doctest: +SKIP

>>> faces, probabilities = p_2d6.h(-1).data_xy(relative=True)
>>> matplotlib.pyplot.bar(
...   [str(f) for f in faces],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Highest die of 2d6",
... )  # doctest: +SKIP

>>> matplotlib.pyplot.legend()  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_2d6_lo_hi_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_2d6_lo_hi_gh.png)

See [the docs](https://posita.github.io/dyce/0.2/) for a much more thorough treatment, including detailed examples.

### Applications and translations

#### Modeling “[The Probability of 4d6, Drop the Lowest, Reroll 1s](http://prestonpoulter.com/2010/11/19/the-probability-of-4d6-drop-the-lowest-reroll-1s/)”

```python
>>> p_4d6 = 4@P(6)
>>> _ = p_4d6.h(slice(1, None))  # discard the lowest die (index 0)
>>> faces, probabilities = _.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="Discard lowest",
... )  # doctest: +SKIP

>>> d6_reroll_first_one = H(6).substitute(lambda h, f: H(6) if f == 1 else f)
>>> p_4d6_reroll_first_one = (4@P(d6_reroll_first_one))
>>> _ = p_4d6_reroll_first_one.h(slice(1, None))  # discard the lowest
>>> faces, probabilities = _.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="Re-roll first 1; discard lowest",
... )  # doctest: +SKIP

>>> p_4d6_reroll_all_ones = 4@P(H(range(2, 7)))
>>> _ = p_4d6_reroll_all_ones.h(slice(1, None))  # discard the lowest
>>> faces, probabilities = _.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="Re-roll all 1s; discard lowest",
... )  # doctest: +SKIP

>>> matplotlib.pyplot.legend()  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_4d6_variants_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_4d6_variants_gh.png)

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
>>> faces, probabilities = res.data_xy(relative=True)
>>> matplotlib.pyplot.plot(faces, probabilities, marker=".")  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_burning_arch_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_burning_arch_gh.png)

An alternative using the [``H.substitute`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.substitute):

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
>>> faces, probabilities = single_attack.data_xy(relative=True)
>>> matplotlib.pyplot.bar(
...   [f - 0.125 for f in faces],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Single Attack",
... )  # doctest: +SKIP

>>> def gwf(h: H, face: int):  # type: (...) -> Union[int, H]
...   return h if face in (1, 2) else face

>>> great_weapon_fighting = 2@(H(6).substitute(gwf)) + 5  # reroll either die if it's a one or two
>>> faces, probabilities = great_weapon_fighting.data_xy(relative=True)
>>> matplotlib.pyplot.bar(
...   [f + 0.125 for f in faces],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Great Weapon Fighting",
... )  # doctest: +SKIP

>>> matplotlib.pyplot.legend()  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_great_weapon_fighting_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_great_weapon_fighting_gh.png)

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
>>> faces, probabilities = normal_hit.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="normal hit",
... )  # doctest: +SKIP

>>> critical_hit = 3@H(12) + 5
>>> faces, probabilities = critical_hit.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="critical hit",
... )  # doctest: +SKIP

>>> advantage = (2@P(20)).h(-1)

>>> def crit(_: H, f: int):  # type: (...) -> Union[int, H]
...   if f == 20: return critical_hit
...   elif f + 5 >= 14: return normal_hit
...   else: return 0

>>> advantage_weighted = advantage.substitute(crit)
>>> faces, probabilities = advantage_weighted.data_xy(relative=True)
>>> matplotlib.pyplot.plot(
...   faces,
...   probabilities,
...   marker=".",
...   label="d20 advantage-weighted",
... )  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_advantage_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_advantage_gh.png)

#### Translation of the accepted answer to “[Roll and Keep in Anydice?](https://rpg.stackexchange.com/questions/166633/roll-and-keep-in-anydice)”

Source:

```
output [highest 3 of 5d [explode d10]] named "Exploded 5k3"
```

Translation:

```python
>>> _ = (5@P(H(10).explode(max_depth=2))).h(slice(-3, None))
>>> faces, probabilities = _.data_xy(relative=True)
>>> matplotlib.pyplot.plot(faces, probabilities, marker=".")  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_d10_explode_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_d10_explode_gh.png)

#### Translation of the accepted answer to “[How do I count the number of duplicates in anydice?](https://rpg.stackexchange.com/questions/111414/how-do-i-count-the-number-of-duplicates-in-anydice/111421#111421)”

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
>>> def dupes(p: P):  # type: (...) -> Iterator[Tuple[int, int]]
...   for roll, count in p.rolls_with_counts():
...     dupes = 0
...     for i in range(1, len(roll)):
...       # Faces are ordered, so we only have to look at one neighbor
...       if roll[i] == roll[i - 1]:
...         dupes += 1
...     yield dupes, count

>>> _ = H(dupes(8@P(10))).lowest_terms()
>>> faces, probabilities = _.data_xy(relative=True)
>>> matplotlib.pyplot.bar(faces, probabilities)  # doctest: +SKIP
>>> matplotlib.pyplot.title(r"Chances of rolling $n$ duplicates in 8d10")  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

![https://raw.githubusercontent.com/posita/dyce/v0.2.2/docs/plot_dupes_gh.png](https://github.com/posita/dyce/blob/v0.2.2/docs/plot_dupes_gh.png)

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
>>> print(_.format(width=65))
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
>>> print(_.format(width=65))
avg |    2.36
std |    0.88
var |    0.77
 -1 |   1.42% |
  0 |   0.59% |
  1 |  16.65% |########
  2 |  23.19% |###########
  3 |  58.15% |#############################

>>> _ = H(brawl_w_optional_swap(4@P(6), 4@P(6))).lowest_terms()
>>> print(_.format(width=65))
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

```

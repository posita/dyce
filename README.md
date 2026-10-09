<!---
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!

  WARNING: THIS DOCUMENT MUST BE SELF-CONTAINED.
  ALL LINKS MUST BE ABSOLUTE.
  This file is used on GitHub and PyPi (via pyproject.toml).
  There is no guarantee that other docs/resources will be available where this content is displayed.
  -->

<!-- docs:hide:start -->
*Copyright and other protections apply.
Please see the accompanying `LICENSE` file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its original, then please contact the author before viewing or using this software in any capacity.*
<!-- docs:hide:end -->

[![Tests](https://github.com/posita/dyce/actions/workflows/tests.yml/badge.svg)](https://github.com/posita/dyce/actions/workflows/tests.yml)
[![Version](https://img.shields.io/pypi/v/dyce.svg)](https://pypi.org/project/dyce/)
[![License](https://img.shields.io/pypi/l/dyce.svg)](https://opensource.org/licenses/MIT)
![Supported Python versions](https://img.shields.io/pypi/pyversions/dyce.svg)
[![Bear-ified™](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://beartype.rtfd.io/)

*Now you’re playing with …*

<img style="float: right; padding: 0 1.0em 0 1.0em;" src="https://raw.githubusercontent.com/posita/dyce/main/docs/dyce.svg" alt="dyce logo">

# `dyce`

`dyce` is a Python library for dice mechanics and other problems with a finite set of possible outcomes.
It counts how many ways each outcome can occur, then calculates exact probabilities.

Suggested audiences and applications:

- Game designers for crafting and compare game mechanics
- Tool developers for using calculations in higher level tooling

## Overview

- [`H`](https://dycelib.org/latest/dyce/#dyce.H) represents possible outcomes and their weights as integer counts.
  A fair, six-sided die can be represented as `H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})`, or the shorthand `H(6)`.
  The sum of three six-sided dice can be represented as `3 @ H(6)`.
- [`P`](https://dycelib.org/latest/dyce/#dyce.P) represents an ordered sequence of histograms.
  A pool of three separate six-sided dice can be represented as `3 @ P(H(6))`, or the shorthand `3 @ P(6)`.
  `P`s keep each die separate, so you can select any die or group of dice and calculate the distribution of their summed results.
- [`P.survey`](https://dycelib.org/latest/dyce/#dyce.P.survey) and [`expand`](https://dycelib.org/latest/dyce/#dyce.expand) are experimental interfaces useful for modeling mechanics where the outcome of one die affects how others are rolled.
  Examples include: exploding dice, conditional re-rolls, or damage that depends on whether an attack hits.
- Optional [Matplotlib](https://dycelib.org/latest/dyce.viz.matplotlib/) and [Plotly](https://dycelib.org/latest/dyce.viz.plotly/) helpers support visualization.

## Example: d20 versus a “target number”

Consider a mechanic where a roll on a fair twenty-sided die “succeeds” when it is greater than or equal to a specific value (a “target number”).
This example compares the outcome distributions for one d20, the higher of two d20s (“advantage”), and the lower of two d20s (“disadvantage”).

```python
>>> from dyce import H, P
>>> d20 = H(20)  # shorthand for an evenly-weighted 20-sided die
>>> d20
H({1: 1, 2: 1, 3: 1, ..., 18: 1, 19: 1, 20: 1})

```

```python
>>> p2d20 = 2 @ P(d20)  # a pool of two such dice
>>> d20_advantage = p2d20.at(-1)  # right-most index (-1) selects highest
>>> d20_disadvantage = p2d20.at(0)  # left-most index (0) selects lowest
>>> d20_advantage
H({1: 1, 2: 3, 3: 5, ..., 18: 35, 19: 37, 20: 39})
>>> d20_disadvantage
H({1: 39, 2: 37, 3: 35, ..., 18: 5, 19: 3, 20: 1})

```

With a single d20, the chance of rolling a 15 or higher is 30%.
With advantage, it climbs to 51%.
With disadvantage, it drops to 9%.

```python
>>> target_number = 15
>>> # How often a d20 is greater than or equal to target_number
>>> d20_vs_target = d20.ge(target_number)
>>> print(d20_vs_target.format())  # built-in text formatting
  avg |    0.30
  std |    0.46
False |  70.00% |#################################
 True |  30.00% |##############

```

```python
>>> d20_advantage_vs_target = d20_advantage.ge(target_number)
>>> print(d20_advantage_vs_target.format_short())
{avg: 0.51, False: 49.00%, True: 51.00%}

```

```python
>>> d20_disadvantage_vs_target = d20_disadvantage.ge(target_number)
>>> print(d20_disadvantage_vs_target.format_short())
{avg: 0.09, False: 91.00%, True:  9.00%}

```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/posita/dyce/main/docs/images/plot_matplotlib_d20_success_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/posita/dyce/main/docs/images/plot_matplotlib_d20_success_light.svg">
  <img alt="Plot: Comparison of the higher of 2d20 vs. a single d20 and the lower of 2d20 vs. a single d20" src="https://raw.githubusercontent.com/posita/dyce/main/docs/images/plot_matplotlib_d20_success_light.svg">
</picture>

As one might expect, with a single d20, each outcome is equally likely, with 10.5 being the average.
With advantage, one is likely to roll at ***least*** a 15 over half the time, and one is nearly twice as likely to roll a 20.
With disadvantage, one is likely to roll at ***most*** a 6 over half the time, and one is nearly twice as likely to roll a 1.

[Run this example in JupyterLite](https://dycelib.org/latest/jupyter/lab/?path=d20_success.ipynb): [<img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try `dyce`!" align="absmiddle">](https://dycelib.org/latest/jupyter/lab/?path=d20_success.ipynb)

## Installation

```sh
python -m pip install dyce
```

`dyce` supports CPython 3.11–3.14 and PyPy 3.11.
It depends on [`optype`](https://jorenham.github.io/optype/) for static and runtime type-checking.
It is available under the [MIT License](https://dycelib.org/latest/license/).

`dyce` will opportunistically use the following, if available:

- [Beartype](https://beartype.github.io/beartype/) for runtime type checking 👌🏾🐻
- [Matplotlib](https://matplotlib.org/) for basic visualization helpers via [`dyce.viz.matplotlib`](https://dycelib.org/latest/dyce.viz.matplotlib/)
- [NumPy](https://numpy.org/) for random number generation

## Explore further

- Consult the [glossary](https://dycelib.org/latest/glossary/) for important terms used in this documentation.
- Read about `dyce`’s [core concepts](https://dycelib.org/latest/concepts/) and operations.
- See [examples](https://dycelib.org/latest/examples/) for worked examples.
- Browse the [API reference](https://dycelib.org/latest/dyce/).
- Read the [contribution guide](https://dycelib.org/latest/contrib/) to report an issue or contribute a change.
- See the [release notes](https://dycelib.org/latest/notes/) for changes between releases.
- Browse the [source code](https://github.com/posita/dyce).

## Other efforts

`dyce` does not stand alone.
Other works include:

- The OG [`dice_roll.py`](https://gist.github.com/vyznev/8f5e62c91ce4d8ca7841974c87271e2f) by Ilmari Karonen
- [`icepool`](https://pypi.org/project/icepool/) by Albert Julius Liu
- [GNOLL](https://pypi.org/project/gnoll/) by Ian Hunter
- [lea](https://pypi.org/project/lea/) by Pierre Denis
- [dice](https://pypi.org/project/dice/) by Sam Clements
- [ossuary](https://github.com/bszonye/ossuary) by B. Szonye
- [PythonDice](https://github.com/Ar-Kareem/PythonDice) by Ar-Kareem
- [dice-notation](https://pypi.org/project/dice-notation/) by Bernardo Martinez Garrido
- Avrae’s [d20](https://pypi.org/project/d20/) by Andrew Zhu
- [python-dice](https://pypi.org/project/python-dice/) by Mark Robson
- [DnDice](https://github.com/LordSembor/DnDice) by “LordSembor”
- [AnyDice](https://anydice.com/) (closed source) by Jasper Flick

Please consider [contributing an issue](https://dycelib.org/latest/contrib/) if you observe discrepancies or think something should be added to the list.

## Donors

When one worries that the flickering light of humanity may be snuffed out at any moment, when one’s heart breaks at the perverse celebration of judgment, vengeance, and death and the demonizing of empathy, compassion, and love, sometimes all that is needed is the kindness of a single stranger to reinvigorate one’s faith that—while all may not be right in the world—there is hope for us human beings.

- [David Eyk](https://eykd.net/about/) not only [inspires others to explore creative writing](https://eykd.net/blog/), but has graciously ceded his PyPI project dedicated to [his own prior work under a similar name](https://code.google.com/archive/p/dyce/).
  As such, `dyce` is now [available as ~~`dycelib`~~ *`dyce`*](https://pypi.org/project/dyce/)!
  Thanks to his generosity, ~~millions~~ *dozens* of future `dyce` users will be spared from typing superfluous characters.
  On behalf of myself, those souls, and our keyboards, we salute you, Mr. Eyk. 🫡

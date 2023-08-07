<!---
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!

  WARNING: THIS DOCUMENT MUST BE SELF-CONTAINED.
  ALL LINKS MUST BE ABSOLUTE.
  This file is used on GitHub and PyPi (via setup.cfg).
  There is no guarantee that other docs/resources will be available where this content is displayed.
-->

*Copyright and other protections apply.
Please see the accompanying ``LICENSE`` file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its original, then please contact the author before viewing or using this software in any capacity.*

[![Tests](https://github.com/posita/dyce/actions/workflows/on-push.yaml/badge.svg)](https://github.com/posita/dyce/actions/workflows/on-push.yaml)
[![Version](https://img.shields.io/pypi/v/dyce/0.6.2.svg)](https://pypi.org/project/dyce/0.6.2/)
[![Development Stage](https://img.shields.io/pypi/status/dyce/0.6.2.svg)](https://pypi.org/project/dyce/0.6.2/)
[![License](https://img.shields.io/pypi/l/dyce/0.6.2.svg)](http://opensource.org/licenses/MIT)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/dyce/0.6.2.svg)](https://pypi.org/project/dyce/0.6.2/)
[![Supported Python Implementations](https://img.shields.io/pypi/implementation/dyce/0.6.2.svg)](https://pypi.org/project/dyce/0.6.2/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![``numerary``-encumbered](https://raw.githubusercontent.com/posita/numerary/latest/docs/numerary-encumbered.svg)](https://posita.github.io/numerary/)
[![Bear-ified™](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://beartype.rtfd.io/)

Now you’re playing with …

<img style="float: right; padding: 0 1.0em 0 1.0em;" src="https://raw.githubusercontent.com/posita/dyce/v0.6.2/docs/dyce.svg" alt="dyce logo">

# ``dyce`` – simple Python tools for exploring dice outcomes and other finite discrete probabilities

**💥 _Now 100% [Bear-ified™](https://beartype.rtfd.io/)!_ 👌🏾🐻**
([Details](#requirements) below.)


``dyce`` is a pure-Python library for modeling arbitrarily complex dice mechanics.
It strives for ***compact expression*** and ***efficient computation***, especially for the most common cases.
Its primary applications are:

1. Computing finite discrete probability distributions for:
    * ***Game designers*** who want to understand or experiment with various dice mechanics and interactions; and
    * ***Design tool developers***.
1. Generating transparent, weighted random rolls for:
    * ***Game environment developers*** who want flexible dice mechanic resolution in, e.g., virtual tabletops (VTTs), chat servers, etc.

Beyond those audiences, ``dyce`` may be useful to anyone interested in exploring finite discrete probabilities but not in developing all the low-level math bits from scratch.

``dyce`` is designed to be immediately and broadly useful with minimal additional investment beyond basic knowledge of Python.
While not as compact as a dedicated grammar, ``dyce``’s Python-based primitives are quite sufficient, and often more expressive.
Those familiar with various [game notations](https://en.wikipedia.org/wiki/Dice_notation) should be able to adapt quickly.
If you’re looking at something on which to build your own grammar or interface, ``dyce`` can serve you well.

``dyce`` should be able to replicate or replace most other dice probability modeling tools.
It strives to be [fully documented](https://posita.github.io/dyce/0.6/) and relies heavily on examples to develop understanding.

``dyce`` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the accompanying ``LICENSE`` file for details.
Non-experimental features should be considered stable (but an unquenchable thirst to increase performance remains).
See the [release notes](https://posita.github.io/dyce/0.6/notes/) for a summary of version-to-version changes.
Source code is [available on GitHub](https://github.com/posita/dyce).

If you find it lacking in any way, please don’t hesitate to [bring it to my attention](https://posita.github.io/dyce/0.6/contrib/).

## Donors

When one worries that the flickering light of humanity may be snuffed out at any moment, when one’s heart breaks at the perverse celebration of judgment, vengeance, and death and the demonizing of empathy, compassion, and love, sometimes all that is needed is the kindness of a single stranger to reinvigorate one’s faith that—while all may not be right in the world—there is hope for us human beings.

* [David Eyk](https://eykd.net/about/) not only [inspires others to explore creative writing](https://eykd.net/blog/), but has graciously ceded his PyPI project dedicated to [his own prior work under a similar name](https://code.google.com/archive/p/dyce/).
  As such, ``dyce`` is now [available as ~~``dycelib``~~ _``dyce``_](https://pypi.org/project/dyce/)!
  Thanks to his generosity, ~~millions~~ *dozens* of future ``dyce`` users will be spared from typing superfluous characters.
  On behalf of myself, those souls, and our keyboards, we salute you, Mr. Eyk. 🙇‍♂️

## A taste

``dyce`` provides several core primitives.
[``H`` objects](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H) represent histograms for modeling finite discrete outcomes, like individual dice.
[``P`` objects](https://posita.github.io/dyce/0.6/dyce/#dyce.p.P) represent pools (ordered sequences) of histograms.
[``R`` objects](https://posita.github.io/dyce/0.6/dyce.r/#dyce.r.R) (covered [elsewhere](https://posita.github.io/dyce/0.6/rollin/)) represent nodes in arbitrary roller trees useful for translating from proprietary grammars and generating weighted random rolls that “show their work” without the overhead of enumeration.
All support a variety of operations.

``` python
>>> from dyce import H
>>> d6 = H(6)  # a standard six-sided die
>>> 2@d6 * 3 - 4  # 2d6 × 3 - 4
H({2: 1, 5: 2, 8: 3, 11: 4, 14: 5, 17: 6, 20: 5, 23: 4, 26: 3, 29: 2, 32: 1})
>>> d6.lt(d6)  # how often a first six-sided die shows a face less than a second
H({False: 21, True: 15})
>>> abs(d6 - d6)  # subtract the least of two six-sided dice from the greatest
H({0: 6, 1: 10, 2: 8, 3: 6, 4: 4, 5: 2})

```

``` python
>>> from dyce import P
>>> p_2d6 = 2@P(d6)  # a pool of two six-sided dice
>>> p_2d6.h()  # pools can be collapsed into histograms
H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
>>> p_2d6 == 2@d6  # pools and histograms are comparable
True

```

By providing an optional argument to the [``P.h`` method](https://posita.github.io/dyce/0.6/dyce/#dyce.p.P.h), one can “take” individual dice from pools, ordered least to greatest.
(The [``H.format`` method](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.format) provides rudimentary visualization for convenience.)

``` python
>>> p_2d6.h(0)  # take the lowest die of 2d6
H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})
>>> print(p_2d6.h(0).format())
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

``` python
>>> p_2d6.h(-1)  # take the highest die of 2d6
H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
>>> print(p_2d6.h(-1).format())
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

[``H`` objects](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H) provide a [``distribution`` method](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.distribution) and a [``distribution_xy`` method](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.distribution_xy) to ease integration with plotting packages
[``anydyce``](https://github.com/posita/anydyce/), for example, makes use of these to integrate with [``matplotlib``](https://matplotlib.org/stable/api/index.html).

<!-- Should match any title of the corresponding plot title -->
<picture>
  <source srcset="https://raw.githubusercontent.com/posita/dyce/v0.6.2/docs/assets/plot_2d6_lo_hi_dark.png" media="(prefers-color-scheme: dark)">
  <img alt="Plot: Taking the lowest or highest die of 2d6" src="https://raw.githubusercontent.com/posita/dyce/v0.6.2/docs/assets/plot_2d6_lo_hi_light.png#gh-light-mode-only"><span style="display: none"><img alt="Plot: Taking the lowest or highest die of 2d6" src="https://raw.githubusercontent.com/posita/dyce/v0.6.2/docs/assets/plot_2d6_lo_hi_dark.png#gh-dark-mode-only"></span>
</picture>
<!-- The above is a ridiculous work-around for GitHub's braindead, proprietary
light/dark image rendering dumpster fire. See
[https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981/87].
-->

<details>
<summary>
  Source: <a href="https://github.com/posita/dyce/blob/v0.6.2/docs/assets/plot_2d6_lo_hi.py"><code>plot_2d6_lo_hi.py</code></a><br>
  Interactive version: <a href="https://posita.github.io/dyce/0.6/jupyter/lab/?path=2d6_lo_hi.ipynb"><img src="https://jupyterlite.readthedocs.io/en/latest/_static/badge.svg" alt="Try dyce"></a>
</summary>

``` python
--8<-- "docs/assets/plot_2d6_lo_hi.py"
```
</details>

[``H`` objects](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H) and [``P`` objects](https://posita.github.io/dyce/0.6/dyce/#dyce.p.P) can generate random rolls.

``` python
>>> d6 = H(6)
>>> d6.roll()  # doctest: +SKIP
4

```

``` python
>>> d10 = H(10) - 1
>>> p_6d10 = 6@P(d10)
>>> p_6d10.roll()  # doctest: +SKIP
(0, 1, 2, 3, 5, 7)

```

See the tutorials on [counting](https://posita.github.io/dyce/0.6/countin/) and [rolling](https://posita.github.io/dyce/0.6/rollin/), as well as the [API guide](https://posita.github.io/dyce/0.6/dyce/) for much more thorough treatments, including detailed examples.

## Design philosophy

``dyce`` is fairly low-level by design, prioritizing ergonomics and composability.
It explicitly avoids stochastic simulation, but instead determines outcomes through enumeration and discrete computation.
That’s a highfalutin way of saying it doesn’t guess.
It *knows*, even if knowing is harder or more limiting.
Which, if we possess a modicum of humility, it often is.

!!! quote

    “It’s frightening to think that you might not know something, but more frightening to think that, by and large, the world is run by people who have faith that they know exactly what is going on.”

    —Amos Tversky

Because ``dyce`` exposes Python primitives rather than defining a dedicated grammar and interpreter, one can more easily integrate it with other tools.[^1]
It can be installed and run anywhere[^2], and modified as desired.
On its own, ``dyce`` is completely adequate for casual tinkering.
However, it really shines when used in larger contexts such as with [Matplotlib](https://matplotlib.org/) or [Jupyter](https://jupyter.org/) or embedded in a special-purpose application.

[^1]:

    You won’t find any lexers, parsers, or tokenizers in ``dyce``’s core, other than straight-up Python.
    That being said, you can always “roll” your own (see what we did there?) and lean on ``dyce`` underneath.
    It doesn’t mind.
    It actually [kind of *likes* it](https://posita.github.io/dyce/0.6/rollin/).

[^2]:

    Okay, maybe not _literally_ anywhere, but [you’d be surprised](https://jokejet.com/guys-i-need-a-network-specialist-with-some-python-experience-its-urgent/).
    Void where prohibited.
    [Certain restrictions](#requirements) apply.
    [Do not taunt Happy Fun Ball](https://youtu.be/GmqeZl8OI2M).

In an intentional departure from [RFC 1925, § 2.2](https://datatracker.ietf.org/doc/html/rfc1925#section-2), ``dyce`` includes some conveniences, such as minor computation optimizations (e.g., the [``H.lowest_terms`` method](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.lowest_terms), various other shorthands, etc.) and formatting conveniences (e.g., the [``H.distribution``](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.distribution), [``H.distribution_xy``](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.distribution_xy), and [``H.format``](https://posita.github.io/dyce/0.6/dyce/#dyce.h.H.format) methods).

## Comparison to alternatives

The following is a best-effort[^3] summary of the differences between various available tools in this space.
Consider exploring the [applications and translations](https://posita.github.io/dyce/0.6/translations/) for added color.

[^3]:

    I have attempted to ensure the above is reasonably accurate, but please consider [contributing an issue](https://posita.github.io/dyce/0.6/contrib/) if you observe discrepancies.

| | [``dyce``](https://pypi.org/project/dyce/)<br>*Bogosian et al.* | [``icepool``](https://pypi.org/project/icepool/)<br>*Albert Julius Liu* | [``dice_roll.py``](https://gist.github.com/vyznev/8f5e62c91ce4d8ca7841974c87271e2f)<br>*Karonen* | [python-dice](https://pypi.org/project/python-dice/)<br>*Robson et al.* | [AnyDice](https://anydice.com/)<br>*Flick* | [d20](https://pypi.org/project/d20/)<br>*Curse LLC* | [DnDice](https://github.com/LordSembor/DnDice)<br>*“LordSembor”* | [dice](https://pypi.org/project/dice/)<br>*Clements et al.* | [dice-notation](https://pypi.org/project/dice-notation/)<br>*Garrido* |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Latest release | 2022 | 2022 | N/A | 2021 | Unknown | 2021 | 2016 | 2021 | 2022 |
| Actively maintained and documented         | ✅ | ✅ | ⚠️[^4] | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Combinatorics optimizations                | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Suitable as a dependency in other projects | ✅ | ✅ | ⚠️[^5] | ✅ | ❌ | ✅ | ⚠️[^5] | ✅ | ❌ |
| Discrete outcome enumeration               | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Arbitrary expressions                      | ✅ | ✅ | ⚠️[^6] | ✅ | ✅ | ✅ | ⚠️[^7] | ❌ | ❌ |
| Arbitrary dice definitions                 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Integrates with other tools                | ✅ | ✅ | ✅ | ⚠️[^8] | ❌ | ⚠️[^8] | ✅ | ⚠️[^8] | ⚠️[^8] |
| Open source (can inspect)                  | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Permissive licensing (can use and extend)  | ✅ | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | ✅ |

[^4]:

    Sparsely documented.
    The author has [expressed a desire](https://rpg.stackexchange.com/a/166663/71245) to release a more polished version.

[^5]:

    Source can be downloaded and incorporated directly, but there is no packaging, versioning, or dependency tracking.

[^6]:

    Callers must perform their own arithmetic and characterize results in terms of a lightweight die primitive, which may be less accessible to the novice.
    That being said, the library is remarkably powerful, given its size.

[^7]:

    Limited arithmetic operations are available.
    The library also provides game-specific functions.

[^8]:

    Results only.
    Input is limited to specialized grammar.

## License

``dyce`` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the included [``LICENSE``](https://posita.github.io/dyce/0.6/license/) file for details.
Source code is [available on GitHub](https://github.com/posita/dyce).

## Installation

Installation can be performed via [PyPI](https://pypi.python.org/pypi/dyce/).

``` sh
% pip install dyce
...
```

Alternately, you can download [the source](https://github.com/posita/dyce) and install manually.

``` sh
% git clone https://github.com/posita/dyce.git
...
% cd dyce
% python -m pip install .  # -or- python -c 'from setuptools import setup ; setup()' install .
...
```

### Requirements

``dyce`` requires a relatively modern version of Python:

* [CPython](https://www.python.org/) (3.9+)
* [PyPy](http://pypy.org/) (CPython 3.9+ compatible)

It has the following runtime dependencies:

* [``numerary``](https://pypi.org/project/numerary/) for ~~proper~~ *best-effort hacking around deficiencies in* static and runtime numeric type-checking
  [![``numerary``-encumbered](https://raw.githubusercontent.com/posita/numerary/latest/docs/numerary-encumbered.svg)](https://posita.github.io/numerary/)

* [``beartype``](https://pypi.org/project/beartype/) for yummy runtime type-checking goodness (a dependency of ``numerary``)
  [![Bear-ified™](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://beartype.rtfd.io/)

``dyce`` will opportunistically use the following, if available at runtime:

* [``numpy``](https://numpy.org/) to supply ``dyce`` with an alternate random number generator implementation

If you use ``beartype`` for type checking your code, but don’t want ``dyce`` or ``numerary`` to use it internally, disable it with [``numerary``’s ``NUMERARY_BEARTYPE`` environment variable](https://posita.github.io/numerary/latest/#requirements).

See the [hacking quick-start](https://posita.github.io/dyce/0.6/contrib/#hacking-quick-start) for additional development and testing dependencies.

## Customers [![``dyce``-powered!](https://raw.githubusercontent.com/posita/dyce/latest/docs/dyce-powered.svg)](https://posita.github.io/dyce/)

* This could be _you_! 👋

Do you have a project that uses ``dyce``?
[Let me know](https://posita.github.io/dyce/0.6/contrib/#starting-discussions-and-filing-issues), and I’ll promote it here!

And don’t forget to do your part in perpetuating gratuitous badge-ification!

``` markdown
<!-- Markdown -->
As of version 1.1, HighRollin is
[![dyce-powered](https://raw.githubusercontent.com/posita/dyce/latest/docs/dyce-powered.svg)][dyce-powered]!
[dyce-powered]: https://posita.github.io/dyce/ "dyce-powered!"
```

``` rst
..
    reStructuredText - see https://docutils.sourceforge.io/docs/ref/rst/directives.html#image

As of version 1.1, HighRollin is |dyce-powered|!

.. |dyce-powered| image:: https://raw.githubusercontent.com/posita/dyce/latest/docs/dyce-powered.svg
   :align: top
   :target: https://posita.github.io/dyce/
   :alt: dyce-powered
```

``` html
<!-- HTML -->
As of version 1.1, HighRollin is <a href="https://posita.github.io/dyce/"><img
  src="https://raw.githubusercontent.com/posita/dyce/latest/docs/dyce-powered.svg"
  alt="dyce-powered"
  style="vertical-align: middle;"></a>!
```

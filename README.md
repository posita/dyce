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

[![v0.2.3 Version](https://img.shields.io/pypi/v/dycelib/0.2.3.svg)](https://pypi.python.org/pypi/dycelib/0.2.3)
[![v0.2.3 Development Stage](https://img.shields.io/pypi/status/dycelib/0.2.3.svg)](https://pypi.python.org/pypi/dycelib/0.2.3)
[![v0.2.3 License](https://img.shields.io/pypi/l/dycelib/0.2.3.svg)](http://opensource.org/licenses/MIT)
[![v0.2.3 Supported Python Versions](https://img.shields.io/pypi/pyversions/dycelib/0.2.3.svg)](https://pypi.python.org/pypi/dycelib/0.2.3)
[![v0.2.3 Supported Python Implementations](https://img.shields.io/pypi/implementation/dycelib/0.2.3.svg)](https://pypi.python.org/pypi/dycelib/0.2.3)

# ``dyce`` – simple Python tools for exploring dice probabilities and outcomes

``dyce`` is a pure-Python library for computing discrete probability distributions.
It is designed to be immediately and broadly useful with minimal additional investment beyond basic knowledge of Python.
While not as compact as a dedicated grammar, ``dyce``’s Python-based primitives are quite sufficient, and often more expressive.
Those familiar with various [game notations](https://en.wikipedia.org/wiki/Dice_notation) should be able to adapt quickly.

``dyce`` should be able to replicate or replace most other dice probability modeling tools.
It strives to be [fully documented](https://posita.github.io/dyce/0.2/) and relies heavily on examples to develop understanding.
If you find it lacking in any way, please consider [contributing an issue](https://posita.github.io/dyce/0.2/contrib) to start a discussion.

``dyce`` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the accompanying ``LICENSE`` file for details.
Source code is [available on GitHub](https://github.com/posita/dyce).

## A taste

``dyce`` provides two key primitives.
[``H`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H) represent histograms for modeling discrete outcomes, like individual dice.
[``P`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.p.P) objects represent pools (ordered sequences) of histograms.
Both support a variety of operations.

```python
>>> from dyce import H
>>> d6 = H(6)  # a standard six-sided die
>>> 2@d6 * 3 - 4  # 2d6 × 3 - 4
H({2: 1, 5: 2, 8: 3, 11: 4, 14: 5, 17: 6, 20: 5, 23: 4, 26: 3, 29: 2, 32: 1})
>>> d6.lt(d6)  # how often a first six-sided die shows a face less than a second
H({False: 21, True: 15})
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

By providing an optional argument to the [``P.h`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.p.P.h), one can “take” individual dice from pools, ordered least to greatest. (The [``H.format`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.format) provides rudimentary visualization for convenience.)

```python
>>> p_2d6.h(0)  # take the lowest die of 2d6
H({1: 11, 2: 9, 3: 7, 4: 5, 5: 3, 6: 1})
>>> print(p_2d6.h(0).format(width=65))
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
>>> p_2d6.h(-1)  # take the highest die of 2d6
H({1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11})
>>> print(p_2d6.h(-1).format(width=65))
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

[``H`` objects](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H) provide a [``distribution`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.distribution) and a [``distribution_xy`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.distribution_xy) to ease integration with plotting packages like [``matplotlib``](https://matplotlib.org/stable/api/index.html):

```python
>>> import matplotlib  # doctest: +SKIP
>>> matplotlib.pyplot.style.use("dark_background")  # doctest: +SKIP

>>> outcomes, probabilities = p_2d6.h(0).distribution_xy()
>>> matplotlib.pyplot.bar(
...   [str(v) for v in outcomes],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Lowest",
... )  # doctest: +SKIP

>>> outcomes, probabilities = p_2d6.h(-1).distribution_xy()
>>> matplotlib.pyplot.bar(
...   [str(v) for v in outcomes],
...   probabilities,
...   alpha=0.75,
...   width=0.5,
...   label="Highest",
... )  # doctest: +SKIP

>>> matplotlib.pyplot.legend()  # doctest: +SKIP
>>> matplotlib.pyplot.title(r"Taking the lowest or highest die of 2d6")  # doctest: +SKIP
>>> matplotlib.pyplot.show()  # doctest: +SKIP

```

<!-- Should match any title of the corresponding plot title -->
![Plot: Taking the lowest or highest die of 2d6](https://github.com/posita/dyce/raw/v0.2.3/docs/plot_2d6_lo_hi_gh.png)

See the [tutorial](https://posita.github.io/dyce/0.2/tutorial) and the [API guide](https://posita.github.io/dyce/0.2/dyce) for a much more thorough treatment, including detailed examples.

## Design philosophy

``dyce`` is fairly low-level by design, prioritizing ergonomics and composability.
It explicitly avoids stochastic simulation, but instead determines outcomes through enumeration and discrete computation.
Because it exposes Python primitives rather than defining a dedicated grammar and interpreter, one can more easily integrate it with other tools.
It can be installed and run anywhere, and modified as desired.
On its own, it is completely adequate for casual tinkering.
However, it really shines when used in larger contexts such as with [Matplotlib](https://matplotlib.org/) or [Jupyter](https://jupyter.org/).

In an intentional departure from [RFC 1925, § 2.2](https://datatracker.ietf.org/doc/html/rfc1925#section-2), ``dyce`` includes some conveniences, such as minor computation optimizations (e.g., the [``H.lowest_terms`` method](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.lowest_terms), various other shorthands, etc.) and formatting conveniences (e.g., the [``H.distribution``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.distribution), [``H.distribution_xy``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.distribution_xy), and [``H.format``](https://posita.github.io/dyce/0.2/dyce/#dyce.h.H.format) methods).

## Comparison to alternatives

The following is a best-effort¹ summary of the differences between various available tools in this space.
Consider exploring the [applications and translations](https://posita.github.io/dyce/0.2/translations) for added color.

| | ``dyce``<br>*Bogosian et al.* | [``dice_roll.py``](https://gist.github.com/vyznev/8f5e62c91ce4d8ca7841974c87271e2f)<br>*Karonen* | [AnyDice](https://anydice.com/)<br>*Flick* | [python_dice](https://pypi.org/project/python-dice/)<br>*Robson et al.* | [d20](https://pypi.org/project/d20/)<br>*Curse LLC* | [DnDice](https://github.com/LordSembor/DnDice)<br>*“LordSembor”* | [dice](https://pypi.org/project/dice/)<br>*Clemens et al.* | [dice-notation](https://pypi.org/project/dice-notation/)<br>*Garrido* | [dyce](https://pypi.org/project/dyce/)<br>*Eyk* |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Actively maintained and documented | ✅ | ⚠² | ✅   | ✅  | ✅  | ❌  | ✅  | ❌  | ❌  |
| Discrete outcome enumeration       | ✅ | ✅  | ✅   | ✅  | ❌  | ✅  | ❌  | ❌  | ❌  |
| Arbitrary expressions              | ✅ | ⚠³ | ✅   | ✅  | ✅  | ⚠⁴ | ❌  | ❌  | ❌  |
| Arbitrary dice definitions         | ✅ | ✅  | ✅   | ❌  | ❌  | ❌  | ❌  | ❌  | ❌  |
| Integrates with other tools        | ✅ | ✅  | ❌   | ⚠⁵ | ⚠⁵ | ✅  | ⚠⁵ | ⚠⁵ | ⚠⁵ |
| Open source                        | ✅ | ✅  | ❌   | ✅  | ✅  | ✅  | ✅  | ✅  | ✅  |
| Permissive licensing               | ✅ | ✅  | N/A | ✅  | ✅  | ✅  | ✅  | ✅  | ✅  |

|Notes|
|---|
| ¹ I have attempted to ensure the above is reasonably accurate, but please consider [contributing an issue](https://posita.github.io/dyce/0.2/contrib) if there are discrepancies. |
| ² Actively maintained, but sparsely documented. The author has [expressed a desire](https://rpg.stackexchange.com/a/166663/71245) to release a more polished version. |
| ³ Callers must perform their own arithmetic and characterize results in terms of a lightweight die primitive, which may be less accessible to the novice. That being said, the library is remarkably powerful, given its size. |
| ⁴ Limited arithmetic operations are available. The library also provides game-specific functions. |
| ⁵ Results only. Input is limited to specialized grammar. |

## License

``dyce`` is licensed under the [MIT License](https://opensource.org/licenses/MIT).
See the included [``LICENSE``](https://posita.github.io/dyce/0.2/license) file for details.
Source code is [available on GitHub](https://github.com/posita/dyce).

## Installation

Installation can be performed via [PyPI](https://pypi.python.org/pypi/dyce/):

```sh
% pip install dycelib
...
```

Alternately, you can download [the source](https://github.com/posita/dyce) and run ``setup.py``:

```sh
% git clone https://github.com/posita/dyce
...
% cd dyce
% python setup.py install  # --editable '.[dev]'
...
```

### Requirements

``dyce`` requires a relatively modern version of Python:

* [cPython](https://www.python.org/) (3.7+)
* [PyPy](http://pypy.org/) (Python 3.7+ compatible)

It has the following dependencies:

* [``typing-extensions``](https://pypi.org/project/typing-extensions/)

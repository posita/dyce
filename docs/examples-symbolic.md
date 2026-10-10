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
For typing:

>>> import sympy  # type: ignore[import-untyped]
>>> import sympy.abc  # type: ignore[import-untyped]
>>> import sympy.solvers  # type: ignore[import-untyped]
>>> import sympy.solvers.inequalities  # type: ignore[import-untyped]

  -- END MONKEY PATCH -->

# Symbolic outcomes

Thanks to [`optype`](https://jorenham.github.io/optype/), `dyce` offers typing support for arbitrary number-like outcomes, including primitives from symbolic expression packages such as [SymPy](https://www.sympy.org/).

    >>> from dyce import H, P
    >>> from dyce.d import d2, d3
    >>> import sympy.abc
    >>> d2_2x = d2 + 2 * sympy.abc.x
    >>> d3_y = d3 + sympy.abc.y
    >>> P(d2_2x, d3_y).h()
    H({2*x + y + 2: 1, 2*x + y + 3: 2, 2*x + y + 4: 2, 2*x + y + 5: 1})

[![Miss you, Doris!](images/doris.png)](https://ifunny.co/picture/shnomf-nomf-hormf-hom-i-ve-gots-to-get-my-4itlmF3P8)
<!-- Original source: https://me.me/i/shnomf-nomf-hormf-hom-ive-gots-to-get-my-rib-22441186 -->

!!! note

    Be aware that, depending on implementation, performance can suffer quite a bit when using symbolic primitives, especially with large histograms or pools.

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

In practice, that means that certain operations won’t work with symbolic expressions where correctness depends on ordering outcomes according to relative value (e.g., dice selection from pools).

Flattening pools (e.g., via [`P.h`][dyce.P.h]) works.

    >>> d2_x = d2 * sympy.abc.x
    >>> d2_x
    H({2*x: 1, x: 1})
    >>> p = P(d2_x / 3, (d2_x + 1) / 3, (d2_x + 2) / 3)
    >>> p
    P(H({2*x/3 + 1/3: 1, x/3 + 1/3: 1}), H({2*x/3 + 2/3: 1, x/3 + 2/3: 1}), H({2*x/3: 1, x/3: 1}))
    >>> p.h()
    H({2*x + 1: 1, 4*x/3 + 1: 3, 5*x/3 + 1: 3, x + 1: 1})

Enumerating rolls works.

    >>> list(p.rolls_with_counts())
    [((2*x/3, 2*x/3 + 1/3, 2*x/3 + 2/3), 1), ((2*x/3 + 1/3, 2*x/3 + 2/3, x/3), 1), ((2*x/3, 2*x/3 + 2/3, x/3 + 1/3), 1), ..., ((2*x/3, x/3 + 1/3, x/3 + 2/3), 1), ((x/3, x/3 + 1/3, x/3 + 2/3), 1)]

[`P.sample`][dyce.P.sample] works.

<!-- BEGIN MONKEY PATCH --
For deterministic outcomes.

>>> import random
>>> from dyce import rng
>>> rng.RNG = random.Random(1776137574)

  -- END MONKEY PATCH -->

    >>> p.sample()
    (2*x/3, 2*x/3 + 2/3, x/3 + 1/3)

Selection (e.g., via [`P.at`][dyce.P.at]) “works” (i.e., falls back to natural ordering of outcomes), but that is a deliberate compromise of convenience.

    >>> p.at(0)
    H({2*x/3: 4, 2*x/3 + 1/3: 2, 2*x/3 + 2/3: 1, x/3: 1})

[`P.apply_to_each_h`][dyce.P.apply_to_each_h] can help pave the way back to concrete outcomes.

    >>> f = lambda outcome: outcome.subs({sympy.abc.x: sympy.Rational(1, 3)})
    >>> p.apply_to_each_h(f)
    P(H({1/9: 1, 2/9: 1}), H({4/9: 1, 5/9: 1}), H({7/9: 1, 8/9: 1}))

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

# Symbolic outcomes

Thanks to ~~[`numerary`](https://pypi.org/project/numerary/)~~ *[`optype`](https://jorenham.github.io/optype/)*, `dyce` offers typing support for arbitrary number-like outcomes, including primitives from symbolic expression packages such as [SymPy](https://www.sympy.org/).

    >>> from dyce import H, P
    >>> import sympy.abc
    >>> d6x = H(6) + sympy.abc.x
    >>> d8y = H(8) + sympy.abc.y
    >>> P(d6x, d8y, d6x).h()
    H({2*x + y + 3: 1, 2*x + y + 4: 3, 2*x + y + 5: 6, ..., 2*x + y + 18: 6, 2*x + y + 19: 3, 2*x + y + 20: 1})

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

SymPy does not even attempt simple relative comparisons between symbolic expressions, even where they are unambiguously resolvable.
Instead, it relies on the caller to invoke its proprietary solver APIs.

    >>> bool(sympy.abc.x < sympy.abc.x + 1)
    Traceback (most recent call last):
      ...
    TypeError: cannot determine truth value of Relational...
    >>> import sympy.solvers.inequalities
    >>> sympy.solvers.inequalities.reduce_inequalities(  # zuban: ignore[no-untyped-call]
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

    >>> p.at(0)
    H({2*x/3: 9, 2*x/3 + 1/3: 6, 2*x/3 + 2/3: 4, x: 4, x + 1/3: 2, x + 2/3: 1, x/3: 1})

Selecting all dice works, since it’s equivalent to flattening (no sorting is required).

    >>> p.at(slice(None))
    H({2*x + 1: 7, 3*x + 1: 1, 4*x/3 + 1: 3, 5*x/3 + 1: 6, 7*x/3 + 1: 6, 8*x/3 + 1: 3, x + 1: 1})

Enumerating rolls works.

    >>> list(p.rolls_with_counts())
    [((2*x/3, 2*x/3 + 1/3, 2*x/3 + 2/3), 1), ((2*x/3 + 1/3, 2*x/3 + 2/3, x), 1), ((2*x/3, 2*x/3 + 2/3, x + 1/3), 1), ..., ((2*x/3, x/3 + 1/3, x/3 + 2/3), 1), ((x, x/3 + 1/3, x/3 + 2/3), 1), ((x/3, x/3 + 1/3, x/3 + 2/3), 1)]

[`P.sample`][dyce.P.sample] “works” (i.e., falls back to natural ordering of outcomes), but that is a deliberate compromise of convenience.

<!-- BEGIN MONKEY PATCH --
For deterministic outcomes.

>>> import random
>>> from dyce import rng
>>> rng.RNG = random.Random(1776137574)

  -- END MONKEY PATCH -->

    >>> p.sample()
    (2*x/3, 2*x/3 + 2/3, x + 1/3)

[`P.apply_to_each_h`][dyce.P.apply_to_each_h] can help pave the way back to concrete outcomes.

    >>> f = lambda outcome: outcome.subs({sympy.abc.x: sympy.Rational(1, 3)})
    >>> p.apply_to_each_h(f)
    P(H({1/9: 1, 2/9: 1, 1/3: 1}), H({4/9: 1, 5/9: 1, 2/3: 1}), H({7/9: 1, 8/9: 1, 1: 1}))
    >>> p.apply_to_each_h(f).at(-1)
    H({7/9: 9, 8/9: 9, 1: 9})

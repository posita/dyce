<!---
  Copyright and other protections apply. Please see the accompanying LICENSE file for
  rights and restrictions governing use of this software. All rights not expressly
  waived or licensed are reserved. If that file is missing or appears to be modified
  from its original, then please contact the author before viewing or using this
  software in any capacity.

  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you!
-->

# ``dyce`` release notes

## [0.6.2](https://github.com/posita/dyce/releases/tag/v0.6.2)

* Adds the [``H.draw``][dyce.h.H.draw] convenience method for treating a histogram as a deck rather than a die.

## [0.6.1](https://github.com/posita/dyce/releases/tag/v0.6.1)

* Fixes [``P.total``][dyce.p.P.total] to return ``#!python 1`` for empty pools, consistent with the empty product.
  (See [this explanation](https://www.johndcook.com/blog/2015/04/14/empty-sum-product/)).
* Renames ``#!python dyce.evaluation._LimitT`` to ``#!python dyce.evaluation.LimitT``.
* Fixes issues pertaining to histograms with zero totals after allowing outcomes with zero counts in non-normalized [``H`` objects][dyce.h.H].
* Fixes issue that would lead to incorrect results when making certain arbitrary selections with heterogeneous pools (e.g., with [``P.rolls_with_counts``][dyce.p.P.rolls_with_counts]).

## [0.6.0](https://github.com/posita/dyce/releases/tag/v0.6.0)

* Now requires ``numerary~=0.4.3``.
* Adds the [``expandable`` decorator][dyce.evaluation.expandable] as well as the [``foreach``][dyce.evaluation.foreach] and [``explode``][dyce.evaluation.explode] convenience functions.
* Deprecates [``P.foreach``][dyce.p.P.foreach], [``H.foreach``][dyce.h.H.foreach], and [``H.substitute``][dyce.h.H.substitute].
* Allows outcomes with zero counts in non-normalized [``H`` objects][dyce.h.H].
  Outcomes with zero counts are dropped when calling [``H.lowest_terms``][dyce.h.H.lowest_terms].
  Adds the [``H.zero_fill``][dyce.h.H.zero_fill] convenience method.
* Fixes memoization in [Risus multi-round combat translation](translations.md#modeling-entire-multi-round-combats).
* Migrates from [``setuptools_scm``](https://pypi.org/project/setuptools-scm/) to [``versioningit``](https://pypi.org/project/versioningit/) for more flexible version number formatting.
* Allows deployments to PyPI from CI based on tags.
* Uses JupyterLite instead of Binder for examples.
* Refactors [``P.is_homogeneous`` property][dyce.p.P.is_homogeneous] into a similarly-named method and adds the [``P.total`` method][dyce.p.P.total] property.
* Removes ``H.order_stat_func_for_n`` and instead caches order stat functions for ``n`` inside [``H.order_stat_for_n_at_pos``][dyce.h.H.order_stat_for_n_at_pos].

## [0.5.2](https://github.com/posita/dyce/releases/tag/v0.5.2)

* Updates binder links that fix requirements ranges.

## [0.5.1](https://github.com/posita/dyce/releases/tag/v0.5.1)

* Fixes broken binder links in docs.
* Adds the ``precision_limit`` argument to [``H.substitute``][dyce.h.H.substitute] and [``H.explode``][dyce.h.H.explode].

## [0.5.0](https://github.com/posita/dyce/releases/tag/v0.5.0)

* Breaks ``dyce.viz`` out into [``anydyce``](https://github.com/posita/anydyce/).
* Removes use of ``#!python numerary.types.…SCU`` types.
* Adds the [``H.foreach``][dyce.h.H.foreach] and [``P.foreach``][dyce.p.P.foreach] class methods.
* Migrates ``#!python resolve_dependent_probability`` to the [``H.foreach``][dyce.h.H.foreach] class method.

## [0.4.5](https://github.com/posita/dyce/releases/tag/v0.4.5)

* Fixes [this bullshit](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981/87) (no, really, I’m serious this time).
* Adds [``FilterRoller``][dyce.r.FilterRoller].
* Adds [``SubstitutionRoller``][dyce.r.SubstitutionRoller].

## [0.4.4](https://github.com/posita/dyce/releases/tag/v0.4.4)

* Removes ``…_gh.png`` hack now that [this dumpster fire](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981) is at least partially resolved.
* Refines Tension Pool example.
* Adds *Ironsworn* example.
* Removes faulty (correctly-derived, but misapplied) math in Risus “Evens Up” example.
* Adds detail around dependent probabilities.
* Adds experimental ``dyce.h.resolve_dependent_probability`` function.

## [0.4.3](https://github.com/posita/dyce/releases/tag/v0.4.3)

* Removes dependencies on deprecated ``#!python numerary.types.…SCT`` tuples
* Adds [Angry GM Tension Pool mechanic](https://theangrygm.com/definitive-tension-pool/) translation.

## [0.4.2](https://github.com/posita/dyce/releases/tag/v0.4.2)

* Removes calls to ``#!python os.get_terminal_size`` to retain utility in environments without terminals.
  Fixes [#5](https://github.com/posita/dyce/issues/5).
  Thanks [@sudo-simon!](https://github.com/sudo-simon)!

## [0.4.1](https://github.com/posita/dyce/releases/tag/v0.4.1)

* Splits out protocol checking into its own fancy library: [``numerary``](https://github.com/posita/numerary/)!
* Is now [available on PyPI as ``dyce``_](https://pypi.org/project/dyce/), thanks to the generosity of [David Eyk](https://eykd.net/about/)!
* Introduces experimental generic [``walk``][dyce.r.walk] function and supporting visitor data structures.
* Uses ``#!python pygraphviz`` to automate class diagram generation.
  (See the note on special considerations for regenerating class diagrams in the [hacking quick start](contrib.md#hacking-quick-start).)
* Introduces experimental use of ``#!python numpy`` for RNG, if present.
* Migrates to using ``pyproject.toml`` and ``setup.cfg``.
* Adds missing [``py.typed`` to ensure clients get type checking](https://www.python.org/dev/peps/pep-0561/).
  (Whoops.)

## [0.4.0](https://github.com/posita/dyce/releases/tag/v0.4.0)

### Breaking changes

!!! warning

    The following changes are not backward compatible.
    Please review before upgrading.

* Renames ``#!python HAbleT`` and ``#!python HAbleOpsMixin`` to [``HableT``][dyce.h.HableT] and  [``HableOpsMixin``][dyce.h.HableOpsMixin].
    Uses alternate spellings.
* Removes deprecated non-flattening unary operation methods ``#!python P.__neg__`` and ``#!python P.__pos__``.
    Uses, e.g., ``#!python P.umap(operator.__neg__)`` or ``#!python P(-h for h in p)`` instead.
* Removes deprecated synonym methods ``#!python H.even`` and ``#!python H.odd``.
    Uses [``H.is_even``][dyce.h.H.is_even] and [``H.is_odd``][dyce.h.H.is_odd] instead.
* Removes deprecated synonym package ``#!python dyce.plt``.
    Uses ``dyce.viz`` instead.
* Removes special case handling of ``#!python H({})`` for addition and subtraction.
    Check for code that relied on, e.g., ``#!python h + H({})`` resolving to ``#!python h``.
    It is probably not correct.
    If the behavior is desired, consider eliminating empty histograms before performing calculations.
    E.G., ``#!python h1 + h2 if h2 else h1``.

    See also the [``sum_h`` function][dyce.h.sum_h], which ensures the result is always a histogram:

    ``` python
    >>> from dyce.h import sum_h
    >>> sum(())
    0
    >>> sum_h(())
    H({})

    ```

    Note, however, that sums including empty histograms will be always result in empty histograms:

    ``` python
    >>> from dyce import H
    >>> hs = (H(6), H(6), H(6), H({}))
    >>> sum_h(hs)
    H({})

    ```

    If a different result was desired, adapting our advice from above would yield something like:

    ``` python
    >>> sum_h(h for h in hs if h)
    H({3: 1, 4: 3, 5: 6, 6: 10, ..., 16: 6, 17: 3, 18: 1})

    ```

### Other changes

* Documentation overhaul including augmented examples and reorganized images and JavaScript.
* Fixes ``#!python H({}).format()`` bug.
* Adds [``beartype``](https://github.com/beartype/beartype) runtime type checking.
* *Maintains* support for Python 3.7 (for now).

## [0.3.2](https://github.com/posita/dyce/releases/tag/v0.3.2)

* Emergency release to ~~cover up~~ _address_ [this ~~embarrassment~~ _typo_](https://github.com/borntyping/python-dice/issues/16#issuecomment-900249398). 😬😅

## [0.3.1](https://github.com/posita/dyce/releases/tag/v0.3.1)

* Adds these release notes.
* Boosts ``#!python isinstance`` performance with ``#!python dyce``’s proprietary numeric ``#!python Protocol``s.
* Reinstates support for Python 3.7 ~~(for now)~~.
* Adds [``H.is_even``][dyce.h.H.is_even] and [``H.is_odd``][dyce.h.H.is_odd].
* Deprecates synonym methods ``#!python H.even`` and ``#!python H.odd``.
* Introduces experimental [``H.total``][dyce.h.H.total] property.
* Removes incorrectly non-flattening unary operation methods ``#!python P.__abs__`` and ``#!python P.__invert__``.
* Deprecates non-flattening unary operation methods ``#!python P.__neg__`` and ``#!python P.__pos__``.
* Renames experimental ``#!python P.homogeneous`` property to [``P.is_homogeneous``][dyce.p.P.is_homogeneous].
* Introduces experimental [``R``][dyce.r.R] and [``Roll``][dyce.r.Roll] primitives.
* Removes ``#!python coerce`` parameter from [``H.map``][dyce.h.H.map], [``H.rmap``][dyce.h.H.rmap], and [``H.umap``][dyce.h.H.umap].
* Renames ``#!python dyce.plt`` to ``dyce.viz``.
* Deprecates synonym package ``#!python dyce.plt``.

## [0.3.0](https://github.com/posita/dyce/releases/tag/v0.3.0)

``dyce`` goes beta!
Non-experimental features should be considered stable.

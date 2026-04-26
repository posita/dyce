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

# `dyce` release notes

## [0.7.0](https://github.com/posita/dyce/releases/tag/v0.7.0)

!!! warning "Breaking changes"

    Some of the following changes are not backward compatible.
    Please review before upgrading.

- Drops support for 3.9 and 3.10 and extends support to 3.14
- Fixes embarrassingly long-running logical error in 4d6 variants example
- Removes `dyce.r` altogether (pending rewrite of an alternative).
- Adds `#!python H.from_counts` class method constructs an [`H`][dyce.H] from multiple sources.
- Removes `#!python H.map`, `#!python H.rmap`, and `#!python H.umap` in favor of [`H.apply`][dyce.H.apply].
- Removes `#!python H.is_even` and `#!python H.is_odd`, whose functionality can be trivially reintroduced using [`H.apply`][dyce.H.apply].
- Removes `#!python H.__reversed__`.
- Removes `#!python H.vs` and `#!python H.within`.
- Renames `#!python H.accumulate` to [`H.merge`][dyce.H.merge].
- Renames `#!python H.distribution` to [`H.probability_items`][dyce.H.probability_items] and removes `#!python H.distribution_xy`.
- Removes `#!python P.map`, `#!python P.rmap`, and `#!python P.umap` in favor of [`P.apply`][dyce.P.apply].
- Removes `P.is_homogeneous`.
- Adds experimental and somewhat inefficient [`H.replace`][dyce.H.replace] method.
- Simplifies and consolidates `#!python dyce.evaluation.expandable` and `#!python dyce.evaluation.foreach` into [`expand`][dyce.expand] (still experimental).
- Renames `#!python explode` to [`explode_n`][dyce.explode_n] to be more explicit about the exit criteria.
- Moves [`HableOpsMixin`][dyce.HableOpsMixin] to its own module.
- *(Finally!)* removes deprecated interfaces
    - `#!python H.explode`
    - `#!python H.foreach`
    - `#!python H.substitute`
    - `#!python P.foreach`
    - `#!python dyce.h.coalesce_replace`
    - `#!python dyce.h.resolve_dependent_probability`
    - `#!python dyce.h.sum_h` (not previously deprecated, but to-date unused)
- Modernizes use of [beartype](https://github.com/beartype/beartype/) with [pytest-beartype](https://github.com/beartype/pytest-beartype)
- Completely eliminates dependency on [`numerary`](https://github.com/beartype/numerary/) (which was flawed since conception), and instead relies on [`optype`](https://jorenham.github.io/optype/) for mathematical operator typing.
  ([`H`][dyce.H] and [`P`][dyce.P] still largely assume that outcome types won’t be mixed, but doing so will still probably work in most contexts, so FAAFO.)
- Stabilizes Jupyter Lite installation
- Defaults to collapsed installation cells in notebooks
- Modernizes `setup.cfg` -> `pyproject.toml` (and `tox.ini`)
- Updates CI workflow
- Who let the dogs out? *We* let dogs out.
  - Migrates to `ruff` for linting

## [0.6.2](https://github.com/posita/dyce/releases/tag/v0.6.2)

- Adds the `H.draw` convenience method for treating a histogram as a deck rather than a die.

## [0.6.1](https://github.com/posita/dyce/releases/tag/v0.6.1)

- Fixes [`P.total`][dyce.P.total] to return `#!python 1` for empty pools, consistent with the empty product.
  (See [this explanation](https://www.johndcook.com/blog/2015/04/14/empty-sum-product/)).
- Renames `#!python dyce.evaluation._LimitT` to `#!python dyce.evaluation.LimitT`.
- Fixes issues pertaining to histograms with zero totals after allowing outcomes with zero counts in non-normalized [`H` objects][dyce.H].
- Fixes issue that would lead to incorrect results when making certain arbitrary selections with heterogeneous pools (e.g., with [`P.rolls_with_counts`][dyce.P.rolls_with_counts]).

## [0.6.0](https://github.com/posita/dyce/releases/tag/v0.6.0)

- Now requires `numerary~=0.4.3`.
- Adds the `expandable` decorator as well as the `foreach` and `explode` convenience functions.
- Deprecates `#!python P.foreach`, `#!python H.foreach`, and `#!python H.substitute`.
- Allows outcomes with zero counts in non-normalized [`H` objects][dyce.H].
  Outcomes with zero counts are dropped when calling [`H.lowest_terms`][dyce.H.lowest_terms].
  Adds the [`H.zero_fill`][dyce.H.zero_fill] convenience method.
- Fixes memoization in [Risus multi-round combat translation](translations.md#modeling-entire-multi-round-combats).
- Migrates from [`setuptools_scm`](https://pypi.org/project/setuptools-scm/) to [`versioningit`](https://pypi.org/project/versioningit/) for more flexible version number formatting.
- Allows deployments to PyPI from CI based on tags.
- Uses JupyterLite instead of Binder for examples.
- Refactors `P.is_homogeneous` property into a similarly-named method and adds the [`P.total` method][dyce.P.total] property.
- Removes `#!python H.order_stat_func_for_n` and instead caches order stat functions for `#!python n` inside [`H.order_stat_for_n_at_pos`][dyce.H.order_stat_for_n_at_pos].

## [0.5.2](https://github.com/posita/dyce/releases/tag/v0.5.2)

- Updates binder links that fix requirements ranges.

## [0.5.1](https://github.com/posita/dyce/releases/tag/v0.5.1)

- Fixes broken binder links in docs.
- Adds the `#!python precision_limit` argument to `#!python H.substitute` and `#!python H.explode`.

## [0.5.0](https://github.com/posita/dyce/releases/tag/v0.5.0)

- Breaks `#!python dyce.viz` out into [`anydyce`](https://github.com/posita/anydyce/).
- Removes use of `#!python numerary.types.…SCU` types.
- Adds the `#!python H.foreach` and `#!python P.foreach` class methods.
- Migrates `#!python resolve_dependent_probability` to the `#!python H.foreach` class method.

## [0.4.5](https://github.com/posita/dyce/releases/tag/v0.4.5)

- Fixes [this bullshit](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981/87) (no, really, I’m serious this time).
- Adds `dyce.r.FilterRoller`.
- Adds `dyce.r.SubstitutionRoller`.

## [0.4.4](https://github.com/posita/dyce/releases/tag/v0.4.4)

- Removes `…_gh.png` hack now that [this dumpster fire](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981) is at least partially resolved.
- Refines Tension Pool example.
- Adds *Ironsworn* example.
- Removes faulty (correctly-derived, but misapplied) math in Risus “Evens Up” example.
- Adds detail around dependent probabilities.
- Adds experimental `#!python dyce.h.resolve_dependent_probability` function.

## [0.4.3](https://github.com/posita/dyce/releases/tag/v0.4.3)

- Removes dependencies on deprecated `#!python numerary.types.…SCT` tuples
- Adds [Angry GM Tension Pool mechanic](https://theangrygm.com/definitive-tension-pool/) translation.

## [0.4.2](https://github.com/posita/dyce/releases/tag/v0.4.2)

- Removes calls to `#!python os.get_terminal_size` to retain utility in environments without terminals.
  Fixes [#5](https://github.com/posita/dyce/issues/5).
  Thanks [@sudo-simon!](https://github.com/sudo-simon)!

## [0.4.1](https://github.com/posita/dyce/releases/tag/v0.4.1)

- Splits out protocol checking into its own fancy library: [`numerary`](https://github.com/beartype/numerary/)!
- Is now [available on PyPI as `dyce`_](https://pypi.org/project/dyce/), thanks to the generosity of [David Eyk](https://eykd.net/about/)!
- Introduces experimental generic `dyce.r.walk` function and supporting visitor data structures.
- Uses `#!python pygraphviz` to automate class diagram generation.
  (See the note on special considerations for regenerating class diagrams in the [hacking quick start](contrib.md#hacking-quick-start).)
- Introduces experimental use of `#!python numpy` for RNG, if present.
- Migrates to using `pyproject.toml` and `setup.cfg`.
- Adds missing [`py.typed` to ensure clients get type checking](https://www.python.org/dev/peps/pep-0561/).
  (Whoops.)

## [0.4.0](https://github.com/posita/dyce/releases/tag/v0.4.0)

!!! warning "Breaking changes"

    The following changes are not backward compatible.
    Please review before upgrading.

- Renames `#!python HAbleT` and `#!python HAbleOpsMixin` to [`HableT`][dyce.HableT] and [`HableOpsMixin`][dyce.HableOpsMixin].
    Uses alternate spellings.
- Removes deprecated non-flattening unary operation methods `#!python P.__neg__` and `#!python P.__pos__`.
    Uses, e.g., `#!python P.umap(operator.__neg__)` or `#!python P(-h for h in p)` instead.
- Removes deprecated synonym methods `#!python H.even` and `#!python H.odd`.
    Uses `#!python H.is_even` and `#!python H.is_odd` instead.
- Removes deprecated synonym package `#!python dyce.plt`.
    Uses `#!python dyce.viz` instead.
- Removes special case handling of `#!python H({})` for addition and subtraction.
    Check for code that relied on, e.g., `#!python h + H({})` resolving to `#!python h`.
    It is probably not correct.
    If the behavior is desired, consider eliminating empty histograms before performing calculations.
    E.G., `#!python h1 + h2 if h2 else h1`.

    See also the ~~`sum_h` function~~, which ensures the result is always a histogram:

        >>> from dyce.h import sum_h  # doctest: +SKIP
        >>> sum(())
        0
        >>> sum_h(())  # doctest: +SKIP
        H({})

    Note, however, that sums including empty histograms will be always result in empty histograms:

        >>> from dyce import H
        >>> hs = [H(6), H(6), H(6), H({})]
        >>> sum_h(hs)  # doctest: +SKIP
        H({})

    If a different result was desired, adapting our advice from above would yield something like:

        >>> sum_h(h for h in hs if h)  # doctest: +SKIP
        H({3: 1, 4: 3, 5: 6, 6: 10, ..., 16: 6, 17: 3, 18: 1})

### Other changes

- Documentation overhaul including augmented examples and reorganized images and JavaScript.
- Fixes `#!python H({}).format(width=65)` bug.
- Adds [`beartype`](https://github.com/beartype/beartype) runtime type checking.
- *Maintains* support for Python 3.7 (for now).

## [0.3.2](https://github.com/posita/dyce/releases/tag/v0.3.2)

- Emergency release to ~~cover up~~ *address* [this ~~embarrassment~~ *typo*](https://github.com/borntyping/python-dice/issues/16#issuecomment-900249398). 😬😅

## [0.3.1](https://github.com/posita/dyce/releases/tag/v0.3.1)

- Adds these release notes.
- Boosts `#!python isinstance` performance with `#!python dyce`’s proprietary numeric `#!python Protocol`s.
- Reinstates support for Python 3.7 ~~(for now)~~.
- Adds `#!python H.is_even` and `#!python H.is_odd`.
- Deprecates synonym methods `#!python H.even` and `#!python H.odd`.
- Introduces experimental [`H.total`][dyce.H.total] property.
- Removes incorrectly non-flattening unary operation methods `#!python P.__abs__` and `#!python P.__invert__`.
- Deprecates non-flattening unary operation methods `#!python P.__neg__` and `#!python P.__pos__`.
- Renames experimental `#!python P.homogeneous` property to `P.is_homogeneous`.
- Introduces experimental `dyce.r.R` and `dyce.r.Roll` primitives.
- Removes `#!python coerce` parameter from `#!python H.map`, `#!python H.rmap`, and `#!python H.umap`.
- Renames `#!python dyce.plt` to `#!python dyce.viz`.
- Deprecates synonym package `#!python dyce.plt`.

## [0.3.0](https://github.com/posita/dyce/releases/tag/v0.3.0)

`dyce` goes beta!
Non-experimental features should be considered stable.

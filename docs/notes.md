<!--- -*- encoding: utf-8 -*-
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

## [0.4.1](https://github.com/posita/dyce/releases/tag/v0.4.1)

* Introduces experimental generic [``walk``][dyce.r.walk] function and supporting visitor data structures.
* Use ``pygraphviz`` to automate class diagram generation.
  (See the note on special considerations for regenerating class diagrams in the [hacking quick start](contrib.md#hacking-quick-start).)

## [0.4.0](https://github.com/posita/dyce/releases/tag/v0.4.0)

### Breaking changes

!!! warning

    The following changes are not backward compatible.
    Please review before upgrading.

* Renames ``HAbleT`` and ``HAbleOpsMixin`` to [``HableT``][dyce.h.HableT] and  [``HableOpsMixin``][dyce.h.HableOpsMixin].
    Use alternate spellings.
* Removes deprecated non-flattening unary operation methods ``P.__neg__`` and ``P.__pos__``.
    Use, e.g., ``#!python P.umap(operator.__neg__)`` or ``#!python P(-h for h in p)`` instead.
* Removes deprecated synonym methods ``H.even`` and ``H.odd``.
    Use  [``H.is_even``][dyce.h.H.is_even] and [``H.is_odd``][dyce.h.H.is_odd] instead.
* Removes deprecated synonym package ``dyce.plt``.
    Use [``dyce.viz``][dyce.viz] instead.
* Removes special case handling of ``H({})`` for addition and subtraction.
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
* Fixes ``H({}).format()`` bug.
* Adds [``beartype``](https://github.com/beartype/beartype) runtime type checking.
* *Maintains* support for Python 3.7 (for now).

## [0.3.2](https://github.com/posita/dyce/releases/tag/v0.3.2)

* Emergency release to ~~cover up~~ _address_ [this ~~embarrassment~~ _typo_](https://github.com/borntyping/python-dice/issues/16#issuecomment-900249398). 😬😅

## [0.3.1](https://github.com/posita/dyce/releases/tag/v0.3.1)

* Adds these release notes.
* Boosts ``#!python isinstance`` performance with ``#!python dyce``’s proprietary numeric ``#!python Protocol``s.
* Reinstates support for Python 3.7 ~~(for now)~~.
* Adds [``H.is_even``][dyce.h.H.is_even] and [``H.is_odd``][dyce.h.H.is_odd].
* Deprecates synonym methods ``H.even`` and ``H.odd``.
* Introduces experimental [``H.total``][dyce.h.H.total] property.
* Removes incorrectly non-flattening unary operation methods ``#!python P.__abs__`` and ``#!python P.__invert__``.
* Deprecates non-flattening unary operation methods ``#!python P.__neg__`` and ``#!python P.__pos__``.
* Renames experimental ``#!python P.homogeneous`` property to [``P.is_homogeneous``][dyce.p.P.is_homogeneous].
* Introduces experimental [``R``][dyce.r.R] and [``Roll``][dyce.r.Roll] primitives.
* Removes ``#!python coerce`` parameter from [``H.map``][dyce.h.H.map], [``H.rmap``][dyce.h.H.rmap], and [``H.umap``][dyce.h.H.umap].
* Renames ``#!python dyce.plt`` to [``dyce.viz``][dyce.viz].
* Deprecates synonym package ``#!python dyce.plt``.

## [0.3.0](https://github.com/posita/dyce/releases/tag/v0.3.0)

``dyce`` goes beta!
Non-experimental features should be considered stable.

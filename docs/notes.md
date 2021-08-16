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

## 0.3.3 (pending)

* Documentation overhaul including augmented examples and reorganized images and JavaScript.
* Fixed ``H({}).format()`` bug.

## [0.3.2](https://github.com/posita/dyce/releases/tag/v0.3.2)

* Emergency release to ~~cover up~~ _address_ [this ~~embarrassment~~ _typo_](https://github.com/borntyping/python-dice/issues/16#issuecomment-900249398). 😬😅

## [0.3.1](https://github.com/posita/dyce/releases/tag/v0.3.1)

* Adds these release notes.
* Boosts ``#!python isinstance`` performance with ``#!python dyce``’s proprietary numeric ``#!python Protocol``s.
* Reinstates support for Python 3.7 (for now).
* Adds [``H.is_even``][dyce.h.H.is_even] and [``H.is_odd``][dyce.h.H.is_odd].
* Deprecates synonym methods [``H.even``][dyce.h.H.even] and [``H.odd``][dyce.h.H.odd].
* Introduces experimental [``H.total``][dyce.h.H.total] property.
* Removes incorrectly non-flattening unary operation methods ``#!python P.__abs__`` and ``#!python P.__invert__``.
* Deprecates non-flattening unary operation methods [``P.__neg__``][dyce.p.P.__neg__] and [``P.__pos__``][dyce.p.P.__pos__].
* Renames experimental ``#!python P.homogeneous`` property to [``P.is_homogeneous``][dyce.p.P.is_homogeneous].
* Introduces experimental [``R``][dyce.r.R] and [``Roll``][dyce.r.Roll] primitives.
* Removes ``#!python coerce`` parameter from [``H.map``][dyce.h.H.map], [``H.rmap``][dyce.h.H.rmap], and [``H.umap``][dyce.h.H.umap].
* Renames ``#!python dyce.plt`` to [``dyce.viz``][dyce.viz].
* Deprecates synonym package ``#!python dyce.plt``.

## [0.3.0](https://github.com/posita/dyce/releases/tag/v0.3.0)

``dyce`` goes beta!
Non-experimental features should be considered stable.

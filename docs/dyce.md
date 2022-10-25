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

# ``#!python dyce`` package reference

``#!python dyce`` revolves around two core primitives.
[``H`` objects][dyce.h.H] are histograms (outcomes or individual dice).
[``P`` objects][dyce.p.P] are collections of histograms (pools).

Additionally, the [``dyce.evaluation``](dyce.evaluation.md) package provides the [``expandable`` decorator][dyce.evaluation.expandable], which is useful for substitutions, explosions, and modeling arbitrarily complex computations with dependent terms.
It also provides [``foreach``][dyce.evaluation.foreach] and [``explode``][dyce.evaluation.explode] as convenient shorthands.
The [``dyce.r``](dyce.r.md) package provides scalars, histograms, pools, operators, etc. for assembling reusable roller trees.

::: dyce.h.H
    options:
      show_root_heading: true

::: dyce.p.P
    options:
      show_root_heading: true

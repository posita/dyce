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

# ``dyce`` package reference

::: dyce
    selection:
      members: false

``dyce`` provides two key primitives:

* [``H``][dyce.lib.H] for histograms (individual dice or outcomes)
* [``D``][dyce.lib.D] for collections of histograms (dice sets)

::: dyce.lib.H
    rendering:
      show_root_full_path: false
      show_root_heading: true
    selection:
      filters:
        - "!^OperatorLT$"
        - "!^OperatorRT$"

::: dyce.lib.D
    rendering:
      show_root_full_path: false
      show_root_heading: true
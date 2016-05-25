<!--- -*- encoding: utf-8; grammar-ext: md; mode: markdown -*-
  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
  >>>>>>>>>>>>>>>> IMPORTANT: READ THIS BEFORE EDITING! <<<<<<<<<<<<<<<<
  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you! -->

Copyright © 2015-2016 [Matt Bogosian](mailto:mtb19@columbia.edu?Subject=_skel) ([**@posita**](https://github.com/posita)).

Please see the accompanying [`LICENSE`](LICENSE) (or [`LICENSE.txt`](LICENSE)) file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If such a file did not accompany this software, then please contact the author before viewing or using this software in any capacity.

- [ ] `git checkout -b X.Y.Z-release`

- [ ] Set version in [`_skel/version.py`](_skel/version.py)

```diff
diff --git a/_skel/version.py b/_skel/version.py
index 0123456..fedcba9 100644
--- a/_skel/version.py
+++ b/_skel/version.py
@@ -25,5 +25,5 @@ from __future__ import (

 __all__ = ()

-__version__ = ( 'master', )
-__release__ = 'master'
+__version__ = ( X, Y, Z )
+__release__ = 'vX.Y.Z'
```

- [ ] Set version in [`README.rst`](README.rst) (`master` → `vX.Y.Z`; [`https://pypi.python.org/pypi/_skel`](https://pypi.python.org/pypi/_skel) → [`https://pypi.python.org/pypi/_skel/X.Y.Z`](https://pypi.python.org/pypi/_skel/X.Y.Z);  [`https://img.shields.io/pypi/.../_skel.svg`](https://img.shields.io/pypi/.../_skel.svg) →  [`https://img.shields.io/pypi/.../_skel/X.Y.Z.svg`](https://img.shields.io/pypi/.../_skel/X.Y.Z.svg))

- [ ] `git commit --all --message 'Update version and release vX.Y.Z.'`

- [ ] `git tag --sign --force --message 'Release vX.Y.Z.' vX.Y.Z`

- [ ] `git push --tags`

- [ ] `./setup.py sdist upload`

- [ ] Upload `_skel.egg-info/PKG-INFO` to [`https://pypi.python.org/pypi?:action=submit_form&name=_skel&version=X.Y.Z`](https://pypi.python.org/pypi?:action=submit_form&name=_skel&version=X.Y.Z) (work-around)

- [ ] `git checkout master`

- [ ] `git branch --delete X.Y.Z-release`

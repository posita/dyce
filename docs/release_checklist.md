<!--- -*- encoding: utf-8 -*-
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!!
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Please keep each sentence on its own unwrapped line.
  It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
  Thank you! -->

Copyright and other protections apply.
Please see the accompanying [`LICENSE`](../LICENSE) file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its originals, then please contact the author before viewing or using this software in any capacity.

The following assumes you are working from the repository root and have a development environment similar to one created by `pip install install --editable '.[dev]'`. (See, e.g., [`./helpers/venvsetup.sh`](../helpers/venvsetup.sh).)

- [ ] If necessary, update copyright in [`LICENSE`](../LICENSE) and [`docs/conf.py`](../docs/conf.py)

- [ ] [`./helpers/release.sh`](../helpers/release.sh)

- [ ] `git push --tags`

- [ ] `python3.x setup.py bdist_wheel sdist`

- [ ] `twine upload dist/*`

- [ ] `git checkout master`

- [ ] `git branch --delete X.Y.Z-release`

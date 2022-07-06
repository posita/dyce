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

The following assumes you are working from the repository root and have a development environment similar to one created by ``pip install install --editable '.[dev]' && python -m pre_commit install``.

* [ ] Update docs and commit
  * Solidify current release start section for next release in [release notes](../docs/notes.md)
  * If necessary, update copyright in [``LICENSE``](../LICENSE)

* [ ] ``git clean -Xdf [-n] [...]``

* [ ] ``"$( git rev-parse --show-toplevel )/helpers/propagate-version.sh" "$( python -m versioningit --next-version . )"``

* [ ] ``git add -u && git commit --edit --message "$( printf 'Release v%s\n\n<TODO: Copy [release notes](docs/notes.md) here. Hope you were keeping track!>' "$( python -m versioningit --next-version . )" )"``

* [ ] ``git tag [--force] --sign "v$( python -m versioningit --next-version . )" && git tag --force latest``

* [ ] ``"$( git rev-parse --show-toplevel )/.tox/check/bin/mike" serve`` and spot check docs (links to external references might be missing)

* [ ] ``git push --force origin "$( git describe --abbrev=0 )" latest``

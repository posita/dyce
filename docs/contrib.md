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

# Contributing to `dyce`

There are several ways you can contribute.

## Filing issues

You can [file new issues](https://github.com/posita/dyce/issues) as you find them.
Please avoid duplicating issues.
[“Writing Effective Bug Reports” by Elisabeth Hendrickson](http://testobsessed.com/wp-content/uploads/2011/07/webr.pdf) (PDF) may be helpful.

## Submission guidelines

If you are willing and able, consider [submitting a pull request](https://github.com/posita/dyce/pulls) (PR) with a fix.
There are only a few guidelines:

* If it is not already present, please add your name (and optionally your email, GitHub username, website address, or other contact information) to the [`LICENSE`](license.md) file:

```md
...
* [Matt Bogosian](mailto:matt@bogosian.net?Subject=dyce); GitHub - [**@posita**](https://github.com/posita)
...
```

* Use [Black](https://pypi.org/project/black/) to format your changes.
  Try to follow the source conventions as you observe them.

* Provide tests where feasible and appropriate.
  At the very least, existing tests should not fail.
  (There are exceptions, but if there is any doubt, they probably do not apply.)
  Unit tests live in `./tests` and can be run with [Tox](https://tox.readthedocs.org/) or [pytest](https://docs.pytest.org/).
  A helper script is provided for setting up an isolated development environment.
  For example:

```sh
[PYTHON=/path/to/python] ./helpers/venvsetup.sh
tox [TOX_ARGS... [-- PYTEST_ARGS...]]
pytest [PYTEST_ARGS...]
```

* If you need me, mention me ([**@posita**](https://github.com/posita)) in your comment, and describe specifically how I can help.

* If you want feedback on a work-in-progress (WIP), create a PR and prefix its title with something like, “`NEED FEEDBACK - `”.

* If your PR is still in progress, but you are not blocked on anything, prefix the title with something like, “`WIP - `”.

* Once you are ready for a merge, resolve any merge conflicts, squash your commits, and provide a useful commit message.
  ([This](https://robots.thoughtbot.com/git-interactive-rebase-squash-amend-rewriting-history) and [this](http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html) may be helpful.)
  Then prefix the PR’s title to something like, “`READY FOR MERGE - `”.
  I will try to get to it as soon as I can.

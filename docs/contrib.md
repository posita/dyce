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

# Contributing to ``dyce``

There are many ways you can contribute.
You have only but to try.

## Filing issues

You can [file new issues](https://github.com/posita/dyce/issues) as you find them.
Please try to avoid duplicating issues.
[“Writing Effective Bug Reports” by Elisabeth Hendrickson](http://testobsessed.com/wp-content/uploads/2011/07/webr.pdf) (PDF) may be helpful.

<!--
## Posting on StackExchange

If you’re so inclined, feel free to post on StackExchange (e.g., in [RPG](https://rpg.stackexchange.com/) or [Math](https://math.stackexchange.com/)), and tag the question with ``dyce``.
Feel free to at-mention ``@posita`` as well.
-->

## Hacking quick-start

A [helper script](https://github.com/posita/dyce/blob/latest/helpers/venvsetup.sh) is provided for bootstrapping an isolated development environment.

```sh
% [PYTHON=…/path/to/python] helpers/venvsetup.sh
…
% . .venv/bin/activate
```

The helper script is really only there to help folks get their feet wet who don’t already manage their own virtual environments.
The above is essentially equivalent to the following (with some additional checking).

```sh
% …/path/to/python -m virtualenv .venv || …/path/to/python -m venv .venv
…
% .venv/bin/pip install --upgrade --editable '.[dev]'
…
% . .venv/bin/activate
```

The ``[dev]`` variant includes additional dependencies necessary for development and testing.
See the ``extras_require`` parameter in [``setup.py``](https://github.com/posita/dyce/blob/latest/setup.py).

Unit tests are run with [Tox](https://tox.readthedocs.org/) (but can also be run with [pytest](https://docs.pytest.org/) directly, if installed).

```sh
% cd …/path/to/dyce
% . .venv/bin/activate
% tox [TOX_ARGS... [-- PYTEST_ARGS...]]
…
% pytest [PYTEST_ARGS...]
…
```

A bare bones example:

```sh
% git clone https://github.com/posita/dyce.git  # or your fork
% cd dyce
% helpers/venvsetup.sh && . .venv/bin/activate
…
% tox
…
```

A [``virtualenvwrapper``](https://pypi.org/project/virtualenvwrapper/)-based alternative:

```sh
% git clone https://github.com/posita/dyce.git  # or your fork
% mkvirtualenv [--python=…/path/to/python] -a "${PWD}/dyce" dycelib
…
% pip install --upgrade --editable '.[dev]'
…
% tox
…
```

## Submission guidelines

If you are willing and able, consider [submitting a pull request](https://github.com/posita/dyce/pulls) with a fix.
See [the docs](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) if you’re not already familiar with pull requests.
``dyce`` releases from [``master``](https://github.com/posita/dyce/tree/master) (although not always immediately), so a lot of [these workflows](http://scottchacon.com/2011/08/31/github-flow.html#how-we-do-it) are helpful.
There are only a few additional guidelines:

* If it is not already present, please add your name (and optionally your email, GitHub username, website address, or other contact information) to the [``LICENSE``](license.md) file.

```md
...
* [Matt Bogosian](mailto:matt@bogosian.net?Subject=dyce); GitHub – [**@posita**](https://github.com/posita)
...
```

* Use [Black](https://pypi.org/project/black/) to format your changes.
  Do your best to follow the source conventions as you observe them.
  If it’s important to you, Existing comments are wrapped at 88 characters per line to match Black’s default.
  (Don’t spend too much effort on strict conformance, though.
  I can clean things up later if they really bother me.)

* Provide tests where feasible and appropriate.
  At the very least, existing tests should not fail.
  (There are exceptions, but if there is any doubt, they probably do not apply.)
  Unit tests live in [``tests``](https://github.com/posita/dyce/tree/latest/tests).

* If you want feedback on a work-in-progress, consider [“mentioning” me](https://github.blog/2011-03-23-mention-somebody-they-re-notified/) ([**@posita**](https://github.com/posita)), and describe specifically how I can help.
  Consider prefixing your pull request’s title with something like, “``NEED FEEDBACK – ``”.

* If your pull request is still in progress, but you are not blocked on anything, consider using the [draft feature](https://github.blog/2019-02-14-introducing-draft-pull-requests/).

* Once you are ready for a merge, resolve any conflicts, squash your commits, and provide a useful commit message.
  ([This](https://robots.thoughtbot.com/git-interactive-rebase-squash-amend-rewriting-history) and [this](http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html) may be helpful.)
  If your pull request started out as a draft, promote it by requesting a review.
  Consider prefixing the pull request’s title to something like, “``READY FOR MERGE – ``”.
  I will try to get to it as soon as I can.

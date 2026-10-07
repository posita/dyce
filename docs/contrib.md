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

# Contributing to `dyce`

You can help by [filing new issues](https://github.com/posita/dyce/issues).
Please try to avoid duplicates.
For beefs, rants, ideas, recipes, etc., consider starting or joining a [discussion](https://github.com/posita/dyce/discussions).

## Hacking quick-start

```sh
# Basic setup
git clone https://github.com/posita/dyce.git
cd dyce
uv venv --clear --prompt "$( basename "${PWD}" )" --relocatable
uv sync
uv run pre-commit install

# Run tests with coverage using the current environment
uv run pytest --cov

# Run tests across configured Python versions
uv run tox

# Run linters, type checkers, and other validators via pre-commit
uv run pre-commit run --all-files --hook-stage pre-push
```

Alternative using `pip`:

```sh
# Basic setup
git clone https://github.com/posita/dyce.git
cd dyce
python3 -m venv --prompt dyce .venv
. .venv/bin/activate
pip install --requirements requirements-dev.txt
pre-commit install

# Run tests with coverage using the current environment
pytest --cov

# Run tests across configured Python versions
tox

# Run linters, type checkers, and other validators via pre-commit
pre-commit run --all-files --hook-stage pre-push
```

## Submission guidelines

Consider submitting a [pull request](https://github.com/posita/dyce/pulls) with a fix, if you have one.
***Required:*** If it is not already present, please add your name (and optionally your email, GitHub username, website address, or other contact information) to the [`LICENSE`](license.md) file to assent to the inclusion of your contribution.
If you want feedback on a work-in-progress, consider [“mentioning” me](https://github.blog/2011-03-23-mention-somebody-they-re-notified/) ([**@posita**](https://github.com/posita)), and describe specifically how I can help.

Provide tests where feasible and appropriate.
Unit tests live in [`tests`](https://github.com/posita/dyce/tree/main/tests).
At the very least, existing tests should not fail.

If at all possible, please author commit messages and PR descriptions yourself.
LLM-produced prose tends to lack concision, clarity, and character.

# `dyce` development guidance

`dyce` is a typed Python library for finite discrete probability computation.
It supports CPython 3.11–3.14 and PyPy 3.11.
Versions come from Git tags through `setuptools-scm`; do not edit a version file.

The code is authoritative when this guidance becomes stale.
Update this file when durable project structure, tooling, or conventions change.

## Working safely

Treat the live working tree as authoritative.
Before editing an existing file, inspect its current working-tree, staged, and `HEAD` versions, then record and immediately recheck a content hash.
If it changed, re-read it and preserve the newer work.
After editing, inspect the diff and limit it to the requested regions.
Do not stage changes unless the user asks.

Generated documentation files can change during `make -C docs-src`.
Edit their source scripts rather than generated output, and verify hashes around generation when another process may be touching the tree.

## Layout

- `dyce/` is the package and ships `py.typed`.
- `dyce/h.py` defines `H`, the histogram and finite-distribution primitive.
- `dyce/p.py` defines `P`, homogeneous and heterogeneous dice pools.
- `dyce/evaluation.py` provides dependent evaluation, including `expand`.
- `dyce/viz/` contains shared graph types plus separate `matplotlib` and portable `plotly` backends.
  `dyce.viz.plotly` produces plain Plotly specifications and does not require Plotly at runtime.
- `tests/` mirrors the package; visualization tests are under `tests/viz/`.
- `docs/` contains site pages, published images, generated notebooks, and release notes.
- `docs-src/` contains documentation generators and snippets used during site builds.

Avoid exhaustive module inventories here.
Use the package tree, `README.md`, and `docs/` for current detail.

## Common commands

```bash
uv sync --group dev
uv run pytest
uv run pytest --cov --cov-report=term-missing
uv run tox -e py313
uv run pre-commit run --all-files --hook-stage pre-push
uv run make -C docs-src
uv run zensical build --strict
uv run zensical serve --strict
```

The pre-push hooks run Ruff, doctest normalization checks, and all four static type checkers: mypy, pyright, ty, and zuban.
Do not validate a typing change with only one checker.
Tox adds runtime checking with beartype and covers the supported Python matrix.
The PyPy environment intentionally avoids Matplotlib.

Pytest discovers doctests from package docstrings, `README.md`, and Markdown under `docs/`.

`docs-src/Makefile` builds the wheel and assembles JupyterLite and pinned wheels into `docs/`.
Run it before building or serving the site.
Review it before changing documentation packaging.

## Python and documentation conventions

- Do not add `from __future__ import annotations`.
  Quote forward references only when necessary.
- Public docstrings use Markdown, raw triple-quoted strings, and one sentence per source line.
- Use mkdocstrings cross-references such as ``[`H`][dyce.H]`` for public intra-library references.
- Use `` `expression` `` and `` `#!math expression` `` for inline code and math.
- Comments should explain architecture, component boundaries, or genuinely counterintuitive code.
  Prefer descriptive names over commentary that restates the implementation.
- Use American spelling except for the project-wide `cancelled` and `cancelling` forms.
- In prose use curly quotation marks and apostrophes.
  In code, comments, and verbatim spans use ASCII quotes.
- Type-ignore comments have no space before `[`, and multiple error codes are alphabetized.
  All four type checkers must pass.
  Suppressions needed by one checker but reported as unused by another are acceptable only when all four checkers pass.
- Forward and reflected operator methods follow this order: `add`, `sub`, `mul`, `truediv`, `floordiv`, `mod`, `pow`, `matmul`, `lshift`, `rshift`, `and`, `or`, `xor`; then `neg`, `pos`, `abs`, `invert`.
  Top-level helper functions are alphabetized.

### Write plainly

Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away.

Use Orwell's tests: know what you mean; choose concrete words; cut needless words; prefer active voice when the actor matters; and avoid stale metaphors and inflated jargon. Prefer minimalism and a conversational tone that prioritizes clarity over complex syntax. Employ short, direct sentences and plain language to make complex themes accessible to a broad audience. Do not use metaphor or metaphorical professional jargon in technical writing. It must be precise, consistent, and unambiguous. Do not use metaphor, jargon, or multiple terms to refer to the same concept. It only confuses readers.

Complete thoughts should be separated by periods and a single space. Colons, em-dashes, and semicolons should be used sparingly. For example, semicolons may be used to separate items in a complicated list, usually preceded by a colon (see, e.g., Orwell's tests above). Em-dashes can be used to signal the occasional aside or parenthetical, but parentheses are preferred. If the aside is relevant in context, consider instead restructuring to improve clarity or simplicity. If it is not relevant, omit it. Occasional, brief asides that providing an appropriate jab or comic relief to a frustrating or complicated topic can remain in place, but they should be very rare exceptions and always subject to approval.

Avoid empty openings, recaps, motivational language, marketing adjectives, and conclusions that add no information. Do not shorten text by deleting a necessary fact or qualifier.

Use ASD-STE100 Simplified Technical English, Issue 9 (January 2025), as the writing standard for new or changed technical prose. This requirement applies to documentation, runbooks, handoff material, architecture text, migration plans, pull request text, review comments, issue comments, and code comments.

## Project mechanisms

- Use `dyce.lifecycle.experimental` for experimental APIs.
- Use `typing_extensions.deprecated` before Python 3.13 and `warnings.deprecated` on Python 3.13 and later.
- `_griffe_ext.py` adds lifecycle admonitions to generated API documentation.
- `helpers/check-doctests.py` checks and normalizes doctest blocks.
- Optional Matplotlib support is the `viz-mpl` extra.

GitHub Actions references are pinned to full commit SHAs with matching version comments.
Update both together.
Releases are made by pushing a PEP 440-compatible `v*` tag; publishing and versioned documentation are handled by GitHub Actions.

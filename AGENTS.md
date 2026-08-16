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

Generated documentation assets can change during `make -C docs`.
Edit their source scripts rather than generated SVG or HTML files, and verify hashes around generation when another process may be touching the tree.

## Layout

- `dyce/` is the package and ships `py.typed`.
- `dyce/h.py` defines `H`, the histogram and finite-distribution primitive.
- `dyce/p.py` defines `P`, homogeneous and heterogeneous dice pools.
- `dyce/evaluation.py` provides dependent evaluation, including `expand`.
- `dyce/viz/` contains shared graph types plus separate `matplotlib` and portable `plotly` backends.
  `dyce.viz.plotly` produces plain Plotly specifications and does not require Plotly at runtime.
- `tests/` mirrors the package; visualization tests are under `tests/viz/`.
- `docs/` contains MkDocs sources, generated examples, and release notes.

Avoid exhaustive module inventories here.
Use the package tree, `README.md`, and `docs/` for current detail.

## Common commands

```bash
uv sync --group dev
uv run pytest
uv run pytest --cov --cov-report=term-missing
uv run tox -e py313
uv run pre-commit run --all-files --hook-stage pre-push
uv run mkdocs build
make -C docs
```

The pre-push hooks run Ruff, doctest normalization checks, and all four static type checkers: mypy, Pyrefly, Pyright, and ty.
Do not validate a typing change with only one checker.
Tox adds runtime checking with beartype and covers the supported Python matrix.
The PyPy environment intentionally avoids Matplotlib.

Pytest discovers doctests from package docstrings, `README.md`, and Markdown under `docs/`.

## Python conventions

- Do not add `from __future__ import annotations`.
  Quote forward references only when necessary.
- Public docstrings use Markdown, raw triple-quoted strings, and one sentence per source line.
- Use mkdocstrings cross-references such as ``[`H`][dyce.H]`` for public intra-library references.
- Use `` `#!python expression` `` and `` `#!math expression` `` for inline code and math.
- Comments should explain architecture, component boundaries, or genuinely counterintuitive code.
  Prefer descriptive names over commentary that restates the implementation.
- Use American spelling except for the project-wide `cancelled` and `cancelling` forms.
- In prose use curly quotation marks and apostrophes.
  In code, comments, and verbatim spans use ASCII quotes.
- Type-ignore comments have no space before `[`, and multiple error codes are alphabetized.
  Suppressions needed by one checker but reported as unused by another are acceptable only when all four checkers pass.
- Forward and reflected operator methods follow this order: `add`, `sub`, `mul`, `truediv`, `floordiv`, `mod`, `pow`, `matmul`, `lshift`, `rshift`, `and`, `or`, `xor`; then `neg`, `pos`, `abs`, `invert`.
  Top-level helper functions are alphabetized.

Write direct prose.
Prefer periods to semicolons or dashes used as asides.
Avoid “+” as shorthand for “and” and avoid stock AI metaphors or throat-clearing.

## Project mechanisms

- Use `dyce.lifecycle.experimental` for experimental APIs.
- Use `typing_extensions.deprecated` before Python 3.13 and `warnings.deprecated` on Python 3.13 and later.
- `_griffe_ext.py` adds lifecycle admonitions to generated API documentation.
- `helpers/check-doctests.py` checks and normalizes doctest blocks.
- Optional Matplotlib support is the `viz-mpl` extra.

GitHub Actions references are pinned to full commit SHAs with matching version comments.
Update both together.
Releases are made by pushing a PEP 440-compatible `v*` tag; publishing and versioned documentation are handled by GitHub Actions.

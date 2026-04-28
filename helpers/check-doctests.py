#!/usr/bin/env python3
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

r"""Synthesize type-checkable files from doctests and run type checkers, or reformat doctest examples in place.

Run "check --help" or "format --help" for subcommand-specific usage.
"""

import argparse
import ast
import atexit
import doctest
import inspect
import logging
import operator
import os
import re
import shutil
import signal
import subprocess  # noqa: S404
import sys
import tempfile
import tomllib
from collections.abc import Callable, Iterable, Iterator, Mapping
from functools import partial
from pathlib import Path
from types import FrameType
from typing import Any

_LOGGER = logging.getLogger(__name__)
_DEFAULT_SUFFIXES: frozenset[str] = frozenset({".md", ".py", ".pyi"})

# ---- Synthesis -----------------------------------------------------------------------


def _leading_blank_lines(s: str) -> int:
    r"""Return the number of leading blank lines in *s*."""
    count = 0
    for line in s.split("\n"):
        if line.strip():
            break
        count += 1
    return count


def _iter_doctests(text: str, filepath: Path) -> Iterator[tuple[int, doctest.DocTest]]:
    r"""
    Yield `(doc_offset, dt)` for every doctest block in *text*.

    First tries to locate docstrings via `ast` (text-only, no import).
    Each docstring's `doc_offset` maps `dt.examples[i].lineno` to an absolute 0-based line number in the original file.
    Falls back to passing the raw content to `DocTestParser` when `ast.parse` fails (e.g. for Markdown files), in which case `doc_offset` is always 0.
    """
    parser = doctest.DocTestParser()
    kwargs: dict[str, Any] = {
        "globs": {"__name__": filepath.stem},
        "name": filepath.stem,
        "filename": str(filepath),
        "lineno": 0,
    }
    try:
        tree = ast.parse(text, filename=str(filepath))
        _LOGGER.debug("%s: parsed via ast", filepath)
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue
            if not node.body:
                continue
            first = node.body[0]
            if not (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                continue
            const = first.value
            # const.lineno is 1-based; subtract 1 for 0-based, then add the number of
            # leading blank lines that inspect.cleandoc will strip, so that doc_offset
            # points at the first non-blank content line in the file.
            doc_offset = const.lineno - 1 + _leading_blank_lines(str(const.value))
            yield (
                doc_offset,
                parser.get_doctest(string=inspect.cleandoc(str(const.value)), **kwargs),
            )
    except SyntaxError:
        _LOGGER.debug("%s: ast parse failed, falling back to text mode", filepath)
        yield 0, parser.get_doctest(string=text, **kwargs)


def _synthesize_filepath(filepath: Path) -> str:
    r"""
    Return a buffer whose doctest code lines occupy their original positions.

    All other lines are blank. The result ends with exactly one `os.linesep`.
    """
    try:
        text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        _LOGGER.warning("skipping %s: %s", filepath, exc)
        return ""
    out = [""] * len(text.splitlines())
    if out:
        # Try to sneak in helpful directives
        out[0] = "# pyright: reportUnusedExpression=false"
    for doc_offset, dt in _iter_doctests(text, filepath):
        for ex in dt.examples:
            if doctest.SKIP in ex.options:
                continue
            for i, line in enumerate(ex.source.splitlines()):
                out[doc_offset + ex.lineno + i] = line
    return os.linesep.join(out) + os.linesep


def _synthesize_filepaths(tmp_dir: Path, filepaths: Iterable[Path]) -> dict[Path, Path]:
    path_map: dict[Path, Path] = {}  # tmp_path -> orig_path
    seen_flat: dict[str, Path] = {}  # flat_name -> first orig_path (collisions)

    for filepath in filepaths:
        flat = _flat_name(filepath)
        if flat in seen_flat:
            _LOGGER.warning(
                "name collision: %s and %s both map to %s; skipping %s",
                seen_flat[flat],
                filepath,
                flat,
                filepath,
            )
            continue
        seen_flat[flat] = filepath
        tmp_path = tmp_dir / flat
        try:
            content = _synthesize_filepath(filepath)
        except OSError as exc:
            _LOGGER.warning("skipping %s: %s", filepath, exc)
            continue
        tmp_path.write_text(content)
        path_map[tmp_path] = filepath
        _LOGGER.debug("wrote %s", tmp_path)

    return path_map


def _run_checkers(
    checker_commands: Iterable[list[str]],
    path_map: Mapping[Path, Path],
    *,
    fail_fast: bool,
) -> int:
    tmp_files = list(path_map)

    exit_code = 0

    for checker_cmd in checker_commands:
        cmd = checker_cmd + [str(p) for p in tmp_files]
        _LOGGER.info("%s", " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: PLW1510, S603
        except FileNotFoundError:
            _LOGGER.error("checker not found: %s", checker_cmd[0])  # noqa: TRY400
            if fail_fast:
                return 1
            exit_code |= 1
            continue

        for stream in (result.stdout, result.stderr):
            if not stream:
                continue
            remapped = stream
            for tmp_path, orig_path in path_map.items():
                remapped = re.sub(
                    rf"{re.escape(str(tmp_path))}\b",
                    str(orig_path),
                    remapped,
                )
            sys.stdout.write(remapped)

        if result.returncode != 0:
            if fail_fast:
                return result.returncode
            exit_code |= result.returncode

    return exit_code


# ── formatting ────────────────────────────────────────────────────────────────


def _ruff_format(source: str) -> str | None:
    r"""
    Format *source* through `ruff format`.

    Returns the formatted source, or `None` if ruff failed or the source is unchanged.
    """
    normalized = source if source.endswith("\n") else source + "\n"
    result = subprocess.run(  # noqa: PLW1510
        ["ruff", "format", "--quiet", "-"],  # noqa: S607
        input=normalized,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    formatted = result.stdout
    return None if formatted == normalized else formatted


def _make_prefixed_lines(source: str, indent: int) -> list[str] | None:
    r"""
    Convert formatted Python *source* to doctest-prefixed lines.

    Applies *indent* spaces before each `>>>` or `...` prompt.
    Returns `None` if the formatted source contains blank lines between top-level statements, which would silently split the example into multiple interactions.
    """
    lines = source.splitlines()
    if not lines:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    # Blank lines between top-level statements would split the doctest example
    if len(tree.body) > 1:
        for i in range(len(tree.body) - 1):
            gap_start = tree.body[i].end_lineno  # 1-based, inclusive
            gap_end = tree.body[i + 1].lineno - 1  # 1-based, inclusive
            for line in lines[gap_start:gap_end]:  # 0-based slice
                if not line.strip():
                    return None
    stmt_starts: set[int] = {node.lineno for node in tree.body}  # 1-based
    pad = " " * indent
    result = []
    for i, line in enumerate(lines, 1):
        if i in stmt_starts:
            result.append(f"{pad}>>> {line}" if line.strip() else f"{pad}>>>")
        else:
            result.append(f"{pad}... {line}" if line.strip() else f"{pad}...")
    return result


def _format_filepath(filepath: Path) -> bool:
    r"""
    Format doctest examples in *filepath* in place.

    Skips `.py` and `.pyi` files.
    Relies on `ruff format` for those, which handles docstring line-length adjustments natively via `docstring-code-line-length`.
    Returns `True` if the file was modified.
    """
    if filepath.suffix in {".py", ".pyi"}:
        _LOGGER.debug(
            "skipping %s: use ruff format for Python doctest formatting", filepath
        )
        return False
    try:
        text = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _LOGGER.warning("skipping %s: %s", filepath, exc)
        return False

    examples: list[tuple[int, doctest.Example]] = [
        (doc_offset + ex.lineno, ex)
        for doc_offset, dt in _iter_doctests(text, filepath)
        for ex in dt.examples
    ]

    if not examples:
        return False

    file_lines = text.splitlines()

    # Collect (start, end, new_lines) replacements. Apply bottom-to-top so earlier line
    # numbers are not invalidated by changes to later ones
    replacements: list[tuple[int, int, list[str]]] = []
    for abs_lineno, ex in examples:
        formatted = _ruff_format(ex.source)
        if formatted is None:
            continue
        # ex.indent is unreliable for Python files: inspect.cleandoc strips indentation
        # before DocTestParser runs, so ex.indent is always 0 in that path. Derive the
        # actual indentation from the original file line instead.
        actual_indent = len(file_lines[abs_lineno]) - len(
            file_lines[abs_lineno].lstrip()
        )
        new_lines = _make_prefixed_lines(formatted, actual_indent)
        if new_lines is None:
            _LOGGER.warning(
                "%s:%d: skipping example: reformatted source would split the doctest block",
                filepath,
                abs_lineno + 1,
            )
            continue
        orig_count = len(ex.source.splitlines())
        replacements.append((abs_lineno, abs_lineno + orig_count, new_lines))

    if not replacements:
        return False

    replacements.sort(key=operator.itemgetter(0), reverse=True)
    for start, end, new_lines in replacements:
        file_lines[start:end] = new_lines

    new_text = "\n".join(file_lines) + ("\n" if text.endswith("\n") else "")
    if new_text == text:
        return False
    filepath.write_text(new_text, encoding="utf-8")
    return True


def _format_filepaths(filepaths: Iterable[Path]) -> bool:
    r"""Format doctest examples across all *filepaths*, logging a summary."""
    changed: list[Path] = [
        filepath for filepath in filepaths if _format_filepath(filepath)
    ]

    if changed:
        for p in changed:
            _LOGGER.info("reformatted %s", p)
        _LOGGER.warning("%d file(s) reformatted", len(changed))
        return True
    else:
        _LOGGER.warning("no files reformatted")
        return False


# ── temp-directory management ─────────────────────────────────────────────────

_tmp_dir: Path | None = None


def _flat_name(filepath: Path) -> str:
    r"""
    Derive a flat filename for *filepath* suitable for a shared temp directory.

    Leading dots and path separators are stripped, remaining separators are replaced with `__`, and the extension is forced to `.py` so that type checkers will analyse the file.
    """
    s = str(filepath).lstrip("." + os.sep)
    s = s.replace(os.sep, "__").replace("/", "__").replace(".", "_")
    return str(Path(s).with_suffix(".py"))


def _cleanup_tmp_dir(*, tmp_dir: Path) -> None:
    if tmp_dir is not None and tmp_dir.exists():
        _LOGGER.debug("removing temp directory %s", tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _signal_handler(
    sig: int, _frame: FrameType | None, *, cleanup_tmp_dir: Callable[[], None]
) -> None:
    cleanup_tmp_dir()
    sys.exit(128 + sig)


# ── config ────────────────────────────────────────────────────────────────────

_SUBCOMMANDS = frozenset({"check", "format"})
_TOML_SHARED_STR_KEYS = frozenset({"log_level"})
_TOML_SHARED_STR_LIST_KEYS = frozenset({"paths", "suffixes"})
_TOML_CHECK_BOOL_KEYS = frozenset({"fail_fast", "keep"})


def _load_toml_config(  # noqa: C901
    subcommand: str | None,
) -> tuple[dict[str, object], dict[str, object]]:
    r"""
    Find and return `[tool.check_doctests]` from the nearest `pyproject.toml`.

    Walks up from the current directory.
    Returns `({}, {})` if no file is found or the section is absent.
    Unknown or malformed keys are warned about and ignored.
    The first element of the tuple contains shared keys (`paths`, `suffixes`, `log_level`); the second contains subcommand-specific keys (e.g. `checkers`, `fail_fast`, `keep` for `check`).
    """
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / "pyproject.toml"
        if not candidate.exists():
            continue
        try:
            with candidate.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            _LOGGER.warning("could not read %s: %s", candidate, exc)
            return {}, {}
        raw: object = data.get("tool", {}).get("check_doctests", {})
        if not isinstance(raw, dict):
            _LOGGER.warning("%s: [tool.check_doctests] is not a table", candidate)
            return {}, {}
        _LOGGER.debug("loaded config from %s", candidate)

        # Parse shared keys (skip subcommand sub-tables).
        shared: dict[str, object] = {}
        for key, val in raw.items():
            if key in _SUBCOMMANDS:
                continue  # sub-table; handled below
            elif key in _TOML_SHARED_STR_KEYS:
                if isinstance(val, str):
                    shared[key] = val
                else:
                    _LOGGER.warning("%s: %s must be a string; ignoring", candidate, key)
            elif key in _TOML_SHARED_STR_LIST_KEYS:
                if isinstance(val, list) and all(isinstance(s, str) for s in val):
                    shared[key] = val
                else:
                    _LOGGER.warning(
                        "%s: %s must be a list of strings; ignoring", candidate, key
                    )
            else:
                _LOGGER.warning("%s: unknown key %r; ignoring", candidate, key)

        # Parse subcommand-specific keys.
        sub: dict[str, object] = {}
        if subcommand in _SUBCOMMANDS:
            raw_sub = raw.get(subcommand, {})
            if not isinstance(raw_sub, dict):
                _LOGGER.warning(
                    "%s: [tool.check_doctests.%s] is not a table",
                    candidate,
                    subcommand,
                )
            else:
                for key, val in raw_sub.items():
                    if subcommand == "check":
                        if key == "checkers":
                            if isinstance(val, list) and all(
                                isinstance(cmd, list)
                                and all(isinstance(t, str) for t in cmd)
                                for cmd in val
                            ):
                                sub[key] = val
                            else:
                                _LOGGER.warning(
                                    "%s: checkers must be a list of string lists; ignoring",
                                    candidate,
                                )
                        elif key in _TOML_CHECK_BOOL_KEYS:
                            if isinstance(val, bool):
                                sub[key] = val
                            else:
                                _LOGGER.warning(
                                    "%s: %s must be a boolean; ignoring",
                                    candidate,
                                    key,
                                )
                        else:
                            _LOGGER.warning(
                                "%s: unknown key %r in [tool.check_doctests.check]; ignoring",
                                candidate,
                                key,
                            )
                    else:
                        _LOGGER.warning(
                            "%s: unknown key %r in [tool.check_doctests.format]; ignoring",
                            candidate,
                            key,
                        )

        return shared, sub
    return {}, {}


# ── argument parsing ──────────────────────────────────────────────────────────


def _split_argv(
    argv: list[str],
) -> tuple[list[str], list[list[str]]]:
    r"""
    Split *argv* on `--` boundaries.

    Returns `(pre_args, checker_commands)` where *pre_args* is everything before the first `--` (passed to argparse) and *checker_commands* is a list of token lists, one per checker, split on subsequent `--` tokens.

    This pre-processing is necessary because argparse swallows `--` in versions prior to 3.12 (see <https://github.com/python/cpython/issues/81691>).
    """
    try:
        sep_idx = argv.index("--")
    except ValueError:
        return argv, []

    pre = argv[:sep_idx]
    rest = argv[sep_idx + 1 :]

    checker_commands: list[list[str]] = []
    current: list[str] = []
    for arg in rest:
        if arg == "--":
            if current:
                checker_commands.append(current)
            current = []
        else:
            current.append(arg)
    if current:
        checker_commands.append(current)

    return pre, checker_commands


def _build_parser() -> tuple[
    argparse.ArgumentParser, dict[str, argparse.ArgumentParser]
]:
    prog = Path(sys.argv[0]).name

    # Shared arguments inherited by both subcommands via parents=.
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Source files or directories to process. "
        "When scanning a directory, only files whose suffix matches --suffixes are included; "
        "explicitly named files are never filtered. "
        "Defaults to all git-tracked files under the repository root when omitted.",
    )
    shared.add_argument(
        "--suffixes",
        nargs="+",
        default=None,
        metavar="EXT",
        help="File suffixes to include when scanning directories. "
        f"Defaults to {' '.join(sorted(_DEFAULT_SUFFIXES))} if not set here or in pyproject.toml.",
    )
    shared.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        metavar="LEVEL",
        help="Logging verbosity. "
        "One of DEBUG, INFO, WARNING, ERROR, CRITICAL (default: WARNING).",
    )

    # Main parser.
    p = argparse.ArgumentParser(
        prog=prog,
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subs = p.add_subparsers(dest="subcommand", required=True)

    # check subparser.
    check_p = subs.add_parser(
        "check",
        parents=[shared],
        help="synthesize temp files from doctests and run type checkers",
        description=(
            "Synthesize each file's doctest code blocks into a temporary buffer\n"
            "preserving original line numbers, then run type checkers on the result.\n"
            "Type checker errors reference the original file and line without remapping.\n"
            "\n"
            "Each file is first parsed with ast to locate docstrings precisely.\n"
            "Non-Python files such as Markdown fall back to DocTestParser on the raw\n"
            "content.\n"
            "\n"
            "Type checker commands follow -- after the regular arguments and are\n"
            "separated from each other by additional -- tokens:\n"
            "\n"
            "  check [options] [paths] -- checker [args] [-- checker [args] ...]\n"
            "\n"
            "Each command receives the synthesized temp files as trailing arguments.\n"
            "If no checker is given on the command line, the checkers list from\n"
            "[tool.check_doctests.check] in the nearest pyproject.toml is used.\n"
            "The built-in fallback is mypy.\n"
        ),
        epilog=(
            "Examples:\n"
            "  check dyce/h.py dyce/types.py -- ty check -- mypy\n"
            "  check dyce/ docs/ --no-fail-fast\n"
            "  check -- pyright\n"
            "\n"
            "pyproject.toml defaults (all keys optional):\n"
            "\n"
            "  [tool.check_doctests]\n"
            '  paths     = ["app", "docs", "tests"]\n'
            '  suffixes  = [".md", ".py", ".pyi"]\n'
            '  log_level = "WARNING"\n'
            "\n"
            "  [tool.check_doctests.check]\n"
            '  checkers  = [["ty", "check"], ["mypy"]]\n'
            "  fail_fast = false\n"
            "  keep      = false\n"
            "\n"
            "CLI options take precedence over pyproject.toml, which takes precedence\n"
            "over the built-in defaults.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check_p.add_argument(
        "--keep",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Keep the temporary directory after completion, logging its path at WARNING. "
        "--no-keep (the default) removes it automatically on exit.",
    )
    check_p.add_argument(
        "--fail-fast",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit with the first failing checker's return code (default). "
        "--no-fail-fast runs all checkers regardless and ORs their return codes.",
    )

    # format subparser.
    format_p = subs.add_parser(
        "format",
        parents=[shared],
        help="reformat doctest examples in place using ruff (skips .py/.pyi files)",
        description=(
            "Reformat >>> doctest examples in place using ruff format.\n"
            "\n"
            "Skips .py and .pyi files; use ruff format directly for those, which\n"
            "handles docstring code line length natively via docstring-code-line-length."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    return p, {"check": check_p, "format": format_p}


def _enum_src_files(paths: Iterable[Path], suffixes: frozenset[str]) -> list[Path]:
    dirs: list[Path] = []
    files: list[Path] = []
    if paths:
        for path in paths:
            if path.is_dir():
                dirs.append(path)
            else:
                # Explicitly named files are never filtered by suffix
                files.append(path)
    else:
        result = subprocess.run(  # noqa: PLW1510
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            _LOGGER.error("git rev-parse failed: %s", result.stderr.strip())
            dirs.append(Path.cwd())
        else:
            dirs.append(Path(result.stdout.strip()))

    if dirs:
        result = subprocess.run(  # noqa: PLW1510, S603
            [  # noqa: S607
                "git",
                "ls-files",
                "--cached",
                "--modified",
                "--other",
                "--exclude-standard",
                *(str(p) for p in dirs),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            _LOGGER.error("git ls-files failed: %s", result.stderr.strip())
        else:
            discovered = [
                Path(p)
                for p in sorted(set(result.stdout.splitlines()))
                if p and Path(p).suffix in suffixes
            ]
            _LOGGER.debug(
                "found %d file(s) via git ls-files (filtered to %s)",
                len(discovered),
                ", ".join(sorted(suffixes)),
            )
            files.extend(discovered)

    files.sort()

    return files


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> int:  # noqa: C901
    pre_argv, checker_commands = _split_argv(sys.argv[1:])
    exit_code = 0

    # Peek at subcommand before parsing so we can load the right toml section
    subcommand = pre_argv[0] if pre_argv and pre_argv[0] in _SUBCOMMANDS else None

    # Load pyproject.toml config. CLI args override these via set_defaults below.
    shared_config, sub_config = _load_toml_config(subcommand)

    parser, subparsers = _build_parser()

    # Apply shared toml defaults to all subparsers. (Paths needs Path conversion.)
    shared_defaults: dict[str, object] = {}
    for k, v in shared_config.items():
        if k == "paths":
            assert isinstance(v, list)  # guaranteed by _load_toml_config validation
            shared_defaults[k] = [Path(str(p)) for p in v]
        else:
            shared_defaults[k] = v
    for sub_p in subparsers.values():
        sub_p.set_defaults(**shared_defaults)

    # Apply subcommand-specific toml defaults. Pull checkers out separately.
    toml_checkers: list[list[str]] | None = None
    if subcommand in subparsers:
        sub_defaults: dict[str, object] = {}
        for k, v in sub_config.items():
            if k == "checkers":
                toml_checkers = v  # type: ignore[assignment]  # ty: ignore[invalid-assignment]
            else:
                sub_defaults[k] = v
        if sub_defaults:
            subparsers[subcommand].set_defaults(**sub_defaults)

    args = parser.parse_args(pre_argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    # Suffix precedence: CLI > pyproject.toml (already in args.suffixes via
    # set_defaults) > built-in
    suffixes = (
        frozenset(args.suffixes) if args.suffixes is not None else _DEFAULT_SUFFIXES
    )

    # Resolve input files.
    files = _enum_src_files(args.paths, suffixes)

    if args.subcommand == "format":
        if _format_filepaths(files):
            exit_code |= 1
        return exit_code

    assert args.subcommand == "check"

    # Checker precedence: CLI > pyproject.toml > built-in default
    if not checker_commands:
        if toml_checkers:
            checker_commands = toml_checkers
            _LOGGER.info("using checkers from pyproject.toml")
        else:
            checker_commands = [["mypy"]]
            _LOGGER.info("no type checker specified; defaulting to mypy")

    # Set up temp directory and cleanup handlers.
    tmp_dir = Path(tempfile.mkdtemp(prefix="check_doctests_"))
    _LOGGER.debug("temp directory: %s", tmp_dir)

    if args.keep:
        _LOGGER.warning("keeping temp directory: %s", tmp_dir)
    else:
        cleanup_tmp_dir = partial(_cleanup_tmp_dir, tmp_dir=tmp_dir)
        atexit.register(cleanup_tmp_dir)
        signal.signal(
            signal.SIGINT,
            partial(_signal_handler, cleanup_tmp_dir=cleanup_tmp_dir),
        )
        signal.signal(
            signal.SIGTERM,
            partial(_signal_handler, cleanup_tmp_dir=cleanup_tmp_dir),
        )

    # Synthesize files into the temp directory
    path_map = _synthesize_filepaths(tmp_dir, files)

    if not path_map:
        _LOGGER.warning("no files to type-check")
        return exit_code

    exit_code |= _run_checkers(checker_commands, path_map, fail_fast=args.fail_fast)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

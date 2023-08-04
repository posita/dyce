#!/usr/bin/env python
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import doctest
import logging
import os
import pathlib
import re
import shutil
import sys
import tempfile
from typing import Iterable, Iterator, Mapping, TextIO

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


PARSER = argparse.ArgumentParser(
    description="Extract doctests from PATH and check them with mypy.",
)
PARSER.add_argument(
    "-a",
    "--mypy-arg",
    metavar="ARG",
    help="append ARG to mypy command",
    action="append",
    default=[],
    dest="mypy_args",
)
PARSER.add_argument(
    "-A",
    "--clear-mypy-args",
    help="clear any mypy command arguments",
    action="store_const",
    const=[],
    dest="mypy_args",
)
# Adapted from
# <https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-exclude>
_DEFAULT_EXCLUDE_RE = r"\A(\..*|__pycache__|dist|site|.*\.egg-info)\Z"
PARSER.add_argument(
    "--exclude-dir-names",
    "--exclude",
    metavar="PATTERN",
    help=f'exclude directories matching PATTERN from inspection (default: "{_DEFAULT_EXCLUDE_RE}")',
    default=_DEFAULT_EXCLUDE_RE,
)
_DEFAULT_INCLUDE_RE = r"\.(md|py|pyi|rst|txt)\Z"
PARSER.add_argument(
    "--include-file-names",
    metavar="PATTERN",
    help=f'include files matching PATTERN (default: "{_DEFAULT_INCLUDE_RE}")',
    default=_DEFAULT_INCLUDE_RE,
)
PARSER.add_argument(
    "--log-level",
    metavar="LEVEL",
    help="set logging verbosity to LEVEL (default: WARNING)",
    choices=["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING"],
    default="WARNING",
)
PARSER.add_argument(
    "--tmp-file-suffix",
    metavar="SUFFIX",
    help='use SUFFIX when creating temporary files (default: ".doctest.py")',
    default=".doctest.py",
)
PARSER.add_argument(
    "-k",
    "--keep-tmp-files",
    help="keep temporary files on exit, e.g., for debugging or inspection (default)",
    action="store_true",
    default=False,
    dest="keep_tmp_files",
)
PARSER.add_argument(
    "-K",
    "--no-keep-tmp-files",
    help="remove temporary files on exit",
    action="store_false",
    dest="keep_tmp_files",
)
PARSER.add_argument(
    "paths",
    nargs="+",
    metavar="PATH",
)


# ---- Functions -----------------------------------------------------------------------


def copy_doctests(
    src_path: pathlib.Path,
    dst_f: TextIO,
    dp: doctest.DocTestParser = doctest.DocTestParser(),
) -> None:
    with src_path.open() as src_f:
        src_p = str(src_path.resolve())
        dt = dp.get_doctest(src_f.read(), {"__name__": "__main__"}, src_p, src_p, 0)
        cur_lineno = 0

        if not dt.examples:
            logging.debug("no doctests found in %s", src_path)

        for example in dt.examples:
            assert cur_lineno <= example.lineno

            while cur_lineno < example.lineno:
                dst_f.write(f"# skipped line {cur_lineno}\n")
                cur_lineno += 1

            dst_f.write(example.source)
            cur_lineno += sum(1 for c in example.source if c == "\n")


def copy_paths(
    parsed_args: argparse.Namespace,
    dst_dir_path: pathlib.Path,
    orig_paths: Iterable[pathlib.Path],
) -> Mapping[pathlib.Path, pathlib.Path]:
    dst_paths_to_orig_paths: dict[pathlib.Path, pathlib.Path] = {}
    cwd_path = pathlib.Path.cwd()

    for orig_path in orig_paths:
        src_path = orig_path.resolve()
        dst_path = dst_dir_path.joinpath(src_path.relative_to(cwd_path))
        dst_path = dst_path.with_name(dst_path.name + parsed_args.tmp_file_suffix)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        logging.debug("checking %s", orig_path)

        try:
            with dst_path.open("w") as dst:
                copy_doctests(src_path, dst)
        except FileNotFoundError:
            logging.warning("%s does not exist; skipping", orig_path)
            dst_path.unlink()
            continue
        except UnicodeDecodeError:
            logging.warning("unable to make sense of %s; skipping", orig_path)
            dst_path.unlink()
            continue

        if dst_path.stat().st_size == 0:
            if parsed_args.keep_tmp_files:
                logging.debug("%s had no tests", dst_path)
            else:
                logging.debug("%s had no tests, deleting", dst_path)
                dst_path.unlink()
        else:
            logging.debug("extracted tests from %s into %s", orig_path, dst_path)
            dst_paths_to_orig_paths[dst_path] = orig_path

    return dst_paths_to_orig_paths


def gather_paths(
    parsed_args: argparse.Namespace,
) -> Iterator[pathlib.Path]:
    exclude_dir_names_re = parsed_args.exclude_dir_names
    include_file_names_re = parsed_args.include_file_names

    for src_p in parsed_args.paths:
        orig_path = pathlib.Path(src_p)

        if orig_path.is_dir():
            for root_p, dir_names, file_names in os.walk(src_p, topdown=True):
                dir_names[:] = (
                    dir_name
                    for dir_name in dir_names
                    if re.search(exclude_dir_names_re, dir_name) is None
                )

                for file_name in file_names:
                    if re.search(include_file_names_re, file_name):
                        yield pathlib.Path(root_p).joinpath(file_name)
        else:
            yield orig_path


def main(*args: str) -> int:
    import mypy.api

    parsed_args = PARSER.parse_args(args) if args else PARSER.parse_args()
    logging.getLogger().setLevel(parsed_args.log_level)
    dst_dir = tempfile.mkdtemp()
    dst_dir_path = pathlib.Path(dst_dir)
    logging.debug("created temporary directory %s", dst_dir_path)
    dst_paths_to_orig_paths = copy_paths(
        parsed_args, dst_dir_path, gather_paths(parsed_args)
    )

    try:
        results = mypy.api.run(parsed_args.mypy_args + [str(dst_dir)])

        if results[0]:
            for line in results[0].rstrip("\n").split("\n"):
                if line.startswith(str(dst_dir)):
                    p, rest = line.split(":", 1)
                    path = pathlib.Path(p)
                    line = f"{str(dst_paths_to_orig_paths.get(path, path))}:{rest}"

                print(line)

        if results[1]:
            sys.stderr.write(results[1])

        return results[2]
    finally:
        if parsed_args.keep_tmp_files:
            print(f"leaving temporary files in {dst_dir_path}", file=sys.stderr)
        else:
            logging.debug("removing %s", dst_dir_path)
            shutil.rmtree(dst_dir)


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    sys.exit(main())

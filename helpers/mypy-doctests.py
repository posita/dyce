#!/usr/bin/env python

from __future__ import annotations, generator_stop

import argparse
import doctest
import logging
import os
import pathlib
import re
import shutil
import sys
import tempfile
from typing import Dict, Iterable, Iterator, Mapping, TextIO

import mypy.api

# ---- Data ----------------------------------------------------------------------------


PARSER = argparse.ArgumentParser(
    description="Extract doctests from PATH and check them with mypy.",
)
PARSER.add_argument(
    "-a",
    "--mypyp-arg",
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
PARSER.add_argument(
    "--exclude-dir-names",
    "--exclude",
    metavar="PATTERN",
    help='exclude directories matching PATTERN from inspection (default: "{}")'.format(
        r"\A(\..*|__pycache__|node_modules|site-packages)\Z"
    ),
    default=r"\A(\..*|__pycache__|node_modules|site-packages)\Z",
)
PARSER.add_argument(
    "--include-file-names",
    metavar="PATTERN",
    help='include files matching PATTERN (default: "{}")'.format(
        r"\.(md|py|pyi|rst|txt)\Z"
    ),
    default=r"\.(md|py|pyi|rst|txt)\Z",
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
    "--keep-temp-files",
    help="keep temporary files on exit, e.g., for debugging or inspection (default)",
    action="store_true",
    default=False,
    dest="keep_temp_files",
)
PARSER.add_argument(
    "-K",
    "--no-keep-temp-files",
    help="remove temporary files on exit",
    action="store_false",
    dest="keep_temp_files",
)
PARSER.add_argument(
    "paths",
    nargs="+",
    metavar="PATH",
)


# ---- Functions -----------------------------------------------------------------------


def main(*args: str) -> int:
    parsed_args = PARSER.parse_args(args) if args else PARSER.parse_args()
    logging.getLogger().setLevel(parsed_args.log_level)
    dst_dir = tempfile.mkdtemp()
    dst_dir_path = pathlib.Path(dst_dir)
    logging.debug("created temporary directory %s", dst_dir_path)
    dst_paths_to_orig_paths = _copy_paths(
        parsed_args, dst_dir_path, _gather_paths(parsed_args)
    )

    try:
        results = mypy.api.run(parsed_args.mypy_args + [str(dst_dir)])

        if results[0]:
            for line in results[0].rstrip("\n").split("\n"):
                if line.startswith(str(dst_dir)):
                    p, rest = line.split(":", 1)
                    path = pathlib.Path(p)
                    line = "{}:{}".format(
                        str(dst_paths_to_orig_paths.get(path, path)), rest
                    )

                print(line)

        if results[1]:
            sys.stderr.write(results[1])

        return results[2]
    finally:
        if parsed_args.keep_temp_files:
            print("leaving temporary files in {}".format(dst_dir_path), file=sys.stderr)
        else:
            logging.debug("removing %s", dst_dir_path)
            shutil.rmtree(dst_dir)


def _copy_doctests(
    src_path: pathlib.Path,
    dst_f: TextIO,
    dp: doctest.DocTestParser = doctest.DocTestParser(),
):
    with src_path.open() as src_f:
        src_p = str(src_path.resolve())
        dt = dp.get_doctest(src_f.read(), {"__name__": "__main__"}, src_p, src_p, 0)
        cur_lineno = 0

        if not dt.examples:
            logging.debug("no doctests found in %s", src_path)

        for example in dt.examples:
            assert cur_lineno <= example.lineno

            while cur_lineno < example.lineno:
                dst_f.write("# skipped line {}\n".format(cur_lineno))
                cur_lineno += 1

            dst_f.write(example.source)
            cur_lineno += sum(1 for c in example.source if c == "\n")


def _copy_paths(
    parsed_args: argparse.Namespace,
    dst_dir_path: pathlib.Path,
    orig_paths: Iterable[pathlib.Path],
) -> Mapping[pathlib.Path, pathlib.Path]:
    dst_paths_to_orig_paths: Dict[pathlib.Path, pathlib.Path] = {}
    cwd_path = pathlib.Path.cwd()

    for orig_path in orig_paths:
        src_path = orig_path.resolve()
        dst_path = dst_dir_path.joinpath(src_path.relative_to(cwd_path))
        dst_path = dst_path.with_name(dst_path.name + parsed_args.tmp_file_suffix)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        logging.debug("checking %s", orig_path)

        try:
            with dst_path.open("w") as dst:
                _copy_doctests(src_path, dst)
        except FileNotFoundError:
            logging.warning("%s does not exist; skipping", orig_path)
            dst_path.unlink()
            continue
        except UnicodeDecodeError:
            logging.warning("unable to make sense of %s; skipping", orig_path)
            dst_path.unlink()
            continue

        if dst_path.stat().st_size == 0:
            if parsed_args.keep_temp_files:
                logging.debug("%s had no tests", dst_path)
            else:
                logging.debug("%s had no tests, deleting", dst_path)
                dst_path.unlink()
        else:
            logging.debug("extracted tests from %s into %s", orig_path, dst_path)
            dst_paths_to_orig_paths[dst_path] = orig_path

    return dst_paths_to_orig_paths


def _gather_paths(
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


if __name__ == "__main__":
    sys.exit(main())

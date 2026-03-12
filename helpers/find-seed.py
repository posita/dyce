#!/usr/bin/env python
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import logging
import random
import sys
from time import time

from dyce import rng

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


_EXEC_GLOBALS = {}  # type: ignore [var-annotated]


def _positive_int(val: str) -> int:
    i = int(val)

    if i <= 0:
        raise ValueError("positive value expected")

    return i


def _parsable_expr(val: str) -> str:
    if val:
        try:
            eval(val, _EXEC_GLOBALS)  # noqa: S307
        except SyntaxError as exc:
            raise ValueError from exc

    return val


def _parsable_stmt(val: str) -> str:
    if val:
        try:
            exec(val, _EXEC_GLOBALS)  # noqa: S102
        except SyntaxError as exc:
            raise ValueError from exc

    return val


_PARSER = argparse.ArgumentParser(
    description="Generate seeds for documentation examples"
)
_PARSER.add_argument(
    "-i",
    "--init",
    default="",
    type=_parsable_stmt,
    help="Python code to execute before beginning the search (useful for additional imports).",
)
_PARSER.add_argument(
    "-l",
    "--log-level",
    choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"),
    default="INFO",
)
_PARSER.add_argument(
    "-n",
    "--limit",
    type=_positive_int,
    default=10_000,
    help="The max number of seeds to consider.",
)
_PARSER.add_argument(
    "-s",
    "--seed",
    type=int,
    default=None,
    help="The seed from which to start searching. If unset, the current epoch time is used.",
)
_PARSER.add_argument(
    "input_expr",
    type=_parsable_expr,
    help="The Python expression to evaluate for each seed.",
)
_PARSER.add_argument(
    "desired_result",
    type=_parsable_expr,
    help="The Python expression to compare input_expr against for each seed.",
)

_LOGGER = logging.getLogger(__name__)

# ---- Functions -----------------------------------------------------------------------


def _main() -> None:
    args = _PARSER.parse_args()
    _LOGGER.setLevel(args.log_level)

    seed = args.seed or int(time())
    desired_result = eval(args.desired_result, _EXEC_GLOBALS)  # noqa: S307

    for i in range(args.limit):
        rng.RNG = random.Random(seed + i)
        res = eval(args.input_expr, _EXEC_GLOBALS)  # noqa: S307
        _LOGGER.debug("%d -> %s", seed + i, res)

        if res == desired_result:
            _LOGGER.info("found %r at %d after %d tries", res, seed + i, i + 1)
            break
    else:
        _LOGGER.error("%r not found after %d tries", res, i + 1)
        sys.exit(1)


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    _main()

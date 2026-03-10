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
            eval(val, _EXEC_GLOBALS)
        except SyntaxError as exc:
            raise ValueError(exc)

    return val


def _parsable_stmt(val: str) -> str:
    if val:
        try:
            exec(val, _EXEC_GLOBALS)
        except SyntaxError as exc:
            raise ValueError(exc)

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


# ---- Functions -----------------------------------------------------------------------


def _main() -> None:
    args = _PARSER.parse_args()
    logging.getLogger().setLevel(args.log_level)

    seed = args.seed if args.seed else int(time())
    desired_result = eval(args.desired_result, _EXEC_GLOBALS)

    for i in range(args.limit):
        rng.RNG = random.Random(seed + i)
        res = eval(args.input_expr, _EXEC_GLOBALS)
        logging.debug(f"{seed + i} -> {res}")

        if res == desired_result:
            logging.info(f"found {res!r} at {seed + i} after {i + 1} tries")
            break
    else:
        logging.error(f"{res!r} not found after {i + 1} tries")
        sys.exit(1)


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    _main()

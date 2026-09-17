#!/usr/bin/env python
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

import argparse
import logging
import random
from collections.abc import Sequence
from time import time
from typing import Any

from dyce import rng

__all__ = ()


def _positive_int(val: str) -> int:
    i = int(val)

    if i <= 0:
        raise ValueError("positive value expected")

    return i


def _parsable_expr(val: str) -> str:
    if val:
        try:
            compile(val, "<expression>", "eval")
        except SyntaxError as exc:
            raise ValueError from exc

    return val


def _parsable_stmt(val: str) -> str:
    if val:
        try:
            compile(val, "<initialization>", "exec")
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


def _find_seed(
    input_expr: str,
    desired_result: object,
    exec_globals: dict[str, Any],
    *,
    seed: int,
    limit: int,
) -> int | None:
    for candidate_seed in range(seed, seed + limit):
        rng.RNG = random.Random(candidate_seed)
        result = eval(input_expr, exec_globals)  # ruff: ignore[suspicious-eval-usage]
        _LOGGER.debug("%d -> %s", candidate_seed, result)

        if result == desired_result:
            return candidate_seed

    return None


def _main(argv: Sequence[str] | None = None) -> int:
    args = _PARSER.parse_args(argv)
    logging.basicConfig(level=args.log_level)

    exec_globals: dict[str, Any] = {}
    exec(args.init, exec_globals)  # ruff: ignore[exec-builtin]
    seed = int(time()) if args.seed is None else args.seed
    desired_result = eval(args.desired_result, exec_globals)  # ruff: ignore[suspicious-eval-usage]
    _LOGGER.info(
        "searching for %r among %d seeds starting at %d",
        desired_result,
        args.limit,
        seed,
    )
    found_seed = _find_seed(
        args.input_expr,
        desired_result,
        exec_globals,
        seed=seed,
        limit=args.limit,
    )

    if found_seed is None:
        _LOGGER.error(
            "%r not found among %d seeds starting at %d",
            desired_result,
            args.limit,
            seed,
        )
        return 1

    _LOGGER.info(
        "found %r at %d after %d tries",
        desired_result,
        found_seed,
        found_seed - seed + 1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

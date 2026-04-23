# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import logging
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from matplotlib import pyplot as plt
from matplotlib import style

from dyce.lifecycle import ExperimentalWarning

__all__ = ("main",)

StyleT = Literal["dark", "light"]
CallbackT = Callable[[argparse.Namespace, str, Path], None]

_PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
_PARSER.add_argument(
    "-d",
    "--output-dir",
    type=Path,
    metavar="PATH",
    default=Path.cwd(),
    help="the directory in which to save the output PNG (default is .)",
)
_PARSER.add_argument(
    "-f",
    "--output-file",
    type=Path,
    metavar="PATH",
    help="the file to which to save the output PNG (relative to -d if not absolute) (default is constructed from name and style)",
)
_PARSER.add_argument(
    "--log-level",
    default="WARNING",
    metavar="LEVEL",
    help="logging verbosity: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: WARNING)",
)
_PARSER.add_argument("-s", "--style", choices=("dark", "light"), default="light")
_LOGGER = logging.getLogger(__name__)


def name_from_path(path: str) -> str:
    return Path(path).stem


warnings.filterwarnings("ignore", category=ExperimentalWarning)


def main(name: str, callback: CallbackT) -> None:
    args = _PARSER.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    plt.figure().set_size_inches(8, 6, forward=True)
    style.use("bmh")
    output_file = (
        Path(f"{name}_{args.style}.png") if not args.output_file else args.output_file
    )
    output_path = args.output_dir.joinpath(output_file)
    _LOGGER.debug("calling %r(%r, %r, %r)", callback, args, name, output_path)
    callback(args, name, output_path)
    plt.tight_layout()
    _LOGGER.info("saving %s", output_path)
    plt.savefig(output_path, dpi=144, transparent=True)

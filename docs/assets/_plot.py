# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import logging
from collections.abc import Callable
from pathlib import Path

__all__ = ("main",)

FigCallbackT = Callable[[str], None]

_PARSER = argparse.ArgumentParser(description="Generate image files for documentation")
_PARSER.add_argument(
    "-d",
    "--output-dir",
    type=Path,
    metavar="PATH",
    default=Path.cwd(),
    help="the directory in which to save the output image (default is .)",
)
_PARSER.add_argument(
    "-f",
    "--output-file",
    type=Path,
    metavar="PATH",
    help="the file to which to save the output image (relative to -d if not absolute) (default is a PNG constructed from name and style)",
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


def main(fig_callback: FigCallbackT) -> None:
    import sys
    import warnings

    from matplotlib import pyplot as plt
    from matplotlib import style

    from dyce.lifecycle import ExperimentalWarning

    warnings.filterwarnings("ignore", category=ExperimentalWarning)
    args = _PARSER.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )
    name = Path(sys.argv[0]).stem
    output_file = (
        Path(f"{name}_{args.style}.png") if not args.output_file else args.output_file
    )
    output_path = args.output_dir.joinpath(output_file)
    line_color = "white" if args.style == "dark" else "black"

    _LOGGER.debug("calling %r(%r)", fig_callback, line_color)
    style.use("bmh")
    fig_callback(line_color)
    plt.tight_layout()
    _LOGGER.info("saving %s", output_path)
    plt.savefig(output_path, dpi=144, transparent=True)

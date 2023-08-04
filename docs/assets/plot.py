# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import logging
from functools import partial

from plug import import_plug

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


_PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
_PARSER.add_argument("-s", "--style", choices=("dark", "light"), default="light")
_PARSER.add_argument(
    "-l",
    "--log-level",
    choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"),
    default="INFO",
)
_PARSER.add_argument("fig", type=partial(import_plug, pfx="plot"))


# ---- Functions -----------------------------------------------------------------------


def _main() -> None:
    import matplotlib.pyplot
    import matplotlib.style

    args = _PARSER.parse_args()
    logging.getLogger().setLevel(args.log_level)
    mod_name, mod_do_it = args.fig
    png_path = f"plot_{mod_name}_{args.style}.png"

    matplotlib.pyplot.figure().set_size_inches(8, 6, forward=True)
    matplotlib.style.use("bmh")
    mod_do_it(args.style)
    matplotlib.pyplot.tight_layout()
    print(f"saving {png_path}")
    matplotlib.pyplot.savefig(png_path, dpi=144, transparent=True)


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    _main()

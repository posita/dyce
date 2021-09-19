# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import argparse
import logging
from functools import partial

from plug import import_plug

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


_PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
# TODO(posita): Get rid of all instances of gh here, below, and with Makefile and
# *_gh.png once this dumpster fire
# <https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981>
# gets resolved
_PARSER.add_argument("-s", "--style", choices=("dark", "light", "gh"), default="light")
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

    args = _PARSER.parse_args()
    logging.getLogger().setLevel(args.log_level)
    mod_name, mod_do_it = args.fig
    png_path = f"plot_{mod_name}_{args.style}.png"

    if args.style == "dark":
        matplotlib.pyplot.style.use("dark_background")
    elif args.style == "light":
        pass
    elif args.style == "gh":
        text_color = "gray"
        matplotlib.rcParams.update(
            {
                "text.color": text_color,
                "axes.edgecolor": text_color,
                "axes.labelcolor": text_color,
                "xtick.color": text_color,
                "ytick.color": text_color,
            }
        )
    else:
        assert False, f"unrecognized style {args.style}"

    mod_do_it(args.style)
    matplotlib.pyplot.tight_layout()
    print(f"saving {png_path}")
    matplotlib.pyplot.savefig(png_path, dpi=72, transparent=True)


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    _main()

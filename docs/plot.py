# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import argparse
from functools import partial

from plug import import_plug

PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
# TODO(posita): Get rid of all instances of gh here, below, and with Makefile and
# *_gh.png once this dumpster fire
# <https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981>
# gets resolved
PARSER.add_argument("-s", "--style", choices=("dark", "light", "gh"), default="light")
PARSER.add_argument("fig", type=partial(import_plug, pfx="plot"))


def main() -> None:
    import matplotlib.pyplot

    args = PARSER.parse_args()
    mod_name, mod_do_it = args.fig
    png_path = "plot_{}_{}.png".format(mod_name, args.style)

    if args.style == "dark":
        matplotlib.pyplot.style.use("dark_background")
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

    mod_do_it(args.style)
    matplotlib.pyplot.tight_layout()
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72, transparent=True)


if __name__ == "__main__":
    main()

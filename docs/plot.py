from __future__ import annotations, generator_stop

import argparse
from functools import partial

from plug import import_plug

PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
# TODO: Get rid of all instances of gh here, below, and with Makefile and *_gh.png once
# [this dumpster
# fire](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981)
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

from typing import Callable, Tuple
import argparse
import importlib.machinery
import importlib.util
import pathlib


def import_fig(arg: str) -> Tuple[str, Callable[[str], None]]:

    try:
        my_dir = pathlib.Path(__file__).parent
        mod_path = str(my_dir.joinpath("plot_{}.py".format(arg)))
        loader = importlib.machinery.SourceFileLoader(arg, mod_path)
        spec = importlib.util.spec_from_loader(arg, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        do_it = mod.do_it  # type: ignore
    except (AttributeError, FileNotFoundError, ImportError, SyntaxError) as exc:
        raise argparse.ArgumentTypeError('unable to load "{}" ({})'.format(arg, exc))
    else:
        return (arg, do_it)


PARSER = argparse.ArgumentParser(description="Generate PNG files for documentation")
# TODO: Get rid of all instances of gh here, below, and with Makefile and *_gh.png once
# [this dumpster
# fire](https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981)
# gets resolved
PARSER.add_argument("-s", "--style", choices=("dark", "light", "gh"), default="light")
PARSER.add_argument("fig", type=import_fig)


def main():
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
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72, transparent=True)


if __name__ == "__main__":
    main()

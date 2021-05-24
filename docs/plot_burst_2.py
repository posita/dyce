import os
from dyce import H
from dyce.plt import plot_burst


def main():
    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    d20 = H(20)
    fig, _ = plot_burst(
        d20,
        outer=(
            ("crit. fail.", d20.le(1)[1]),
            ("fail.", d20.within(2, 14)[0]),
            ("succ.", d20.within(15, 19)[0]),
            ("crit. succ.", d20.ge(20)[1]),
        ),
        graph_color="RdYlBu_r",
    )
    print("saving {}".format(png_path))
    fig.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

import os
from dyce import P
from dyce.plt import plot_burst


def main():
    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    p_d20 = P(20)
    fig, _ = plot_burst(
        p_d20.h(),
        outer=(
            ("crit. fail.", p_d20.le(1)[1]),
            ("fail.", p_d20.within(2, 14)[0]),
            ("succ.", p_d20.within(15, 19)[0]),
            ("crit. succ.", p_d20.ge(20)[1]),
        ),
        graph_color="RdYlBu_r",
    )
    print("saving {}".format(png_path))
    fig.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

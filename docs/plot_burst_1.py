import os
from dyce import H
from dyce.plt import plot_burst


def main():
    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"

    fig, _ = plot_burst(2 @ H(6))

    print("saving {}".format(png_path))
    fig.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

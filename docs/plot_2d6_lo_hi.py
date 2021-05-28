import os
from dyce import H, P


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    p_2d6 = 2 @ P(H(6))
    faces, probabilities = p_2d6.h(0).data_xy(relative=True)
    matplotlib.pyplot.bar(
        [f - 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Lowest die of 2d6",
    )

    faces, probabilities = p_2d6.h(-1).data_xy(relative=True)
    matplotlib.pyplot.bar(
        [f + 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Highest die of 2d6",
    )

    matplotlib.pyplot.legend()
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

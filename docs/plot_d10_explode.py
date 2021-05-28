import os
from dyce import H, P


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    h = (5 @ P(H(10).explode(max_depth=2))).h(slice(-3, None))
    faces, probabilities = h.data_xy(relative=True)
    matplotlib.pyplot.plot(faces, probabilities, marker=".")

    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

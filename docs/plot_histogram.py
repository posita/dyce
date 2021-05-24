import os
from dyce import H


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    faces, probabilities = (2 @ H(6)).data_xy(relative=True)
    matplotlib.pyplot.bar([str(f) for f in faces], probabilities)
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

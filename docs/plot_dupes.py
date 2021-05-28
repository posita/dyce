import os
from dyce import H, P


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    def dupes(p: P):
        for roll, count in p.rolls_with_counts():
            dupes = 0
            for i in range(1, len(roll)):
                if roll[i] == roll[i - 1]:
                    dupes += 1
            yield dupes, count

    h = H(dupes(8 @ P(10))).lowest_terms()
    faces, probabilities = h.data_xy(relative=True)
    matplotlib.pyplot.barh(faces, probabilities)

    matplotlib.pyplot.title("Number of duplicates rolled in 8d10")
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

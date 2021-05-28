import os
from dyce import H, P


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    p_4d6 = 4 @ P(6)
    h = p_4d6.h(slice(1, None))
    faces, probabilities = h.data_xy(relative=True)
    matplotlib.pyplot.plot(faces, probabilities, marker=".", label="Discard lowest")

    d6_reroll_first_one = H(6).substitute(lambda h, f: H(6) if f == 1 else f)
    p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
    h = p_4d6_reroll_first_one.h(slice(1, None))
    faces, probabilities = h.data_xy(relative=True)
    matplotlib.pyplot.plot(
        faces, probabilities, marker=".", label="Re-roll first 1; discard lowest"
    )

    p_4d6_reroll_all_ones = 4 @ P(H(range(2, 7)))
    h = p_4d6_reroll_all_ones.h(slice(1, None))
    faces, probabilities = h.data_xy(relative=True)
    matplotlib.pyplot.plot(
        faces, probabilities, marker=".", label="Re-roll all 1s; discard lowest"
    )

    matplotlib.pyplot.legend()
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

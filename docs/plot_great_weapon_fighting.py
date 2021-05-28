import os
from dyce import H


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    single_attack = 2 @ H(6) + 5
    faces, probabilities = single_attack.data_xy(relative=True)
    matplotlib.pyplot.bar(
        [f - 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Single Attack",
    )

    def gwf(h: H, face: int):
        return h if face in (1, 2) else face

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5
    faces, probabilities = great_weapon_fighting.data_xy(relative=True)
    matplotlib.pyplot.bar(
        [f + 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Great Weapon Fighting",
    )

    matplotlib.pyplot.legend()
    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

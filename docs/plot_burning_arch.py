import os
from dyce import H


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    save_roll = H(20)
    burning_arch_damage = 10 @ H(6) + 10
    pass_save = save_roll.ge(10)
    damage_half_on_save = burning_arch_damage // (pass_save + 1)
    res = damage_half_on_save
    faces, probabilities = res.data_xy(relative=True)
    matplotlib.pyplot.plot(faces, probabilities, marker=".")

    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

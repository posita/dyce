import os
from dyce import H, P


def main():
    import matplotlib.pyplot

    base, _ = os.path.splitext(__file__)
    png_path = base + ".png"
    matplotlib.pyplot.style.use("dark_background")

    normal_hit = H(12) + 5
    critical_hit = 3 @ H(12) + 5
    advantage = (2 @ P(20)).h(-1)

    def crit(_: H, f: int):
        if f == 20:
            return critical_hit
        elif f + 5 >= 14:
            return normal_hit
        else:
            return 0

    adv_w_crit = advantage.substitute(crit)
    faces, probabilities = adv_w_crit.data_xy(relative=True)
    matplotlib.pyplot.scatter(faces, probabilities, color="skyblue", marker="d")
    matplotlib.pyplot.bar(faces, probabilities, color="skyblue", width=0.25)

    print("saving {}".format(png_path))
    matplotlib.pyplot.savefig(png_path, dpi=72)


if __name__ == "__main__":
    main()

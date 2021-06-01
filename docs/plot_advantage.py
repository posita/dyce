from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

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
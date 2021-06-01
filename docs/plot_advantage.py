from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    normal_hit = H(12) + 5
    faces, probabilities = normal_hit.data_xy(relative=True)
    matplotlib.pyplot.plot(
        faces,
        probabilities,
        marker=".",
        label="normal hit",
    )
    critical_hit = 3 @ H(12) + 5
    faces, probabilities = critical_hit.data_xy(relative=True)
    matplotlib.pyplot.plot(
        faces,
        probabilities,
        marker=".",
        label="critical hit",
    )
    advantage = (2 @ P(20)).h(-1)

    def crit(_: H, f: int):
        if f == 20:
            return critical_hit
        elif f + 5 >= 14:
            return normal_hit
        else:
            return 0

    advantage_weighted = advantage.substitute(crit)
    faces, probabilities = advantage_weighted.data_xy(relative=True)
    matplotlib.pyplot.plot(
        faces,
        probabilities,
        marker=".",
        label="d20 advantage-weighted",
    )

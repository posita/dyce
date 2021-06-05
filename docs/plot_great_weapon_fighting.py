from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    single_attack = 2 @ H(6) + 5
    faces, probabilities = single_attack.data_xy()
    matplotlib.pyplot.bar(
        [f - 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Single Attack",
    )

    def gwf(h: H, face):
        return h if face in (1, 2) else face

    great_weapon_fighting = 2 @ (H(6).substitute(gwf)) + 5
    faces, probabilities = great_weapon_fighting.data_xy()
    matplotlib.pyplot.bar(
        [f + 0.125 for f in faces],
        probabilities,
        alpha=0.75,
        width=0.5,
        label="Great Weapon Fighting",
    )

    matplotlib.pyplot.legend()

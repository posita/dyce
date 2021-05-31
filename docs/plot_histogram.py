from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    faces, probabilities = (2 @ H(6)).data_xy(relative=True)
    matplotlib.pyplot.bar([str(f) for f in faces], probabilities)

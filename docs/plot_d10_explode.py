from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    h = (10 @ P(H(10).explode(max_depth=3))).h(slice(-3, None))
    faces, probabilities = h.data_xy()
    matplotlib.pyplot.plot(faces, probabilities, marker=".")

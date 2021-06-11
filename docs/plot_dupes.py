from __future__ import annotations, generator_stop

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    def dupes(p: P):
        for roll, count in p.rolls_with_counts():
            dupes = 0
            for i in range(1, len(roll)):
                if roll[i] == roll[i - 1]:
                    dupes += 1
            yield dupes, count

    res = H(dupes(8 @ P(10))).lowest_terms()
    faces, probabilities = res.data_xy()
    matplotlib.pyplot.bar(faces, probabilities)
    matplotlib.pyplot.title(r"Chances of rolling $n$ duplicates in 8d10")

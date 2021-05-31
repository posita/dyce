from dyce import H
from dyce.plt import plot_burst


def do_it(style: str) -> None:
    text_color = "white" if style == "dark" else "black"
    d20 = H(20)
    plot_burst(
        d20,
        outer=(
            ("crit. fail.", d20.le(1)[1]),
            ("fail.", d20.within(2, 14)[0]),
            ("succ.", d20.within(15, 19)[0]),
            ("crit. succ.", d20.ge(20)[1]),
        ),
        graph_color="RdYlBu_r",
        text_color=text_color,
    )

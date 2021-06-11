from __future__ import annotations, generator_stop

from dyce import H
from dyce.plt import plot_burst


def do_it(style: str) -> None:
    text_color = "white" if style == "dark" else "black"
    plot_burst(2 @ H(6), text_color=text_color)

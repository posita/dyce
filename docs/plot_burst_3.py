from __future__ import annotations, generator_stop

from dyce import H
from dyce.plt import plot_burst


def do_it(style: str) -> None:
    text_color = "white" if style == "dark" else "black"
    d8 = H(8)
    d12 = H(12)
    plot_burst(d12, d8, text_color=text_color)

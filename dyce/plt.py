# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Type

import warnings

from .lib import H

try:
    import matplotlib.axes
    import matplotlib.figure
    import matplotlib.pyplot
except ImportError:
    warnings.warn("matplotlib not found; {} APIs disabled".format(__name__))
    matplotlib = None  # noqa: F811

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


ColorT = Tuple[float, float, float, float]
ColorListT = List[ColorT]
LabelT = Tuple[str, float]

if matplotlib:
    AxesT = Type[matplotlib.axes.Axes]
    FigureT = Type[matplotlib.figure.Figure]
else:
    AxesT = Any  # type: ignore
    FigureT = Any  # type: ignore

DEFAULT_GRAPH_COLOR = "RdYlGn_r"
DEFAULT_TEXT_COLOR = "black"
DEFAULT_GRAPH_ALPHA = 0.5
_HIDE_LIM = 1 / 2 ** 6


# ---- Functions -----------------------------------------------------------------------


def alphasize(colors: ColorListT, alpha: float) -> ColorListT:
    if alpha < 0.0:
        return colors
    else:
        return [(r, g, b, alpha) for r, g, b, _ in colors]


def display_burst(
    ax: AxesT,
    h_inner: H,
    outer: Optional[Iterable[LabelT]] = None,
    desc: Optional[str] = None,
    graph_color: str = "RdYlGn",
    text_color: str = "black",
    alpha: float = 0.5,
) -> None:
    assert matplotlib

    if outer is None:
        outer = (
            ("{:.2%}".format(v) if v >= _HIDE_LIM else "", v)
            for _, v in h_inner.data(relative=True)
        )

    outer_labels, outer_values = list(zip(*outer))

    if desc:
        ax.set_title(desc, fontdict={"fontweight": "bold"}, pad=24.0)

    ax.pie(
        outer_values,
        labels=outer_labels,
        radius=1.2,
        labeldistance=1.2,
        startangle=90,
        colors=graph_colors(graph_color, outer_values, alpha),
        wedgeprops=dict(width=0.8, edgecolor=text_color),
    )
    ax.pie(
        h_inner.values(),
        labels=h_inner,
        radius=1,
        labeldistance=0.8,
        startangle=90,
        colors=graph_colors(graph_color, h_inner, alpha),
        textprops=dict(color=text_color),
        wedgeprops=dict(width=0.4, edgecolor=text_color),
    )
    ax.set(aspect="equal")


def graph_colors(name: str, vals: Iterable, alpha: float = 1.0) -> ColorListT:
    assert matplotlib
    cmap = matplotlib.pyplot.get_cmap(name)
    count = sum(1 for _ in vals)

    if count <= 1:
        colors = cmap((0.5,))
    else:
        colors = cmap([v / (count - 1) for v in range(count - 1, -1, -1)])

    return alphasize(colors, alpha)


def labels_cumulative(
    h: H,
) -> Iterator[LabelT]:
    le_total, ge_total = 0.0, 1.0
    for face, percentage in h.data(relative=True):
        le_total += percentage

        if percentage >= _HIDE_LIM:
            label = "{} {:.2%}; ≥{:.2%}; ≤{:.2%}".format(
                face, percentage, le_total, ge_total
            )
        else:
            label = ""

        ge_total -= percentage
        yield (label, percentage)


def plot_burst(
    h_inner: H,
    outer: Optional[Iterable[LabelT]] = None,
    desc: Optional[str] = None,
    graph_color: str = DEFAULT_GRAPH_COLOR,
    text_color: str = DEFAULT_TEXT_COLOR,
    alpha: float = DEFAULT_GRAPH_ALPHA,
) -> Tuple[FigureT, AxesT]:
    assert matplotlib
    fig, ax = matplotlib.pyplot.subplots()
    display_burst(ax, h_inner, outer, desc, graph_color, text_color, alpha)
    matplotlib.pyplot.tight_layout()

    return fig, ax

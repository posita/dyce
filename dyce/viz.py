# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import warnings
from fractions import Fraction
from numbers import Real
from typing import Any, Iterable, Iterator, Optional, Sequence, Tuple, Union

from numerary.bt import beartype

from .h import H
from .lifecycle import experimental

try:
    import matplotlib.pyplot
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
except ImportError:
    warnings.warn(f"matplotlib not found; {__name__} APIs disabled")
    matplotlib = None  # noqa: F811
    Axes = Any  # noqa: F811
    Figure = Any  # noqa: F811

__all__ = ()


# ---- Types ---------------------------------------------------------------------------


ColorT = Sequence[float]
ColorListT = Iterable[ColorT]
LabelT = Tuple[str, Union[float, Real]]


# ---- Data ----------------------------------------------------------------------------


DEFAULT_GRAPH_COLOR = "RdYlGn_r"
DEFAULT_TEXT_COLOR = "black"
DEFAULT_GRAPH_ALPHA = 0.5
_HIDE_LIM = Fraction(1, 2 ** 6)


# ---- Functions -----------------------------------------------------------------------


@experimental
@beartype
def alphasize(colors: ColorListT, alpha: float) -> ColorListT:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and may change or disappear in
        future versions.

    Returns a new color list where *alpha* has been applied to each color in *colors*.
    If *alpha* is negative, *colors* is returned unmodified.
    """
    if alpha < 0.0:
        return colors
    else:
        return [(r, g, b, alpha) for r, g, b, _ in colors]


@experimental
@beartype
def display_burst(
    ax: Axes,
    h_inner: H,
    outer: Optional[Union[H, Iterable[LabelT]]] = None,
    desc: Optional[str] = None,
    inner_color: str = DEFAULT_GRAPH_COLOR,
    outer_color: Optional[str] = None,
    text_color: str = DEFAULT_TEXT_COLOR,
    alpha: float = DEFAULT_GRAPH_ALPHA,
) -> None:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and may change or disappear in
        future versions.

    Creates a dual, overlapping, cocentric pie chart in *ax*, which can be useful for
    visualizing relative probability distributions. See the
    [visualization tutorial](countin.md#visualization) for examples.
    """
    assert matplotlib
    inner_colors = graph_colors(inner_color, h_inner, alpha)

    if outer is None:
        outer = (
            (f"{float(v):.2%}" if v >= _HIDE_LIM else "", v)
            for _, v in h_inner.distribution()
        )
    elif isinstance(outer, H):
        outer = ((str(outcome), count) for outcome, count in outer.distribution())

    outer_labels, outer_values = list(zip(*outer))
    outer_colors = graph_colors(
        inner_color if outer_color is None else outer_color,
        outer_values,
        alpha,
    )

    if desc:
        ax.set_title(desc, fontdict={"fontweight": "bold"}, pad=24.0)

    ax.pie(
        outer_values,
        labels=outer_labels,
        radius=1.0,
        labeldistance=1.1,
        startangle=90,
        colors=outer_colors,
        wedgeprops=dict(width=0.8, edgecolor=text_color),
    )
    ax.pie(
        h_inner.values(),
        labels=h_inner,
        radius=0.9,
        labeldistance=0.8,
        startangle=90,
        colors=inner_colors,
        textprops=dict(color=text_color),
        wedgeprops=dict(width=0.6, edgecolor=text_color),
    )
    ax.set(aspect="equal")


@experimental
@beartype
def graph_colors(name: str, vals: Iterable, alpha: float = -1.0) -> ColorListT:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and may change or disappear in
        future versions.

    Returns a color list computed from a [``matplotlib``
    colormap](https://matplotlib.org/stable/gallery/color/colormap_reference.html)
    matching *name*, weighted to to *vals*. The color list and *alpha* are passed
    through [``alphasize``][dyce.viz.alphasize] before being returned.
    """
    assert matplotlib
    cmap = matplotlib.pyplot.get_cmap(name)
    count = sum(1 for _ in vals)

    if count <= 1:
        colors = cmap((0.5,))
    else:
        colors = cmap([v / (count - 1) for v in range(count - 1, -1, -1)])

    return alphasize(colors, alpha)


@experimental
@beartype
def labels_cumulative(
    h: H,
) -> Iterator[LabelT]:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and may change or disappear in
        future versions.

    Enumerates label, probability pairs for each outcome in *h* where each label
    contains several percentages. This can be useful for passing as the *outer* value to
    either [``display_burst``][dyce.viz.display_burst] or
    [``plot_burst``][dyce.viz.plot_burst].
    """
    le_total, ge_total = 0.0, 1.0
    for outcome, probability in h.distribution():
        le_total += probability
        label = f"{outcome} {float(probability):.2%}; ≥{le_total:.2%}; ≤{ge_total:.2%}"
        ge_total -= probability
        yield (label, probability)


@experimental
@beartype
def plot_burst(
    h_inner: H,
    outer: Optional[Union[H, Iterable[LabelT]]] = None,
    desc: Optional[str] = None,
    inner_color: str = DEFAULT_GRAPH_COLOR,
    outer_color: Optional[str] = None,
    text_color: str = DEFAULT_TEXT_COLOR,
    alpha: float = DEFAULT_GRAPH_ALPHA,
) -> Tuple[Figure, Axes]:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and may change or disappear in
        future versions.

    Wrapper around [``display_burst``][dyce.viz.display_burst] that creates a figure,
    axis pair and calls
    [``matplotlib.pyplot.tight_layout``](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.tight_layout.html)
    on the result.
    """
    assert matplotlib
    fig, ax = matplotlib.pyplot.subplots()
    display_burst(ax, h_inner, outer, desc, inner_color, outer_color, text_color, alpha)
    matplotlib.pyplot.tight_layout()

    return fig, ax

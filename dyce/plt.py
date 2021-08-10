# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from typing import Iterable, Iterator, Optional, Tuple, Union

from .h import H
from .lifecycle import deprecated
from .viz import (
    DEFAULT_GRAPH_ALPHA,
    DEFAULT_GRAPH_COLOR,
    DEFAULT_TEXT_COLOR,
    Axes,
    ColorListT,
    Figure,
    LabelT,
)
from .viz import alphasize as viz_alphasize
from .viz import display_burst as viz_display_burst
from .viz import graph_colors as viz_graph_colors
from .viz import labels_cumulative as viz_labels_cumulative
from .viz import plot_burst as viz_plot_burst

__all__ = ()


# ---- Functions -----------------------------------------------------------------------


@deprecated
def alphasize(colors: ColorListT, alpha: float) -> ColorListT:
    r"""
    !!! warning "Deprecated"

        Use [``dyce.viz``][dyce.viz] instead.
    """
    return viz_alphasize(colors, alpha)


@deprecated
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
    !!! warning "Deprecated"

        Use [``dyce.viz``][dyce.viz] instead.
    """
    return viz_display_burst(
        ax, h_inner, outer, desc, inner_color, outer_color, text_color, alpha
    )


@deprecated
def graph_colors(name: str, vals: Iterable, alpha: float = -1.0) -> ColorListT:
    r"""
    !!! warning "Deprecated"

        Use [``dyce.viz``][dyce.viz] instead.
    """
    return viz_graph_colors(name, vals, alpha)


@deprecated
def labels_cumulative(
    h: H,
) -> Iterator[LabelT]:
    r"""
    !!! warning "Deprecated"

        Use [``dyce.viz``][dyce.viz] instead.
    """
    return viz_labels_cumulative(h)


@deprecated
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
    !!! warning "Deprecated"

        Use [``dyce.viz``][dyce.viz] instead.
    """
    return viz_plot_burst(
        h_inner, outer, desc, inner_color, outer_color, text_color, alpha
    )

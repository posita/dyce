# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import html
import warnings
from collections import deque
from fractions import Fraction
from numbers import Real
from typing import Any, Dict, Iterable, Iterator, Optional, Sequence, Tuple, Union

from .h import H
from .lifecycle import experimental
from .r import (
    ChainRoller,
    PoolRoller,
    R,
    RepeatRoller,
    Roll,
    RollOutcome,
    SelectionRoller,
    SumRoller,
    ValueRoller,
)

try:
    import graphviz
    from graphviz import Digraph
except ImportError:
    warnings.warn("graphviz not found; {} APIs disabled".format(__name__))
    graphviz = None  # noqa: F811
    Digraph = Any

try:
    import matplotlib.pyplot
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
except ImportError:
    warnings.warn("matplotlib not found; {} APIs disabled".format(__name__))
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
_VALUE_LEN = 24


# ---- Functions -----------------------------------------------------------------------


@experimental
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
            ("{:.2%}".format(float(v)) if v >= _HIDE_LIM else "", v)
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
        label = "{} {:.2%}; ≥{:.2%}; ≤{:.2%}".format(
            outcome, float(probability), le_total, ge_total
        )
        ge_total -= probability
        yield (label, probability)


@experimental
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


@experimental
def walk_r(
    g: Digraph,
    obj: Union[R, Roll, RollOutcome],
) -> None:
    r"""
    !!! warning "Experimental"

        This method should be considered experimental and is highly likely change or
        disappear in future versions.

    Whoo boy. What a *mess*. Hasn’t anyone around here ever heard of the visitor
    pattern? Jeez!

    This is a *study*. It‘s here so I can solve my immediate problem of generating
    pretty pictures for docs. But it’s also a vehicle for achieving enlightenment by
    being my own non-traditional customer of rollers and rolls.
    """
    serial = 1
    names: Dict[int, str] = {}

    def _name_for_obj(obj: Union[R, Roll, RollOutcome]) -> str:
        nonlocal serial, names

        if id(obj) not in names:
            names[id(obj)] = f"{type(obj).__name__}-{serial}"
            serial += 1

        return names[id(obj)]

    rollers: Dict[str, R] = {}
    rolls: Dict[str, Roll] = {}
    roll_outcomes: Dict[str, RollOutcome] = {}
    queue = deque((obj,))

    while queue:
        obj = queue.popleft()
        obj_name = _name_for_obj(obj)

        if isinstance(obj, R):
            if obj_name not in rollers:
                rollers[obj_name] = obj
                queue.extend(obj.sources)
        elif isinstance(obj, Roll):
            if obj_name not in rolls:
                rolls[obj_name] = obj
                queue.append(obj.r)

                attrs = obj.annotation if obj.annotation else {}
                g.edge(
                    obj_name,
                    _name_for_obj(obj.r),
                    label="r",
                    **attrs.get("edge", {}),
                )
                queue.extend(obj.sources)

                for i, roll_outcome in enumerate(obj):
                    attrs = roll_outcome.annotation if roll_outcome.annotation else {}
                    g.edge(
                        obj_name,
                        _name_for_obj(roll_outcome),
                        label=f"[{i}]",
                        **attrs.get("edge", {}),
                    )
                    queue.append(roll_outcome)
        elif isinstance(obj, RollOutcome):
            if obj_name not in roll_outcomes:
                roll_outcomes[obj_name] = obj
                queue.extend(obj.sources)

    if rollers:
        with g.subgraph(name="cluster_rollers") as c:
            c.attr(label="<<i>Roller Tree</i>>", style="dotted")

            for r_name, r in rollers.items():
                attrs = r.annotation if r.annotation else {}

                if isinstance(r, PoolRoller):
                    label = f"<<b>{type(r).__name__}</b>>"
                elif isinstance(r, RepeatRoller):
                    label = f"""<<b>{type(r).__name__}</b><br/><font face="Courier New">n={r.n!r}</font>>"""
                elif isinstance(r, SelectionRoller):
                    label = f"""<<b>{type(r).__name__}</b><br/><font face="Courier New">which={r.which!r}</font>>"""
                elif isinstance(r, ValueRoller):
                    value = _truncate(repr(r.value), is_html=True)
                    label = f"""<<b>{type(r).__name__}</b><br/><font face="Courier New">value={value}</font>>"""
                elif isinstance(r, (ChainRoller, SumRoller)):
                    if hasattr(r.op, "__name__"):
                        op = r.op.__name__  # type: ignore
                    else:
                        op = repr(r.op)

                    op = _truncate(op, is_html=True)
                    label = f"""<<b>{type(r).__name__}</b><br/><font face="Courier New">op={op}</font>>"""
                else:
                    label = f"<<b>{type(r).__name__}</b>>"

                c.node(r_name, label=label, **attrs.get("node", {}))

                for i, roller_src in enumerate(r.sources):
                    attrs = roller_src.annotation if roller_src.annotation else {}
                    c.edge(
                        r_name,
                        _name_for_obj(roller_src),
                        label=f"sources[{i}]",
                        **attrs.get("edge", {}),
                    )

    if rolls:
        with g.subgraph(name="cluster_rolls") as c:
            c.attr(label="<<i>Roll Tree</i>>", style="dotted")

            for roll_name, roll in rolls.items():
                attrs = roll.annotation if roll.annotation else {}
                c.node(
                    roll_name,
                    label=f"<<b>{type(roll).__name__}</b>>",
                    **attrs.get("node", {}),
                )

                for i, roll_src in enumerate(roll.sources):
                    attrs = roll_src.annotation if roll_src.annotation else {}
                    c.edge(
                        roll_name,
                        _name_for_obj(roll_src),
                        label=f"sources[{i}]",
                        **attrs.get("edge", {}),
                    )

    if roll_outcomes:
        with g.subgraph(name="cluster_roll_outcomes") as c:
            c.attr(label="<<i>Roll Outcomes</i>>", style="dotted")

            for roll_outcome_name, roll_outcome in roll_outcomes.items():
                attrs = roll_outcome.annotation if roll_outcome.annotation else {}
                c.node(
                    roll_outcome_name,
                    label=f"""<<b>{type(roll_outcome).__name__}</b><br/><font face="Courier New">value={roll_outcome.value}</font>>""",
                    **attrs.get(
                        "node",
                        {"style": "dotted"} if roll_outcome.value is None else {},
                    ),
                )

                for i, roll_outcome_src in enumerate(roll_outcome.sources):
                    attrs = (
                        roll_outcome_src.annotation
                        if roll_outcome_src.annotation
                        else {}
                    )
                    c.edge(
                        roll_outcome_name,
                        _name_for_obj(roll_outcome_src),
                        label=f"sources[{i}]",
                        **attrs.get("edge", {}),
                    )


def _truncate(value: str, value_len: int = _VALUE_LEN, is_html: bool = False) -> str:
    value = value if len(value) <= value_len else (value[: value_len - 3] + "...")

    return html.escape(value) if is_html else value

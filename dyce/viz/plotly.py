# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

r"""
`dyce.viz.plotly` builds [Plotly](https://plotly.com/) figure specifications for [`H`][dyce.H] objects.

Each builder returns a [`PlotSpec`][dyce.viz.plotly.PlotSpec] containing plain mappings and lists.
Neither Plotly nor Matplotlib is required.
Callers can pass `spec.data`, `spec.layout`, and `spec.config` to `Plotly.newPlot`, or pass `spec.figure_dict()` to `plotly.graph_objects.Figure`.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from dyce.h import H
from dyce.lifecycle import experimental

from . import GraphType, _format_percentage, values_for_graph_type

__all__ = (
    "PlotSpec",
    "bar_spec",
    "line_spec",
    "ridge_spec",
)

# Rows sit one _RIDGE_ROW_STEP apart and the tallest ridge stands _DEFAULT_RIDGE_OVERLAP of them
# high. Only the ratio matters, since the y-axis range derives from it.
_RIDGE_ROW_STEP: float = 1.0
_DEFAULT_RIDGE_OVERLAP: float = 2.4
_RIDGE_FILL_ALPHA: float = 0.4
# Seats each fill on the baseline with a slight taper, and gives a lone
# single-outcome spike a visible triangle instead of a zero-width sliver.
_RIDGE_FILL_FOOT: float = 0.1
_DEFAULT_PRECISION: int = 2


@dataclass
class PlotSpec:
    r"""
    Portable structural description of a Plotly figure.

    *data* and *layout* are accepted by both Plotly.py and Plotly.js.
    *config* contains renderer options used by Plotly.js and by HTML generated with Plotly.py.
    [`as_dict`][dyce.viz.plotly.PlotSpec.as_dict] returns a plain, JSON-serializable representation suitable for crossing a worker boundary.
    """

    data: list[dict[str, Any]]
    layout: dict[str, Any]
    config: dict[str, Any] = field(
        default_factory=lambda: {
            "responsive": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        }
    )

    def as_dict(self) -> dict[str, Any]:
        r"""Return the complete specification as plain mappings and lists."""
        return {"data": self.data, "layout": self.layout, "config": self.config}

    def figure_dict(self) -> dict[str, Any]:
        r"""Return the portion accepted by `plotly.graph_objects.Figure`."""
        return {"data": self.data, "layout": self.layout}


@experimental
def bar_spec(
    *hs: H,
    colors: Sequence[str] = (),
    graph_type: GraphType = GraphType.NORMAL,
    horizontal: bool = False,
    labels: Sequence[str] = (),
    max_percent: float | None = None,
    precision: int = _DEFAULT_PRECISION,
) -> PlotSpec:
    r"""
    Return a portable Plotly figure specification for a grouped bar chart of one or more histograms.

    Use *labels* to assign legend names to each histogram.
    Unmatched histograms receive an empty label.

    *colors* assigns hues, cycling as needed.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    When *horizontal* is `True`, outcomes appear on the y-axis and probabilities on the x-axis.

    *max_percent* fixes the probability-axis maximum, which is useful for keeping several separately rendered figures comparable.

    *precision* is the number of decimal places tooltips show.

    === "Vertical bars (default)"

            --8<-- "docs/assets/plotly_viz_plot_bar.py:viz"

        --8<-- "docs/snippets/plotly_viz_plot_bar.html"

    === "Horizontal bars (`horizontal=True`)"

            --8<-- "docs/assets/plotly_viz_plot_hbar.py:viz"

        --8<-- "docs/snippets/plotly_viz_plot_hbar.html"
    """
    data: list[dict[str, Any]] = []
    for i, h in enumerate(hs):
        label = labels[i] if i < len(labels) else ""
        outcomes, probabilities = values_for_graph_type(h, graph_type)
        outcomes_list = list(outcomes)
        percents = [probability * 100.0 for probability in probabilities]
        outcome_ref = "y" if horizontal else "x"
        trace: dict[str, Any] = {
            "type": "bar",
            "name": label,
            "orientation": "h" if horizontal else "v",
            "x": percents if horizontal else outcomes_list,
            "y": outcomes_list if horizontal else percents,
            "customdata": percents,
            "hovertemplate": f"{label}<br>%{{{outcome_ref}}}: %{{customdata:.{precision}f}}%<extra></extra>",
            "texttemplate": f"%{{customdata:.{precision}f}}%",
            "textposition": "auto",
            "meta": {"series": i, "role": "bar"},
        }
        if colors:
            trace["marker"] = {"color": colors[i % len(colors)]}
        data.append(trace)

    probability_axis: dict[str, Any] = {
        "title": {"text": "Probability (%)"},
        "rangemode": "tozero",
    }
    if max_percent is not None:
        probability_axis["range"] = [0.0, max_percent]
    outcome_axis = {"title": {"text": "Outcome"}, "zeroline": False}
    return PlotSpec(
        data=data,
        layout={
            "barmode": "group",
            "showlegend": len(hs) > 1,
            "xaxis": probability_axis if horizontal else outcome_axis,
            "yaxis": outcome_axis if horizontal else probability_axis,
        },
    )


@experimental
def line_spec(
    *hs: H,
    colors: Sequence[str] = (),
    graph_type: GraphType = GraphType.NORMAL,
    labels: Sequence[str] = (),
    precision: int = _DEFAULT_PRECISION,
) -> PlotSpec:
    r"""
    Return a portable Plotly figure specification for a line graph of one or more histograms.

    Use *labels* to assign legend names to each histogram.
    Unmatched histograms receive an empty label.

    *colors* assigns hues, cycling as needed.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    *precision* is the number of decimal places tooltips show.

    === "`graph_type=GraphType.NORMAL` (default)"

            --8<-- "docs/assets/plotly_viz_plot_line.py:viz"

        --8<-- "docs/snippets/plotly_viz_plot_line.html"

    === "`graph_type=GraphType.AT_MOST`"

            --8<-- "docs/assets/plotly_viz_plot_line_at_most.py:viz"

        --8<-- "docs/snippets/plotly_viz_plot_line_at_most.html"

    === "`graph_type=GraphType.AT_LEAST`"

            --8<-- "docs/assets/plotly_viz_plot_line_at_least.py:viz"

        --8<-- "docs/snippets/plotly_viz_plot_line_at_least.html"
    """
    data: list[dict[str, Any]] = []
    for i, h in enumerate(hs):
        label = labels[i] if i < len(labels) else ""
        outcomes, probabilities = values_for_graph_type(h, graph_type)
        color = colors[i % len(colors)] if colors else None
        marker: dict[str, Any] = {"size": 5}
        trace: dict[str, Any] = {
            "type": "scatter",
            "mode": "lines+markers",
            "name": label,
            "x": list(outcomes),
            "y": [probability * 100.0 for probability in probabilities],
            "hovertemplate": f"{label}<br>%{{x}}: %{{y:.{precision}f}}%<extra></extra>",
            "marker": marker,
            "meta": {"series": i, "role": "line"},
        }
        if color is not None:
            marker["color"] = color
            trace["line"] = {"color": color}
        data.append(trace)
    return PlotSpec(
        data=data,
        layout={
            "showlegend": len(hs) > 1,
            "hovermode": "x",
            "xaxis": {"title": {"text": "Outcome"}, "zeroline": False},
            "yaxis": {
                "title": {"text": "Probability (%)"},
                "rangemode": "tozero",
            },
        },
    )


@experimental
def ridge_spec(
    *hs: H,
    colors: Sequence[str] = (),
    graph_type: GraphType = GraphType.NORMAL,
    label_bgcolor: str | None = None,
    labels: Sequence[str] = (),
    overlap: float = _DEFAULT_RIDGE_OVERLAP,
    peak: float | None = None,
    precision: int = _DEFAULT_PRECISION,
    show_peak_labels: bool = True,
) -> PlotSpec:
    r"""
    Return a portable Plotly figure specification for a ridgeline (“joyplot”) of one or more histograms.

    Each histogram becomes its own filled ridge, stacked vertically and offset so that neighbors overlap.
    Ridges appear top-to-bottom in argument order, and lower ridges are drawn in front of higher ones.

    Each ridge covers only its own outcomes.
    Where a neighbor has an outcome this histogram lacks, the line bridges the gap rather than dipping to zero, since the histogram says nothing there rather than saying zero.

    Every ridge contributes two traces, a translucent fill and an opaque crest line carrying the markers and the tooltip.
    Each trace’s `meta` records its ridge and which of the two it is, so a caller can restyle without counting.

    Use *labels* to name each histogram.
    Names are drawn as “pills” inside the plot at their ridge’s baseline, pinned to the left edge, so a long one grows rightward over its own ridge rather than clipping into the margin.
    Unmatched histograms get a blank label.
    Set *label_bgcolor* to a translucent color appropriate for the rendering context.

    *colors* assigns a hue per ridge, cycled if there are fewer colors than histograms.
    Each ridge’s fill takes that hue translucently and its crest line takes it at full strength.
    Without *colors*, the traces carry none and Plotly’s own sequence gives a ridge’s fill and line different hues, so either supply colors or restyle by `meta` afterward.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    *overlap* is how many rows tall a ridge at *peak* stands.
    At `1.0`, such a ridge just reaches the next row's baseline.

    *peak* overrides the percentage drawn at full height, which is otherwise the largest among *hs*.
    Pass the largest across several figures to put them all on one scale, so ridges stay comparable between subplots.

    If *show_peak_labels* is `True`, each ridge’s maximum point is labeled with its probability.

    *precision* is the number of decimal places tooltips show.

        --8<-- "docs/assets/plotly_viz_plot_ridge.py:viz"

    --8<-- "docs/snippets/plotly_viz_plot_ridge.html"
    """
    rows = []
    for i, h in enumerate(hs):
        outcomes, probabilities = values_for_graph_type(h, graph_type)
        rows.append(
            (
                labels[i] if i < len(labels) else "",
                list(outcomes),
                [probability * 100.0 for probability in probabilities],
            )
        )
    num_rows = len(rows)
    peak_height = overlap * _RIDGE_ROW_STEP
    if peak is None:
        peak = max((max(percents, default=0.0) for _, _, percents in rows), default=0.0)
    data: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    for i, (label, row_outcomes, percents) in enumerate(rows):
        baseline = float(num_rows - 1 - i) * _RIDGE_ROW_STEP
        scale = peak_height / peak if peak else 0.0
        crests = [baseline + percent * scale for percent in percents]
        color = colors[i % len(colors)] if colors else None
        fill: dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "x": [
                row_outcomes[0] - _RIDGE_FILL_FOOT,
                *row_outcomes,
                row_outcomes[-1] + _RIDGE_FILL_FOOT,
            ]
            if row_outcomes
            else [],
            "y": [baseline, *crests, baseline] if row_outcomes else [],
            "fill": "toself",
            "line": {"width": 0},
            "hoverinfo": "skip",
            "showlegend": False,
            "meta": {"ridge": i, "role": "fill"},
        }
        if color is not None:
            fill["fillcolor"] = _with_alpha(color, _RIDGE_FILL_ALPHA)
        data.append(fill)
        marker: dict[str, Any] = {"size": 4}
        # The plotted y is offset and scaled, so tooltips read the true
        # percentages out of customdata instead.
        line: dict[str, Any] = {
            "type": "scatter",
            "mode": "lines+markers",
            "x": list(row_outcomes),
            "y": crests,
            "name": label,
            "customdata": percents,
            "hovertemplate": f"{label}<br>%{{x}}: %{{customdata:.{precision}f}}%<extra></extra>",
            "marker": marker,
            "showlegend": False,
            "meta": {"ridge": i, "role": "line"},
        }
        if color is not None:
            marker["color"] = color
            line["line"] = {"color": color, "width": 1.5}
        data.append(line)
        annotation: dict[str, Any] = {
            "name": "ridge-label",
            "xref": "paper",
            "x": 0,
            "xanchor": "left",
            "xshift": 4,
            "yref": "y",
            "y": baseline,
            "yanchor": "bottom",
            "yshift": 2,
            "text": label,
            "showarrow": False,
            "align": "left",
            "borderpad": 2,
        }
        if label_bgcolor is not None:
            annotation["bgcolor"] = label_bgcolor
        annotations.append(annotation)
        if show_peak_labels and percents:
            ridge_peak = max(percents)
            peak_indices = tuple(
                i for i, percent in enumerate(percents) if percent == ridge_peak
            )
            peak_index = peak_indices[len(peak_indices) // 2]
            peak_on_left = peak_index <= (len(row_outcomes) - 1) / 2.0
            peak_annotation: dict[str, Any] = {
                "name": "ridge-peak-label",
                "xref": "x",
                "x": row_outcomes[peak_index],
                "xanchor": "left" if peak_on_left else "right",
                "ax": 8 if peak_on_left else -8,
                "ay": 0,
                "yref": "y",
                "y": crests[peak_index],
                "yanchor": "middle",
                "text": _format_percentage(ridge_peak / 100.0),
                "showarrow": True,
                "arrowhead": 0,
                "arrowwidth": 0.75,
                "borderpad": 2,
            }
            if color is not None:
                peak_annotation["arrowcolor"] = _with_alpha(color, 0.4)
            if label_bgcolor is not None:
                peak_annotation["bgcolor"] = label_bgcolor
            annotations.append(peak_annotation)

    return PlotSpec(
        data=data,
        layout={
            "showlegend": False,
            # Not "x unified": one tooltip per ridge at the outcome nearest the
            # cursor, all at once. The fills skip hover, so that is exactly one
            # apiece.
            "hovermode": "x",
            "annotations": annotations,
            "shapes": [],
            "xaxis": {"title": {"text": "Outcome"}, "zeroline": False},
            "yaxis": {
                "showticklabels": False,
                "showgrid": False,
                "zeroline": False,
                "range": [
                    -0.5 * _RIDGE_ROW_STEP,
                    (num_rows - 1) * _RIDGE_ROW_STEP
                    + peak_height
                    + 0.5 * _RIDGE_ROW_STEP,
                ],
            },
        },
    )


def _with_alpha(color: str, alpha: float) -> str:
    if color.startswith("#") and len(color) in (4, 7):
        if len(color) == 4:
            red, green, blue = (int(channel * 2, 16) for channel in color[1:])
        else:
            red, green, blue = (int(color[i : i + 2], 16) for i in (1, 3, 5))

        return f"rgba({red},{green},{blue},{alpha})"

    return color

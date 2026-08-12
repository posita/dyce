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
`dyce.viz_plotly` builds [Plotly](https://plotly.com/) figure specifications for [`H`][dyce.H] objects.

Each builder returns a [`PlotSpec`][dyce.viz_plotly.PlotSpec] containing plain mappings and lists.
Nothing imports Plotly (or Matplotlib) until [`figure_from_spec`][dyce.viz_plotly.figure_from_spec] is called.
Browser callers can instead pass `spec.data`, `spec.layout`, and `spec.config` to `Plotly.newPlot`.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from .h import H
from .lifecycle import experimental

__all__ = ("PlotSpec", "figure_from_spec", "ridge_spec")

# Rows sit one _RIDGE_ROW_STEP apart and the tallest ridge stands _DEFAULT_RIDGE_OVERLAP of them
# high. Only the ratio matters, since the y-axis range derives from it.
_RIDGE_ROW_STEP: float = 1.0
_DEFAULT_RIDGE_OVERLAP: float = 2.4
_RIDGE_FILL_ALPHA: float = 0.4
# Seats each fill on the baseline with a slight taper, and gives a lone
# single-outcome spike a visible triangle instead of a zero-width sliver.
_RIDGE_FILL_FOOT: float = 0.1
_DEFAULT_PRECISION: int = 2


class _FigureT(Protocol):
    data: tuple[Any, ...]
    layout: Any

    def to_html(self, *args: object, **kwargs: object) -> str: ...

    def update_layout(self, *args: object, **kwargs: object) -> object: ...


@dataclass
class PlotSpec:
    r"""
    Portable structural description of a Plotly figure.

    *data* and *layout* are accepted by both Plotly.py and Plotly.js.
    *config* contains renderer options used by Plotly.js and by HTML generated with Plotly.py.
    [`as_dict`][dyce.viz_plotly.PlotSpec.as_dict] returns a plain, JSON-serializable representation suitable for crossing a worker boundary.
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
def ridge_spec(
    *hs: H,
    colors: Sequence[str] = (),
    label_bgcolor: str | None = None,
    labels: Sequence[str] = (),
    overlap: float = _DEFAULT_RIDGE_OVERLAP,
    peak: float | None = None,
    precision: int = _DEFAULT_PRECISION,
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
    Set *label_bgcolor* to a translucent color appropriate for the rendering context.
    Unmatched histograms get a blank label.

    *colors* assigns a hue per ridge, cycled if there are fewer colors than histograms.
    Each ridge’s fill takes that hue translucently and its crest line takes it at full strength.
    Without *colors*, the traces carry none and Plotly’s own sequence gives a ridge’s fill and line different hues, so either supply colors or restyle by `meta` afterward.

    *peak* overrides the percentage drawn at full height, which is otherwise the largest among *hs*.
    Pass the largest across several figures to put them all on one scale, so ridges stay comparable between subplots.

    *overlap* is how many rows tall a ridge at *peak* stands.
    At `1.0`, such a ridge just reaches the next row's baseline.

    *precision* is the number of decimal places tooltips show.

        --8<-- "docs/assets/plotly_viz_plot_ridge.py:viz"

    --8<-- "docs/snippets/plotly_viz_plot_ridge.html"
    """
    rows = [
        (labels[i] if i < len(labels) else "", list(h.outcomes()), _percents(h))
        for i, h in enumerate(hs)
    ]
    num_rows = len(rows)
    peak_height = overlap * _RIDGE_ROW_STEP
    if peak is None:
        peak = max((max(percents, default=0.0) for _, _, percents in rows), default=0.0)
    data: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []

    for i, (label, outcomes, percents) in enumerate(rows):
        baseline = float(num_rows - 1 - i) * _RIDGE_ROW_STEP
        scale = peak_height / peak if peak else 0.0
        crests = [baseline + percent * scale for percent in percents]
        color = colors[i % len(colors)] if colors else None
        fill: dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "x": [
                outcomes[0] - _RIDGE_FILL_FOOT,
                *outcomes,
                outcomes[-1] + _RIDGE_FILL_FOOT,
            ]
            if outcomes
            else [],
            "y": [baseline, *crests, baseline] if outcomes else [],
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
            "x": list(outcomes),
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

    return PlotSpec(
        data=data,
        layout={
            "showlegend": False,
            # Not "x unified": one tooltip per ridge at the outcome nearest the
            # cursor, all at once. The fills skip hover, so that is exactly one
            # apiece.
            "hovermode": "x",
            "annotations": annotations,
            "xaxis": {"title": {"text": "Outcome"}},
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


# ---- Helpers -------------------------------------------------------------------------


def _percents(h: H) -> list[float]:
    return [float(probability) * 100.0 for _, probability in h.probability_items()]


@experimental
def figure_from_spec(spec: PlotSpec) -> _FigureT:
    r"""
    Return a `plotly.graph_objects.Figure` for *spec*.

    Plotly is only required when this convenience function is called.
    """
    try:
        from plotly.graph_objects import Figure  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "figure_from_spec requires plotly; install with: pip install 'dyce[plotly]'"
        ) from exc

    return cast("_FigureT", Figure(spec.figure_dict()))


def _with_alpha(color: str, alpha: float) -> str:
    if color.startswith("#") and len(color) in (4, 7):
        if len(color) == 4:
            red, green, blue = (int(channel * 2, 16) for channel in color[1:])
        else:
            red, green, blue = (int(color[i : i + 2], 16) for i in (1, 3, 5))

        return f"rgba({red},{green},{blue},{alpha})"

    return color

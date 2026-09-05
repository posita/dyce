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
`dyce.viz.matplotlib` provides optional, basic [Matplotlib](https://matplotlib.org/)-based visualization utilities.
Its requirements can be installed via the `viz-mpl` optional dependency group.

```sh
pip install 'dyce[viz-mpl]'
# or
uv sync --group viz-mpl
```

<!-- BEGIN MONKEY PATCH --
>>> from typing import Any
>>> _: Any

  -- END MONKEY PATCH -->
"""

from collections.abc import Callable, Sequence
from fractions import Fraction
from itertools import accumulate, cycle
from typing import Generic, TypedDict, TypeVar, cast, overload

try:
    import matplotlib as mpl
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "dyce[viz-mpl] requires matplotlib; install with: pip install 'dyce[viz-mpl]'"
    ) from exc
else:
    from matplotlib import colors as mcolors
    from matplotlib import pyplot as plt
    from matplotlib import ticker as mticker
    from matplotlib import transforms as mtransforms
    from matplotlib.axes import Axes
    from matplotlib.colors import Colormap
    from matplotlib.typing import RGBAColorType

from dyce.h import H
from dyce.lifecycle import experimental
from dyce.types import natural_key

from . import GraphType, _format_percentage, values_for_graph_type

__all__ = (
    "BurstFormatterT",
    "format_outcome_name",
    "format_outcome_name_probability",
    "format_probability",
    "plot_bar",
    "plot_burst",
    "plot_line",
    "plot_ridge",
)

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")


class _RidgeT(TypedDict, Generic[_T]):
    label: str
    outcomes: tuple[_T, ...]
    probs: tuple[float, ...]
    baseline: int
    color: RGBAColorType | None


BurstFormatterT = Callable[[_T, Fraction, H[_T]], str]
r"""
Callable type for burst-plot wedge labels.

Called as `formatter(outcome, probability, histogram)`.
Return an empty string to suppress the label for that wedge.
"""

_DEFAULT_MARKERS: str = "."
_DEFAULT_PLOT_ALPHA: float = 0.75
_DEFAULT_RIDGE_ALPHA: float = 0.4
_DEFAULT_RIDGE_OVERLAP: float = 2.4

_LABEL_LIM: Fraction = Fraction(1, 2**5)  # suppress burst labels below ~3.1%
_RIDGE_FILL_FOOT: float = 0.1
_RIDGE_ROW_STEP: float = 1.0

_formatter: BurstFormatterT


@experimental
def format_outcome_name(
    outcome: _T,
    prob: Fraction,  # ruff: ignore[unused-function-argument]
    h: H[_T],  # ruff: ignore[unused-function-argument]
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with its outcome.
    If *outcome* has a `.name` attribute (e.g. an `Enum`), that is used; otherwise `str(outcome)` is used.
    """
    return str(outcome.name) if hasattr(outcome, "name") else str(outcome)  # pyright: ignore[reportAttributeAccessIssue]


_formatter = format_outcome_name


@experimental
def format_outcome_name_probability(
    outcome: _T,
    prob: Fraction,
    h: H[_T],
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with both its outcome and probability.
    If *outcome* has a `.name` attribute (e.g. an `Enum`), that is used; otherwise `str(outcome)` is used.
    """
    name = format_outcome_name(outcome, prob, h)
    return f"{name}\n{format_probability(outcome, prob, h)}"


_formatter = format_outcome_name_probability


@experimental
def format_probability(
    outcome: _T,  # ruff: ignore[unused-function-argument]
    prob: Fraction,
    h: H[_T],  # ruff: ignore[unused-function-argument]
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with its probability as a percentage.
    """
    return f"{float(prob):.2%}"


_formatter = format_probability
del _formatter


@experimental
def plot_bar(
    *hs: H,
    alpha: float = _DEFAULT_PLOT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap | None = None,
    graph_type: GraphType = GraphType.NORMAL,
    horizontal: bool = False,
    labels: Sequence[str] = (),
) -> Axes:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

    Plots a grouped bar chart of one or more histograms.

    Use *labels* to assign legend names to each histogram.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    When *horizontal* is `True`, bars are drawn horizontally with outcomes on the y-axis and probabilities on the x-axis.

    If *ax* is `None`, `matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

    === "Vertical bars (default)"

            --8<-- "docs/assets/plot_viz_plot_bar.py:viz"

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_bar_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_bar_light.svg">
            <img alt="Plot: 2d10 vs. d8 + d12, vertically and horizontally" src="../assets/plot_viz_plot_bar_light.svg">
        </picture>

    === "Horizontal bars (`horizontal=True`)"

            --8<-- "docs/assets/plot_viz_plot_hbar.py:viz"

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_hbar_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_hbar_light.svg">
            <img alt="Plot: 2d10 vs. d8 + d12, vertically and horizontally" src="../assets/plot_viz_plot_hbar_light.svg">
        </picture>
    """
    hs_list = _labeled_hs(hs, labels)
    ax = _get_ax(ax)
    pct_formatter = mticker.PercentFormatter(xmax=1)
    if horizontal:
        ax.xaxis.set_major_formatter(pct_formatter)
    else:
        ax.yaxis.set_major_formatter(pct_formatter)
    if not hs_list:
        return ax

    unique_outcomes = _sorted_outcomes(hs_list)
    n = len(hs_list)
    bar_width = 0.8 / n
    if unique_outcomes:
        lo, hi = unique_outcomes[0], unique_outcomes[-1]
        if horizontal:
            ax.set_yticks(unique_outcomes)
            ax.set_ylim(lo - 1.0, hi + 1.0)
        else:
            ax.set_xticks(unique_outcomes)
            ax.set_xlim(lo - 1.0, hi + 1.0)
    colors = _colors_linear(cmap, len(hs_list), alpha) if cmap else None
    for i, (label, h) in enumerate(hs_list):
        outcomes, probs = values_for_graph_type(h, graph_type)
        offsets = [o + (i + 0.5) * bar_width - 0.4 for o in outcomes]
        if horizontal:
            ax.barh(
                offsets,
                probs,
                height=bar_width,
                alpha=alpha,
                color=colors[i] if colors else None,
                label=label or None,
            )
        else:
            ax.bar(
                offsets,
                probs,
                width=bar_width,
                alpha=alpha,
                color=colors[i] if colors else None,
                label=label or None,
            )

    return ax


@overload
def plot_burst(
    h: H[_T1],
    compare: None = ...,
    *,
    alpha: float = ...,
    ax: Axes | None = ...,
    cmap: str | Colormap | None = ...,
    compare_cmap: str | Colormap | None = ...,
    compare_formatter: BurstFormatterT[_T1] | None = ...,
    formatter: BurstFormatterT[_T1] = ...,
    title: str = ...,
    use_midpoints_for_colors: bool = ...,
) -> Axes: ...
@overload
def plot_burst(
    h: H[_T1],
    compare: H[_T2],
    *,
    alpha: float = ...,
    ax: Axes | None = ...,
    cmap: str | Colormap | None = ...,
    compare_cmap: str | Colormap | None = ...,
    compare_formatter: BurstFormatterT[_T2],
    formatter: BurstFormatterT[_T1] = ...,
    title: str = ...,
    use_midpoints_for_colors: bool = ...,
) -> Axes: ...
@overload
def plot_burst(
    h: H[_T1],
    compare: H[_T2],
    *,
    alpha: float = ...,
    ax: Axes | None = ...,
    cmap: str | Colormap | None = ...,
    compare_cmap: str | Colormap | None = ...,
    compare_formatter: None = ...,
    formatter: BurstFormatterT[_T1 | _T2] = ...,
    title: str = ...,
    use_midpoints_for_colors: bool = ...,
) -> Axes: ...
@overload
def plot_burst(
    h: H[_T1],
    compare: H[_T2],
    *,
    alpha: float = ...,
    ax: Axes | None = ...,
    cmap: str | Colormap | None = ...,
    compare_cmap: str | Colormap | None = ...,
    compare_formatter: BurstFormatterT[_T2] | None = ...,
    formatter: BurstFormatterT[_T1] = ...,
    title: str = ...,
    use_midpoints_for_colors: bool = ...,
) -> Axes: ...
@experimental
def plot_burst(
    h: H[_T1],
    compare: H[_T2] | None = None,
    *,
    alpha: float = _DEFAULT_PLOT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap | None = None,
    compare_cmap: str | Colormap | None = None,
    compare_formatter: BurstFormatterT[_T2] | None = None,
    formatter: BurstFormatterT[_T1] | BurstFormatterT[_T1 | _T2] = format_outcome_name,
    title: str = "",
    use_midpoints_for_colors: bool = True,
) -> Axes:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

    Plots a dual concentric pie chart for one or two histograms, useful for getting a “feel” when comparing distributions.

    The inner ring represents *h* and the outer ring represents *compare*.
    When *compare* is `None` (the default), both rings show the same histogram: the inner ring labels outcomes (via *formatter*) and the outer ring labels probabilities.
    When *compare* differs from *h*, both rings default to labelling outcomes
    This is useful for comparing two related distributions side-by-side in a single visual.

    Wedge labels are suppressed when the probability is below `Fraction(1, 32)` (~3.1%) to avoid clutter.

    *formatter* and *compare_formatter* are `BurstFormatterT` callables (see `format_outcome_name`, `format_probability`, `format_outcome_name_probability`).

    *cmap* / *compare_cmap* accept any matplotlib colormap name or instance.
    If `None`, `mpl.rcParams["image.cmap"]` is used.

    If *ax* is `None`, `matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

        --8<-- "docs/assets/plot_viz_plot_burst.py:viz"

    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_burst_dark.svg">
        <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_burst_light.svg">
        <img alt="Plot: 2d10 vs. d8 + d12" src="../assets/plot_viz_plot_burst_light.svg">
    </picture>
    """
    ax = _get_ax(ax)
    h_compare = cast("H[_T2]", h if compare is None else compare)
    if compare_formatter is None:
        compare_formatter = cast(
            "BurstFormatterT[_T2]", format_probability if compare is None else formatter
        )

    def _wedges(
        hist: H[_T], fmt: BurstFormatterT[_T]
    ) -> tuple[tuple[str, ...], tuple[float, ...]]:
        labels_list: list[str] = []
        probs_list: list[float] = []
        for outcome, probability in hist.probability_items():
            label = fmt(outcome, probability, hist) if probability >= _LABEL_LIM else ""
            labels_list.append(label)
            probs_list.append(float(probability))
        return tuple(labels_list), tuple(probs_list)

    inner_labels, inner_probs = _wedges(h, formatter)
    outer_labels, outer_probs = _wedges(h_compare, compare_formatter)
    cmap = mpl.rcParams["image.cmap"] if cmap is None else cmap
    assert cmap is not None
    compare_cmap = mpl.rcParams["image.cmap"] if compare_cmap is None else compare_cmap
    assert compare_cmap is not None
    inner_colors = _colors_proportionate(
        cmap, inner_probs, alpha, use_midpoints=use_midpoints_for_colors
    )
    outer_colors = _colors_proportionate(
        compare_cmap, outer_probs, alpha, use_midpoints=use_midpoints_for_colors
    )
    if title:
        ax.set_title(title, fontweight="bold", pad=24.0)
    if outer_probs:
        ax.pie(
            outer_probs,
            labels=outer_labels,
            radius=1.0,
            labeldistance=1.15,
            startangle=90,
            colors=outer_colors,
            wedgeprops={"width": 0.8},
        )
    if inner_probs:
        ax.pie(
            inner_probs,
            labels=inner_labels,
            radius=0.85,
            labeldistance=0.7,
            startangle=90,
            colors=inner_colors,
            wedgeprops={"width": 0.5},
        )
    ax.set(aspect="equal")

    return ax


@experimental
def plot_line(
    *hs: H,
    alpha: float = _DEFAULT_PLOT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap | None = None,
    graph_type: GraphType = GraphType.NORMAL,
    labels: Sequence[str] = (),
    markers: str = _DEFAULT_MARKERS,
) -> Axes:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

    Plots a line graph of one or more histograms.

    Use *labels* to assign legend names to each histogram.
    Unmatched histograms receive an empty label.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    *markers* is a string whose characters are cycled across histograms (e.g. `"oX^"` produces circle, cross, triangle, circle, …).

    If *ax* is `None`, `matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

    === "`graph_type=GraphType.NORMAL` (default)"

            --8<-- "docs/assets/plot_viz_plot_line.py:viz"

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_line_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_line_light.svg">
            <img alt="Plot: d6 and 2d10 vs. d8 + d12" src="../assets/plot_viz_plot_line_light.svg">
        </picture>

    === "`graph_type=GraphType.AT_MOST`"

            --8<-- "docs/assets/plot_viz_plot_line_at_most.py:viz"

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_line_at_most_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_line_at_most_light.svg">
            <img alt="Plot: d6 and 2d10 vs. d8 + d12" src="../assets/plot_viz_plot_line_at_most_light.svg">
        </picture>

    === "`graph_type=GraphType.AT_LEAST`"

            --8<-- "docs/assets/plot_viz_plot_line_at_least.py:viz"

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_line_at_least_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_line_at_least_light.svg">
            <img alt="Plot: d6 and 2d10 vs. d8 + d12" src="../assets/plot_viz_plot_line_at_least_light.svg">
        </picture>
    """
    hs_list = _labeled_hs(hs, labels)
    ax = _get_ax(ax)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    if not hs_list:
        return ax

    unique_outcomes = _sorted_outcomes(hs_list)
    if unique_outcomes:
        lo, hi = unique_outcomes[0], unique_outcomes[-1]
        ax.set_xticks(unique_outcomes)
        ax.set_xlim(lo - 0.5, hi + 0.5)
    colors = _colors_linear(cmap, len(hs_list), alpha) if cmap else None
    markers_cycle_forever = cycle(markers or " ")
    for i, ((label, h), marker) in enumerate(
        zip(hs_list, markers_cycle_forever, strict=False)
    ):
        outcomes, probs = values_for_graph_type(h, graph_type)
        ax.plot(
            outcomes,
            probs,
            color=colors[i] if colors else None,
            label=label or None,
            marker=marker,
            alpha=alpha,
        )

    return ax


@experimental
def plot_ridge(
    *hs: H[_T],
    alpha: float = _DEFAULT_RIDGE_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap | None = None,
    graph_type: GraphType = GraphType.NORMAL,
    labels: Sequence[str] = (),
    overlap: float = _DEFAULT_RIDGE_OVERLAP,
    peak: float | None = None,
    show_peak_labels: bool = True,
) -> Axes:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

    Plots a ridgeline (“joyplot”) of one or more histograms, useful for comparing a family of related distributions, where [`plot_line`][dyce.viz.matplotlib.plot_line] would produce a tangle of overlapping curves.

    Each histogram becomes its own filled ridge, stacked vertically and offset so that neighbors overlap.
    Ridges appear top-to-bottom in argument order, and lower ridges are drawn in front of higher ones.

    Each ridge covers only its own outcomes.
    Where a neighbor has an outcome this histogram lacks, the line bridges the gap rather than dipping to zero, since the histogram says nothing there rather than saying zero.

    Use *labels* to name each histogram.
    Names are drawn inside the plot at their ridge’s baseline, pinned to the left edge, so a long one grows rightward over its own ridge rather than clipping into the margin.
    Unmatched histograms get a blank label.

    *cmap* accepts any Matplotlib colormap name or instance, sampled evenly to color the ridges.
    If `None`, the default line colors associated with the current style are used.
    Pass `mpl.rcParams["image.cmap"]` to use the default color map instead.

    *graph_type* controls which variant of the distribution is plotted (see [`GraphType`][dyce.viz.GraphType]).

    *overlap* is how many rows tall a ridge at *peak* stands.
    At `1.0`, such a ridge just reaches the next row's baseline.

    *peak* overrides the percentage drawn at full height, which is otherwise the largest among *hs*.
    Pass the largest across several figures to put them all on one scale, so ridges stay comparable between subplots.

    If *show_peak_labels* is `True`, each ridge’s maximum point is labeled with its probability.

    If *ax* is `None`, `matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

        --8<-- "docs/assets/plot_viz_plot_ridge.py:viz"

    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_ridge_dark.svg">
        <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_ridge_light.svg">
        <img alt="Plot: 2d10 vs. d8 + d12" src="../assets/plot_viz_plot_ridge_light.svg">
    </picture>
    """
    hs_list = _labeled_hs(hs, labels)
    ax = _get_ax(ax)
    if not hs_list:
        return ax

    unique_outcomes = _sorted_outcomes(hs_list)
    if unique_outcomes:
        lo, hi = unique_outcomes[0], unique_outcomes[-1]
        ax.set_xticks(unique_outcomes)  # type: ignore[arg-type] # ty: ignore[invalid-argument-type]
        ax.set_xlim(lo - 0.5, hi + 0.5)  # type: ignore[operator] # ty: ignore[unsupported-operator]
    colors = _colors_linear(cmap, len(hs_list)) if cmap else None
    ridges: list[_RidgeT[_T]] = []
    for i, (label, h) in enumerate(hs_list):
        outcomes, probs = values_for_graph_type(h, graph_type)
        ridges.append(
            {
                "label": label,
                "outcomes": outcomes,
                "probs": probs,
                "baseline": len(hs_list) - 1 - i,  # ordered top-to-bottom
                "color": colors[i] if colors else None,
            }
        )
    peak = (
        max((max(row["probs"], default=0.0) for row in ridges), default=0.0)
        if peak is None
        else peak
    )
    peak_height = overlap * _RIDGE_ROW_STEP
    scale = peak_height / peak if peak else 0.0
    ridge_transform = mtransforms.blended_transform_factory(
        # Makes sure labels appear at the leftmost edge of the graph, rather than where
        # an outcome of value 0 is or would have been
        ax.transAxes,
        # This is the default (i.e., no change)
        ax.transData,
    )
    label_transform = mtransforms.offset_copy(
        ridge_transform,
        fig=ax.get_figure(root=True),
        x=4.0,
        units="points",
    )
    ylim = (
        -0.5 * _RIDGE_ROW_STEP,
        (len(ridges) - 1) * _RIDGE_ROW_STEP + peak_height + 0.5 * _RIDGE_ROW_STEP,
    )
    for i, ridge in enumerate(ridges):
        crests = tuple(ridge["baseline"] + prob * scale for prob in ridge["probs"])
        (line,) = ax.plot(
            cast("Sequence[float] | Sequence[int] | Sequence[str]", ridge["outcomes"]),
            crests,
            color=ridge["color"],
            marker=_DEFAULT_MARKERS[0],
            zorder=2 * i + 1,  # lower rows are appear in front of higher rows
        )
        red, green, blue = mcolors.to_rgb(line.get_color())
        fill_outcomes = ridge["outcomes"]
        fill_crests: tuple[float | int, ...] = crests
        if fill_outcomes:
            fill_outcomes = (
                ridge["outcomes"][0] - _RIDGE_FILL_FOOT,  # type: ignore[arg-type,operator] # ty: ignore[unsupported-operator]
                *fill_outcomes,
                ridge["outcomes"][-1] + _RIDGE_FILL_FOOT,  # type: ignore[arg-type,operator] # ty: ignore[unsupported-operator]
            )
            fill_crests = (
                ridge["baseline"],
                *fill_crests,
                ridge["baseline"],
            )
        if ridge["outcomes"]:
            ax.fill(
                fill_outcomes,
                fill_crests,
                color=(red, green, blue, alpha),
                zorder=2 * i,  # sits just behind the line
            )
        label_text = ax.text(
            0.0,
            ridge["baseline"],
            ridge["label"],
            transform=label_transform,
            ha="left",
            va="bottom",
            zorder=2 * len(ridges),  # on top of everything
            bbox={
                "boxstyle": "square,pad=0.2",
                "facecolor": mcolors.to_rgba(ax.get_facecolor(), 0.72),
                "edgecolor": "none",
            },
        )
        label_text.set_gid("ridge-label")
        if show_peak_labels and ridge["probs"]:
            ridge_peak = max(ridge["probs"])
            peak_indices = tuple(
                i for i, prob in enumerate(ridge["probs"]) if prob == ridge_peak
            )
            peak_index = peak_indices[len(peak_indices) // 2]
            peak_outcome = ridge["outcomes"][peak_index]
            peak_y = crests[peak_index]
            peak_on_left = (
                ax.transData.transform((ax.convert_xunits(peak_outcome), peak_y))[0]
                <= ax.transAxes.transform((0.5, 0.0))[0]
            )
            x_offset = 8.0 if peak_on_left else -8.0
            peak_text = ax.annotate(
                _format_percentage(ridge_peak),
                xy=(peak_outcome, peak_y),
                xytext=(x_offset, 0.0),
                textcoords="offset points",
                color=mpl.rcParams["ytick.color"],
                ha="left" if peak_on_left else "right",
                va="center",
                zorder=2 * len(ridges),
                bbox={
                    "boxstyle": "square,pad=0.2",
                    "facecolor": mcolors.to_rgba(ax.get_facecolor(), 0.72),
                    "edgecolor": "none",
                },
                arrowprops={
                    "arrowstyle": "-",
                    "color": mcolors.to_rgba(line.get_color(), 0.4),
                    "linewidth": 0.75,
                },
            )
            peak_text.set_gid("ridge-peak-label")
            peak_text.set_in_layout(False)

    # Baselines are the only reference the rows need, so the y-axis carries no
    # ticks or grid of its own.
    ax.set_yticks([])
    ax.yaxis.grid(visible=False)
    ax.set_ylim(*ylim)

    return ax


# ---- Helpers -------------------------------------------------------------------------


def _colors_linear(
    cmap: str | Colormap,
    num_rows: int,
    alpha: float = 1.0,
) -> list[tuple[float, float, float, float]]:
    cm: Colormap = plt.colormaps.get_cmap(cmap) if isinstance(cmap, str) else cmap
    points = [i / (num_rows - 1) for i in range(num_rows)] if num_rows > 1 else [0.5]
    return [(r, g, b, alpha) for r, g, b, _ in (cm(p) for p in points)]


def _colors_proportionate(
    cmap: str | Colormap,
    probs: tuple[float, ...],
    alpha: float = 1.0,
    *,
    use_midpoints: bool = True,
) -> list[tuple[float, float, float, float]]:
    cm: Colormap = plt.colormaps.get_cmap(cmap) if isinstance(cmap, str) else cmap
    total = sum(probs, start=0.0)
    if not total:
        return []

    cumul = list(accumulate(probs, initial=0.0))
    points = (
        [(cumul[i] + cumul[i + 1]) / (2.0 * total) for i in range(len(probs))]
        if use_midpoints
        else [i / (len(probs) - 1) for i in range(len(probs))]
    )

    return [(r, g, b, alpha) for r, g, b, _ in (cm(p) for p in points)]


def _get_ax(ax: Axes | None) -> Axes:
    return ax if ax is not None else plt.gca()


def _labeled_hs(
    hs: tuple[H[_T], ...],
    labels: Sequence[str],
) -> list[tuple[str, H[_T]]]:
    return [(labels[i] if i < len(labels) else "", h) for i, h in enumerate(hs)]


def _sorted_outcomes(hs_list: list[tuple[str, H[_T]]]) -> list[_T]:
    all_outcomes: set[_T] = {o for _, h in hs_list for o in h}
    try:
        return sorted(all_outcomes)  # type: ignore[type-var]
    except TypeError:  # pragma: no cover
        return sorted(all_outcomes, key=natural_key)

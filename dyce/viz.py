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
`#!python dyce.viz` provides optional, basic [Matplotlib](https://matplotlib.org/)-based visualization utilities.
Its requirements can be installed via the `viz` optional dependency group.

```sh
pip install 'dyce[viz]'
# or
uv sync --group viz
```

    <!-- BEGIN MONKEY PATCH --
    >>> from typing import Any
    >>> _: Any

      -- END MONKEY PATCH -->
"""

import operator
from collections.abc import Callable, Sequence
from fractions import Fraction
from itertools import accumulate, cycle
from typing import Literal, TypeVar, cast, overload

try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    from matplotlib.axes import Axes
    from matplotlib.colors import Colormap
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "dyce[viz] requires matplotlib; install with: pip install 'dyce[viz]'"
    ) from exc

from dyce import H
from dyce.lifecycle import experimental
from dyce.types import natural_key

__all__ = (
    "BurstFormatterT",
    "GraphTypeT",
    "format_outcome_name",
    "format_outcome_name_probability",
    "format_probability",
    "plot_bar",
    "plot_burst",
    "plot_line",
)

_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")

GraphTypeT = Literal["normal", "at_most", "at_least"]
r"""
Controls which variant of the distribution is plotted.

- `#!python "normal"`: raw probability for each outcome
- `#!python "at_most"`: cumulative probability `#!math P(X \le k)`
- `#!python "at_least"`: survival probability `#!math P(X \ge k)`
"""

BurstFormatterT = Callable[[_T, Fraction, H[_T]], str]
r"""
Callable type for burst-plot wedge labels.

Called as `#!python formatter(outcome, probability, histogram)`.
Return an empty string to suppress the label for that wedge.
"""

_DEFAULT_ALPHA: float = 0.75
_DEFAULT_CMAP: str = "RdYlGn_r"
_DEFAULT_CMAP_COMPARE: str = "RdYlBu_r"
_DEFAULT_MARKERS: str = "oX^v><dP"
_LABEL_LIM: Fraction = Fraction(1, 32)  # suppress burst labels below ~3.1%


@experimental
def format_outcome_name(
    outcome: _T,
    _prob: Fraction,
    _h: H[_T],
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with its outcome.
    If *outcome* has a `#!python .name` attribute (e.g. an `#!python Enum`), that is used; otherwise `#!python str(outcome)` is used.
    """
    return str(outcome.name) if hasattr(outcome, "name") else str(outcome)  # pyright: ignore[reportAttributeAccessIssue]


@experimental
def format_outcome_name_probability(
    outcome: _T,
    prob: Fraction,
    h: H[_T],
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with both its outcome and probability.
    If *outcome* has a `#!python .name` attribute (e.g. an `#!python Enum`), that is used; otherwise `#!python str(outcome)` is used.
    """
    name = format_outcome_name(outcome, prob, h)
    return f"{name}\n{format_probability(outcome, prob, h)}"


@experimental
def format_probability(
    _outcome: _T,
    prob: Fraction,
    _h: H[_T],
) -> str:
    r"""
    Burst-plot formatter that labels each wedge with its probability as a percentage.
    """
    return f"{float(prob):.2%}"


@experimental
def plot_bar(
    *hs: H,
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    graph_type: GraphTypeT = "normal",
    horizontal: bool = False,
    labels: Sequence[str] = (),
) -> Axes:
    r"""
    Plots a grouped bar chart of one or more histograms.

    Pass one or more [`H`][dyce.H] instances as positional arguments.
    Use *labels* to assign names to each histogram; unmatched histograms receive an empty label.
    When multiple histograms are provided, bars are interleaved side-by-side.

    *graph_type* controls which variant of the distribution is plotted (see `GraphTypeT`).
    When *horizontal* is `#!python True`, bars are drawn horizontally with outcomes on the y-axis and probabilities on the x-axis.

    If *ax* is `#!python None`, `#!python matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

    === "Vertical bars (default)"

            >>> from dyce import H
            >>> from dyce.viz import plot_bar
            >>> ax = plot_bar(
            ...     2 @ H(6),
            ...     H(12),
            ...     labels=["2d6", "d12"],
            ... )
            >>> _ = ax.set_title("2d6 vs. d12")
            >>> _ = ax.legend(loc="upper right")

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_bar_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_bar_light.svg">
            <img alt="Plot: 2d6 vs. d12, vertically and horizontally" src="../assets/plot_viz_plot_bar_light.svg">
        </picture>

    === "Horizontal bars (`horizontal=True`)"

            >>> from dyce import H
            >>> from dyce.viz import plot_bar
            >>> ax = plot_bar(
            ...     2 @ H(6),
            ...     H(12),
            ...     labels=["2d6", "d12"],
            ...     horizontal=True,
            ... )
            >>> _ = ax.set_title("2d6 vs. d12")
            >>> _ = ax.legend(loc="upper right")

        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_hbar_dark.svg">
            <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_hbar_light.svg">
            <img alt="Plot: 2d6 vs. d12, vertically and horizontally" src="../assets/plot_viz_plot_hbar_light.svg">
        </picture>

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->
    """
    hs_list = _labeled_hs(hs, labels)
    ax = _get_ax(ax)

    pct_formatter = ticker.PercentFormatter(xmax=1)
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
        try:
            lo, hi = min(unique_outcomes), max(unique_outcomes)
            if horizontal:
                ax.set_yticks(unique_outcomes)
                ax.set_ylim(lo - 1.0, hi + 1.0)
            else:
                ax.set_xticks(unique_outcomes)
                ax.set_xlim(lo - 1.0, hi + 1.0)
        except TypeError:  # pragma: no cover
            pass  # non-comparable outcomes: matplotlib handles categorical axes

    for i, (label, h) in enumerate(hs_list):
        outcomes, probs = _values_for_graph_type(h, graph_type)
        offsets = [o + (i + 0.5) * bar_width - 0.4 for o in outcomes]
        if horizontal:
            ax.barh(offsets, probs, height=bar_width, label=label or None, alpha=alpha)
        else:
            ax.bar(offsets, probs, width=bar_width, label=label or None, alpha=alpha)

    return ax


@overload
def plot_burst(
    h: H[_T1],
    compare: None = None,
    *,
    formatter: BurstFormatterT[_T1] = format_outcome_name,
    compare_formatter: None = None,
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap = _DEFAULT_CMAP,
    compare_cmap: str | Colormap = _DEFAULT_CMAP_COMPARE,
    title: str = "",
) -> Axes: ...
@overload
def plot_burst(
    h: H[_T1],
    compare: H[_T2],
    *,
    formatter: BurstFormatterT[_T1] = format_outcome_name,
    compare_formatter: BurstFormatterT[_T2],
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap = _DEFAULT_CMAP,
    compare_cmap: str | Colormap = _DEFAULT_CMAP_COMPARE,
    title: str = "",
) -> Axes: ...
@overload
def plot_burst(
    h: H[_T1],
    compare: H[_T2],
    *,
    formatter: BurstFormatterT[_T1 | _T2] = format_outcome_name,
    compare_formatter: None = None,
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap = _DEFAULT_CMAP,
    compare_cmap: str | Colormap = _DEFAULT_CMAP_COMPARE,
    title: str = "",
) -> Axes: ...
@experimental
def plot_burst(
    h: H[_T1],
    compare: H[_T2] | None = None,
    *,
    formatter: BurstFormatterT[_T1] | BurstFormatterT[_T1 | _T2] = format_outcome_name,
    compare_formatter: BurstFormatterT[_T2] | None = None,
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    cmap: str | Colormap = _DEFAULT_CMAP,
    compare_cmap: str | Colormap = _DEFAULT_CMAP_COMPARE,
    title: str = "",
) -> Axes:
    r"""
    Plots a dual concentric pie chart for one or two histograms.

    The inner ring represents *h* and the outer ring represents *compare*.
    When *compare* is `#!python None` (the default), both rings show the same histogram: the inner ring labels outcomes (via *formatter*) and the outer ring labels probabilities.
    When *compare* differs from *h*, both rings default to labelling outcomes — useful for comparing two related distributions side-by-side in a single visual.

    Wedge labels are suppressed when the probability is below `#!python Fraction(1, 32)` (~3.1%) to avoid clutter.

    *formatter* and *compare_formatter* are `BurstFormatterT` callables (see `format_outcome_name`, `format_probability`, `format_outcome_name_probability`).

    *cmap* / *compare_cmap* accept any matplotlib colormap name or instance.

    If *ax* is `#!python None`, `#!python matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

        >>> from dyce import H
        >>> from dyce.viz import plot_burst
        >>> from matplotlib import pyplot as plt
        >>> ax_d6 = plt.subplot2grid((1, 2), (0, 0))
        >>> _ = plot_burst(H(6), ax=ax_d6)
        >>> _ = ax_d6.set_title("d6")
        >>> ax_2d6_vs_d12 = plt.subplot2grid((1, 2), (0, 1))
        >>> _ = plot_burst(
        ...     2 @ H(6),
        ...     H(12),
        ...     ax=ax_2d6_vs_d12,
        ... )
        >>> _ = ax_2d6_vs_d12.set_title("2d6 vs. d12")

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->

    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_burst_dark.svg">
        <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_burst_light.svg">
        <img alt="Plot: 2d6 vs. d12" src="../assets/plot_viz_plot_burst_light.svg">
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

    inner_colors = _graph_colors(cmap, inner_probs, alpha)
    outer_colors = _graph_colors(compare_cmap, outer_probs, alpha)

    if title:
        ax.set_title(title, fontweight="bold", pad=24.0)

    ax.pie(
        outer_probs,
        labels=outer_labels,
        radius=1.0,
        labeldistance=1.15,
        startangle=90,
        colors=outer_colors,
        wedgeprops={"width": 0.8},
    )
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
    alpha: float = _DEFAULT_ALPHA,
    ax: Axes | None = None,
    graph_type: GraphTypeT = "normal",
    labels: Sequence[str] = (),
    markers: str = _DEFAULT_MARKERS,
) -> Axes:
    r"""
    Plots a line graph of one or more histograms.

    Pass one or more [`H`][dyce.H] instances as positional arguments.
    Use *labels* to assign names to each histogram; unmatched histograms receive an empty label.
    *markers* is a string whose characters are cycled across histograms (e.g. `#!python "oX^"` produces circle, cross, triangle, circle, …).

    *graph_type* controls which variant of the distribution is plotted (see `GraphTypeT`).

    If *ax* is `#!python None`, `#!python matplotlib.pyplot.gca()` is used.
    Returns the axes so the caller can further customise the plot.

    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)
    >>> import matplotlib as mpl
    >>> mpl.use("Agg")

      -- END MONKEY PATCH -->

        >>> from dyce import H
        >>> from dyce.viz import plot_line
        >>> ax = plot_line(
        ...     2 @ H(6),
        ...     H(12),
        ...     graph_type="at_most",
        ...     labels=["2d6", "d12"],
        ... )
        >>> _ = ax.set_title("2d6 vs. d12")
        >>> _ = ax.legend(loc="upper left")

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->

    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="../assets/plot_viz_plot_line_dark.svg">
        <source media="(prefers-color-scheme: light)" srcset="../assets/plot_viz_plot_line_light.svg">
        <img alt="Plot: d6 and 2d6 vs. d12" src="../assets/plot_viz_plot_line_light.svg">
    </picture>
    """
    hs_list = _labeled_hs(hs, labels)
    ax = _get_ax(ax)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))

    if not hs_list:
        return ax

    unique_outcomes = _sorted_outcomes(hs_list)

    if unique_outcomes:
        try:
            lo, hi = min(unique_outcomes), max(unique_outcomes)
            ax.set_xticks(unique_outcomes)
            ax.set_xlim(lo - 0.5, hi + 0.5)
        except TypeError:  # pragma: no cover
            pass  # non-comparable outcomes: matplotlib handles categorical axes

    markers_cycle_forever = cycle(markers or " ")
    for (label, h), marker in zip(hs_list, markers_cycle_forever, strict=False):
        outcomes, probs = _values_for_graph_type(h, graph_type)
        ax.plot(outcomes, probs, label=label or None, marker=marker, alpha=alpha)

    return ax


# ---- Helpers -------------------------------------------------------------------------


def _labeled_hs(
    hs: tuple[H[_T], ...],
    labels: Sequence[str],
) -> list[tuple[str, H[_T]]]:
    return [(labels[i] if i < len(labels) else "", h) for i, h in enumerate(hs)]


def _get_ax(ax: Axes | None) -> Axes:
    return ax if ax is not None else plt.gca()


def _values_for_graph_type(
    h: H[_T],
    graph_type: GraphTypeT,
) -> tuple[tuple[_T, ...], tuple[float, ...]]:
    if not h:
        return (), ()
    outcomes: tuple[_T, ...] = tuple(h)
    probs: tuple[float, ...] = tuple(float(p) for _, p in h.probability_items())
    if graph_type == "at_least":
        probs = tuple(accumulate(probs, operator.sub, initial=1.0))[:-1]
    elif graph_type == "at_most":
        probs = tuple(accumulate(probs, operator.add, initial=0.0))[1:]
    return outcomes, probs


def _graph_colors(
    cmap: str | Colormap,
    probs: tuple[float, ...],
    alpha: float,
) -> list[tuple[float, float, float, float]]:
    cm: Colormap = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap
    total = sum(probs)
    if not total:
        return []

    cumul = list(accumulate(probs, initial=0.0))
    midpoints = [(cumul[i] + cumul[i + 1]) / (2.0 * total) for i in range(len(probs))]
    return [(r, g, b, alpha) for r, g, b, _ in (cm(m) for m in midpoints)]


def _sorted_outcomes(hs_list: list[tuple[str, H[_T]]]) -> list[_T]:
    all_outcomes: set[_T] = {o for _, h in hs_list for o in h}
    try:
        return sorted(all_outcomes)  # type: ignore[type-var]
    except TypeError:  # pragma: no cover
        return sorted(all_outcomes, key=natural_key)

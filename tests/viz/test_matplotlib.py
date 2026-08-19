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

if True:  # so ruff won't complain imports are out-of-order, but still sort the others
    import pytest

    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg")

from collections.abc import Generator, Iterable
from typing import cast

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Wedge
from matplotlib.text import Annotation, Text

from dyce import H
from dyce.d import d0, d1, d4, d6, d8, d12, d20, h2d6, h2d10
from dyce.viz import GraphType
from dyce.viz.matplotlib import (
    format_outcome_name,
    format_outcome_name_probability,
    format_probability,
    plot_bar,
    plot_burst,
    plot_line,
    plot_ridge,
)

__all__ = ()


@pytest.fixture(autouse=True)
def _close_figures() -> Generator[None]:
    yield
    plt.close("all")


def _line_xdata_as_floats(line: Line2D) -> list[float]:
    return [float(x) for x in cast("Iterable[float]", line.get_xdata())]


def _line_ydata_as_floats(line: Line2D) -> list[float]:
    return [float(y) for y in cast("Iterable[float]", line.get_ydata())]


def _ridge_label_texts(ax: Axes) -> list[Text]:
    return [text for text in ax.texts if text.get_gid() == "ridge-label"]


def _ridge_peak_texts(ax: Axes) -> list[Annotation]:
    return [
        text
        for text in ax.texts
        if isinstance(text, Annotation) and text.get_gid() == "ridge-peak-label"
    ]


class TestFormatters:
    def test_format_outcome_name_int(self) -> None:
        from fractions import Fraction

        assert format_outcome_name(3, Fraction(1, 6), d6) == "3"

    def test_format_outcome_name_enum(self) -> None:
        from enum import Enum
        from fractions import Fraction

        class Face(Enum):
            HEADS = 1

        assert format_outcome_name(Face.HEADS, Fraction(1, 2), d1) == "HEADS"

    def test_format_probability(self) -> None:
        from fractions import Fraction

        result = format_probability(3, Fraction(1, 6), d6)
        assert "16.67%" in result

    def test_format_outcome_name_probability(self) -> None:
        labels = tuple(
            format_outcome_name_probability(outcome, probability, h2d6)
            for outcome, probability in h2d6.probability_items()
        )
        assert labels == (
            "2\n2.78%",
            "3\n5.56%",
            "4\n8.33%",
            "5\n11.11%",
            "6\n13.89%",
            "7\n16.67%",
            "8\n13.89%",
            "9\n11.11%",
            "10\n8.33%",
            "11\n5.56%",
            "12\n2.78%",
        )


class TestPlotBar:
    def test_no_args(self) -> None:
        ax = plot_bar()
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_empty_h(self) -> None:
        ax = plot_bar(d0)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_bar(d6, ax=supplied)
        assert returned is supplied

    def test_labeled_hs(self) -> None:
        labels = ["d8 + d12", "2d10"]
        ax = plot_bar(d8 + d12, h2d10, labels=labels)
        assert [c.get_label() for c in ax.containers] == labels

    def test_labeled_empty_hs(self) -> None:
        labels = ["empty 1", "empty 2"]
        ax = plot_bar(d0, d0, labels=labels)
        assert [c.get_label() for c in ax.containers] == labels

    def test_horizontal_labeled_hs(self) -> None:
        labels = ["d8 + d12", "2d10"]
        ax = plot_bar(d8 + d12, h2d10, labels=labels, horizontal=True)
        assert [c.get_label() for c in ax.containers] == labels

    def test_labels_partial(self) -> None:
        labels = ["d6"]
        ax = plot_bar(d6, d8, labels=labels)
        assert [c.get_label() for c in ax.containers][: len(labels)] == labels

    def test_graph_type_at_most(self) -> None:
        ax = plot_bar(d6, graph_type=GraphType.AT_MOST)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether this affected
        # _values_for_graph_type's behavior

    def test_horizontal_graph_type_at_least(self) -> None:
        ax = plot_bar(d6, graph_type=GraphType.AT_LEAST, horizontal=True)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether this affected
        # _values_for_graph_type's behavior


class TestPlotBurst:
    def test_empty_h(self) -> None:
        ax = plot_burst(d0)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_burst(d6, ax=supplied)
        assert returned is supplied

    def test_with_compare(self) -> None:
        ax = plot_burst(d8 + d12, h2d10)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for differing wedges

    def test_title(self) -> None:
        ax = plot_burst(d6, title="d6")
        assert ax.get_title() == "d6"

    def test_custom_formatter(self) -> None:
        ax = plot_burst(d6, formatter=format_probability)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether formatter was
        # actually used

    def test_custom_compare_formatter(self) -> None:
        ax = plot_burst(d6, d6, compare_formatter=format_outcome_name_probability)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether formatter was
        # actually used

    def test_plot_burst(self) -> None:
        mpl.use("agg")
        ax = plot_burst(h2d6)
        wedge_labels = [
            w.get_label() for w in ax.get_children() if isinstance(w, Wedge)
        ]
        assert len(wedge_labels) == 22
        assert wedge_labels == [
            "",  # 2 is hidden
            "5.56%",
            "8.33%",
            "11.11%",
            "13.89%",
            "16.67%",
            "13.89%",
            "11.11%",
            "8.33%",
            "5.56%",
            "",  # 12 is hidden
            "",  # 2 is hidden
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "",  # 12 is hidden
        ]

    def test_plot_burst_outer(self) -> None:
        mpl.use("agg")
        ax = plot_burst(h2d6, compare_formatter=format_outcome_name_probability)
        wedge_labels = [
            w.get_label() for w in ax.get_children() if isinstance(w, Wedge)
        ]
        assert len(wedge_labels) == 22
        assert wedge_labels == [
            "",  # 2 is hidden
            "3\n5.56%",
            "4\n8.33%",
            "5\n11.11%",
            "6\n13.89%",
            "7\n16.67%",
            "8\n13.89%",
            "9\n11.11%",
            "10\n8.33%",
            "11\n5.56%",
            "",  # 12 is hidden
            "",  # 2 is hidden
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "",  # 12 is hidden
        ]

    def test_str_outcomes(self) -> None:
        ax = plot_burst(H({"one": 1, "two": 1}))
        wedge_labels = [
            w.get_label() for w in ax.get_children() if isinstance(w, Wedge)
        ]
        assert wedge_labels == ["50.00%", "50.00%", "one", "two"]


class TestPlotLine:
    def test_no_args(self) -> None:
        ax = plot_line()
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_empty_h(self) -> None:
        ax = plot_line(d0)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_line(d6, ax=supplied)
        assert returned is supplied

    def test_labeled_hs(self) -> None:
        labels = ["d8 + d12", "2d10"]
        ax = plot_line(d8 + d12, h2d10, labels=labels)
        assert [ln.get_label() for ln in ax.lines] == labels

    def test_labeled_empty_hs(self) -> None:
        labels = ["empty 1", "empty 2"]
        ax = plot_line(d0, d0, labels=labels)
        assert [ln.get_label() for ln in ax.lines] == labels

    def test_graph_type_at_most(self) -> None:
        ax = plot_line(d6, graph_type=GraphType.AT_MOST)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether this affected
        # _values_for_graph_type's behavior

    def test_markers_cycled(self) -> None:
        ax = plot_line(d6, d6, d6, markers="ox")
        markers_used = [ln.get_marker() for ln in ax.lines]
        assert markers_used == ["o", "x", "o"]


class TestPlotRidge:
    def test_no_args(self) -> None:
        ax = plot_ridge()
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_empty_h(self) -> None:
        ax = plot_ridge(d0)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test for a blank graph

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_ridge(d6, ax=supplied)
        assert returned is supplied

    def test_labeled_empty_hs(self) -> None:
        labels = ["empty 1", "empty 2"]
        ax = plot_ridge(d0, d0, labels=labels)
        assert [t.get_text() for t in _ridge_label_texts(ax)] == labels

    def test_labels_are_drawn_in_the_plot_not_as_yticks(self) -> None:
        labels = ["2d6", "d12"]
        ax = plot_ridge(h2d6, d12, labels=labels)
        assert [t.get_text() for t in _ridge_label_texts(ax)] == labels
        assert list(ax.get_yticks()) == []

    def test_label_pills_are_inset_from_the_left_border(self) -> None:
        ax = plot_ridge(d6, labels=["d6"])
        figure = ax.get_figure()
        assert isinstance(figure, Figure)
        figure.tight_layout()
        figure.canvas.draw()
        label_patch = _ridge_label_texts(ax)[0].get_bbox_patch()
        assert label_patch is not None
        assert label_patch.get_window_extent().x0 > ax.bbox.x0

    def test_labels_partial(self) -> None:
        labels = ["2d6"]
        ax = plot_ridge(h2d6, d12, labels=labels)
        assert [t.get_text() for t in _ridge_label_texts(ax)] == [*labels, ""]

    def test_one_ridge_per_h(self) -> None:
        ax = plot_ridge(h2d6, d12, d6)
        assert len(ax.patches) == 3  # the filled ridges
        assert len(ax.lines) == 3  # the crest lines

    def test_empty_h_gets_no_ridge(self) -> None:
        labels = ["d6", "empty"]
        ax = plot_ridge(d6, d0, labels=labels)
        assert len(ax.patches) == 1  # no ridge for the empty histogram
        assert [t.get_text() for t in _ridge_label_texts(ax)] == labels

    def test_rows_stack_top_down_in_argument_order(self) -> None:
        labels = ["d6", "d8", "d12"]
        ax = plot_ridge(d6, d8, d12, labels=labels)
        ridge_labels = _ridge_label_texts(ax)
        assert [t.get_position()[1] for t in ridge_labels] == [2.0, 1.0, 0.0]
        assert [t.get_text() for t in ridge_labels] == labels

    def test_peak_labels_show_each_ridge_probability(self) -> None:
        ax = plot_ridge(d4, H({1: 1, 2: 3, 3: 2}), peak=0.5)
        peak_texts = _ridge_peak_texts(ax)
        assert [text.get_text() for text in peak_texts] == ["25%", "50%"]
        assert [text.xy for text in peak_texts] == [
            pytest.approx((3, 2.2)),
            pytest.approx((2, 2.4)),
        ]
        assert [text.get_position() for text in peak_texts] == [(-8.0, 0.0), (8.0, 0.0)]
        assert all(text.arrow_patch is not None for text in peak_texts)

    def test_peak_labels_can_be_hidden(self) -> None:
        ax = plot_ridge(d4, show_peak_labels=False)
        assert all(text.get_gid() != "ridge-peak-label" for text in ax.texts)

    def test_each_ridge_contains_only_its_own_outcomes(self) -> None:
        ax = plot_ridge(d6, d12)
        assert _line_xdata_as_floats(ax.lines[0]) == [float(outcome) for outcome in d6]
        assert _line_xdata_as_floats(ax.lines[1]) == [float(outcome) for outcome in d12]

    def test_heights_share_one_scale(self) -> None:
        ax = plot_ridge(
            h2d6,
            h2d6 + 10,  # different outcomes, same peak probability
            d12,  # half of peak probability
        )
        peaks = [
            max(_line_ydata_as_floats(line)) - baseline
            for line, baseline in zip(ax.lines, (2.0, 1.0, 0.0), strict=True)
        ]
        assert peaks[0] == pytest.approx(peaks[1])
        assert peaks[0] == pytest.approx(peaks[2] * 2)

    def test_peak_defaults_to_the_tallest_probability(self) -> None:
        max_prob = max(
            float(probability)
            for h in (d4, d20)
            for _, probability in h.probability_items()
        )
        _, provided_peak_ax = plt.subplots()
        _, default_computed_peak_ax = plt.subplots()
        plot_ridge(d4, d20, peak=max_prob, ax=provided_peak_ax)
        plot_ridge(d4, d20, ax=default_computed_peak_ax)
        assert [_line_ydata_as_floats(line) for line in provided_peak_ax.lines] == [
            _line_ydata_as_floats(line) for line in default_computed_peak_ax.lines
        ]

    def test_peak_below_the_tallest_probability_exceeds_overlap(self) -> None:
        max_prob = max(float(probability) for _, probability in d4.probability_items())
        scalar = 5
        overlap = 1.0
        ax = plot_ridge(d4, peak=max_prob / scalar, overlap=overlap)
        assert max(_line_ydata_as_floats(ax.lines[0])) == pytest.approx(
            overlap * scalar
        )

    def test_explicit_peak_normalizes_scale_across_axes(self) -> None:
        max_prob = max(
            float(probability)
            for h in (d4, d20)
            for _, probability in h.probability_items()
        )
        _, d4_ax = plt.subplots()
        _, d20_ax = plt.subplots()
        plot_ridge(d4, peak=max_prob, overlap=2.0, ax=d4_ax)
        plot_ridge(d20, peak=max_prob, overlap=2.0, ax=d20_ax)
        assert max(_line_ydata_as_floats(d4_ax.lines[0])) == pytest.approx(
            2.0  # 25% / 25% * overlap
        )
        assert max(_line_ydata_as_floats(d20_ax.lines[0])) == pytest.approx(
            0.4  # 5% / 25% * overlap = 0.4
        )

    def test_overlap_scales_ridge_height(self) -> None:
        _, taller_ax = plt.subplots()
        _, shorter_ax = plt.subplots()
        plot_ridge(d6, d8, overlap=1.0, ax=taller_ax)
        plot_ridge(d6, d8, overlap=0.0, ax=shorter_ax)
        assert max(_line_ydata_as_floats(taller_ax.lines[0])) > max(
            _line_ydata_as_floats(shorter_ax.lines[0])
        )

    def test_graph_type_at_most(self) -> None:
        ax = plot_ridge(d6, graph_type=GraphType.AT_MOST)
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether this affected
        # _values_for_graph_type's behavior

    def test_cmap(self) -> None:
        ax = plot_ridge(d6, d8, cmap="plasma")
        assert ax is not None
        # TODO(posita): # ruff: ignore[missing-todo-link] - test whether the color map
        # was used

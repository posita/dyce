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

import pytest

from dyce import H
from dyce.d import d0, d4, d6, d8, d20, h2d6
from dyce.viz_plotly import (
    GraphType,
    PlotSpec,
    bar_spec,
    figure_from_spec,
    line_spec,
    ridge_spec,
)

__all__ = ()


def _traces(spec: PlotSpec, role: str) -> list[dict]:
    return [trace for trace in spec.data if trace["meta"]["role"] == role]


class TestBarSpec:
    def test_vertical_bar_data(self) -> None:
        trace = bar_spec(d4, labels=["d4"], precision=3).data[0]
        assert trace["x"] == [1, 2, 3, 4]
        assert trace["y"] == [pytest.approx(25.0)] * 4
        assert trace["customdata"] == trace["y"]
        assert trace["orientation"] == "v"
        assert "%{x}" in trace["hovertemplate"]
        assert "customdata:.3f" in trace["hovertemplate"]

    def test_horizontal_bar_data(self) -> None:
        spec = bar_spec(d4, horizontal=True)
        trace = spec.data[0]
        assert trace["x"] == [pytest.approx(25.0)] * 4
        assert trace["y"] == [1, 2, 3, 4]
        assert trace["orientation"] == "h"
        assert "%{y}" in trace["hovertemplate"]
        assert spec.layout["xaxis"]["title"]["text"] == "Probability (%)"

    @pytest.mark.parametrize(
        ("graph_type", "expected"),
        [
            (GraphType.AT_MOST, [25.0, 50.0, 75.0, 100.0]),
            (GraphType.AT_LEAST, [100.0, 75.0, 50.0, 25.0]),
        ],
    )
    def test_graph_type(self, graph_type: GraphType, expected: list[float]) -> None:
        assert bar_spec(d4, graph_type=graph_type).data[0]["y"] == pytest.approx(
            expected
        )

    def test_multiple_histograms_are_grouped_and_labeled(self) -> None:
        spec = bar_spec(d4, d6, labels=["d4", "d6"])
        assert spec.layout["barmode"] == "group"
        assert spec.layout["showlegend"] is True
        assert [trace["name"] for trace in spec.data] == ["d4", "d6"]

    def test_colors_cycle_and_metadata_identifies_series(self) -> None:
        spec = bar_spec(d4, d6, colors=["#123456"])
        assert [trace["marker"]["color"] for trace in spec.data] == [
            "#123456",
            "#123456",
        ]
        assert [trace["meta"] for trace in spec.data] == [
            {"series": 0, "role": "bar"},
            {"series": 1, "role": "bar"},
        ]

    def test_max_percent_sets_probability_range(self) -> None:
        assert bar_spec(d6, max_percent=42.0).layout["yaxis"]["range"] == [
            0.0,
            42.0,
        ]

    def test_empty_inputs(self) -> None:
        assert bar_spec().data == []
        assert bar_spec(d0).data[0]["x"] == []


class TestLineSpec:
    def test_one_trace_per_histogram(self) -> None:
        spec = line_spec(d4, d6, labels=["d4", "d6"])
        assert len(spec.data) == 2
        assert spec.data[0]["x"] == [1, 2, 3, 4]
        assert spec.data[0]["y"] == [pytest.approx(25.0)] * 4
        assert [trace["name"] for trace in spec.data] == ["d4", "d6"]
        assert spec.layout["showlegend"] is True

    def test_precision_and_metadata(self) -> None:
        trace = line_spec(d6, precision=4).data[0]
        assert "y:.4f" in trace["hovertemplate"]
        assert trace["meta"] == {"series": 0, "role": "line"}

    @pytest.mark.parametrize(
        ("graph_type", "expected"),
        [
            (GraphType.AT_MOST, [25.0, 50.0, 75.0, 100.0]),
            (GraphType.AT_LEAST, [100.0, 75.0, 50.0, 25.0]),
        ],
    )
    def test_graph_type(self, graph_type: GraphType, expected: list[float]) -> None:
        assert line_spec(d4, graph_type=graph_type).data[0]["y"] == pytest.approx(
            expected
        )

    def test_colors_cycle_to_line_and_marker(self) -> None:
        spec = line_spec(d4, d6, colors=["#123456"])
        for trace in spec.data:
            assert trace["line"]["color"] == "#123456"
            assert trace["marker"]["color"] == "#123456"

    def test_without_colors_carries_no_hue(self) -> None:
        trace = line_spec(d6).data[0]
        assert "line" not in trace
        assert "color" not in trace["marker"]

    def test_empty_inputs(self) -> None:
        assert line_spec().data == []
        assert line_spec(d0).data[0]["x"] == []


class TestRidgeSpec:
    def test_two_traces_per_h(self) -> None:
        spec = ridge_spec(h2d6, d6, d8)
        assert len(spec.data) == 6
        assert [trace["meta"] for trace in spec.data] == [
            {"ridge": 0, "role": "fill"},
            {"ridge": 0, "role": "line"},
            {"ridge": 1, "role": "fill"},
            {"ridge": 1, "role": "line"},
            {"ridge": 2, "role": "fill"},
            {"ridge": 2, "role": "line"},
        ]

    def test_no_args(self) -> None:
        spec = ridge_spec()
        assert spec.data == []
        assert spec.layout["annotations"] == []

    def test_empty_h(self) -> None:
        # No outcomes to seat a fill on, so both traces are empty but present.
        spec = ridge_spec(d0)
        assert [trace["x"] for trace in spec.data] == [[], []]

    def test_each_ridge_covers_only_its_own_outcomes(self) -> None:
        spec = ridge_spec(d6, d20)
        lines = _traces(spec, "line")
        assert lines[0]["x"] == list(d6.outcomes())
        assert lines[1]["x"] == list(d20.outcomes())

    def test_fill_has_a_foot_outside_each_end(self) -> None:
        # The fill seats on the baseline just past the real outcomes, so it
        # tapers rather than ending in a hard vertical edge.
        spec = ridge_spec(d6)
        fill, line = spec.data
        assert fill["x"][0] == pytest.approx(min(line["x"]) - 0.1)
        assert fill["x"][-1] == pytest.approx(max(line["x"]) + 0.1)
        # both feet on the baseline
        assert fill["y"][0] == pytest.approx(0.0)
        assert fill["y"][-1] == pytest.approx(0.0)

    def test_single_outcome_ridge_is_a_triangle(self) -> None:
        # A lone spike would otherwise be a zero-width sliver.
        spec = ridge_spec(H({7: 1}))
        fill = _traces(spec, "fill")[0]
        assert len(fill["x"]) == 3  # foot, the outcome, foot
        assert fill["x"][0] != fill["x"][-1]

    def test_rows_stack_top_down_in_argument_order(self) -> None:
        spec = ridge_spec(d6, d8, d20)
        assert [note["y"] for note in spec.layout["annotations"]] == [2.0, 1.0, 0.0]

    def test_labels_become_annotations(self) -> None:
        spec = ridge_spec(h2d6, d6, labels=["2d6", "d6"])
        assert [note["text"] for note in spec.layout["annotations"]] == ["2d6", "d6"]
        assert spec.layout["yaxis"]["showticklabels"] is False

    def test_labels_partial(self) -> None:
        spec = ridge_spec(h2d6, d6, labels=["2d6"])
        assert [note["text"] for note in spec.layout["annotations"]] == ["2d6", ""]

    def test_labels_have_configurable_pill_backgrounds(self) -> None:
        spec = ridge_spec(
            d6,
            labels=["d6"],
            label_bgcolor="rgba(255,255,255,0.72)",
        )
        annotation = spec.layout["annotations"][0]
        assert annotation["borderpad"] == 2
        assert annotation["bgcolor"] == "rgba(255,255,255,0.72)"

    def test_label_background_color_is_optional(self) -> None:
        annotation = ridge_spec(d6).layout["annotations"][0]
        assert annotation["borderpad"] == 2
        assert "bgcolor" not in annotation

    def test_customdata_carries_true_percentages(self) -> None:
        # The plotted y is offset and scaled, so tooltips read customdata.
        spec = ridge_spec(d4)
        line = _traces(spec, "line")[0]
        assert line["customdata"] == [pytest.approx(25.0)] * 4
        assert line["y"] != line["customdata"]

    @pytest.mark.parametrize(
        ("graph_type", "expected"),
        [
            (GraphType.AT_MOST, [25.0, 50.0, 75.0, 100.0]),
            (GraphType.AT_LEAST, [100.0, 75.0, 50.0, 25.0]),
        ],
    )
    def test_graph_type(self, graph_type: GraphType, expected: list[float]) -> None:
        line = _traces(ridge_spec(d4, graph_type=graph_type), "line")[0]
        assert line["customdata"] == pytest.approx(expected)

    def test_colors_give_each_ridge_one_hue(self) -> None:
        spec = ridge_spec(d6, d8, colors=["#1f77b4", "#d62728"])
        assert _traces(spec, "fill")[0]["fillcolor"] == "rgba(31,119,180,0.4)"
        assert _traces(spec, "line")[0]["line"]["color"] == "#1f77b4"
        assert _traces(spec, "fill")[1]["fillcolor"] == "rgba(214,39,40,0.4)"

    def test_colors_cycle(self) -> None:
        spec = ridge_spec(d4, d6, d8, colors=["#1f77b4"])
        assert {trace["fillcolor"] for trace in _traces(spec, "fill")} == {
            "rgba(31,119,180,0.4)"
        }

    def test_colors_short_hex(self) -> None:
        spec = ridge_spec(d6, colors=["#08f"])
        assert _traces(spec, "fill")[0]["fillcolor"] == "rgba(0,136,255,0.4)"

    def test_colors_non_hex_passes_through(self) -> None:
        spec = ridge_spec(d6, colors=["rebeccapurple"])
        assert _traces(spec, "fill")[0]["fillcolor"] == "rebeccapurple"

    def test_without_colors_traces_carry_none(self) -> None:
        spec = ridge_spec(d6)
        assert "fillcolor" not in _traces(spec, "fill")[0]
        assert "line" not in _traces(spec, "line")[0]

    def test_heights_share_one_scale(self) -> None:
        # d6 and h2d6 peak at the same probability, so their ridges reach the
        # same height above their respective baselines.
        spec = ridge_spec(d6, h2d6)
        lines = _traces(spec, "line")
        assert max(lines[0]["y"]) - 1.0 == pytest.approx(max(lines[1]["y"]) - 0.0)

    def test_peak_puts_separate_specs_on_one_scale(self) -> None:
        # Pass the largest percentage across several figures so ridges stay
        # comparable between subplots.
        d4_spec = ridge_spec(d4, peak=25.0, overlap=2.0)
        d20_spec = ridge_spec(d20, peak=25.0, overlap=2.0)
        assert max(_traces(d4_spec, "line")[0]["y"]) == pytest.approx(2.0)
        assert max(_traces(d20_spec, "line")[0]["y"]) == pytest.approx(0.4)

    def test_peak_defaults_to_the_tallest_percentage(self) -> None:
        assert ridge_spec(d4, d20, peak=25.0) == ridge_spec(d4, d20)

    def test_overlap_sets_how_many_rows_tall_a_peak_stands(self) -> None:
        spec = ridge_spec(d6, overlap=1.0)
        assert max(_traces(spec, "line")[0]["y"]) == pytest.approx(1.0)

    def test_y_range_pads_the_stack(self) -> None:
        spec = ridge_spec(d6, d8, overlap=2.0)
        assert spec.layout["yaxis"]["range"] == [-0.5, 1.0 + 2.0 + 0.5]

    def test_precision_reaches_the_tooltip(self) -> None:
        spec = ridge_spec(d6, precision=4)
        assert "customdata:.4f" in _traces(spec, "line")[0]["hovertemplate"]

    def test_fill_skips_hover_so_each_ridge_shows_one_tooltip(self) -> None:
        spec = ridge_spec(d6, d8)
        assert all(trace["hoverinfo"] == "skip" for trace in _traces(spec, "fill"))
        assert spec.layout["hovermode"] == "x"

    def test_spec_is_json_serializable(self) -> None:
        # The playground hands this across a worker boundary, so it has to
        # survive a round trip with no Plotly or numpy types in it.
        import json

        spec = ridge_spec(h2d6, d6, labels=["2d6", "d6"], colors=["#1f77b4"])
        assert json.loads(json.dumps(spec.as_dict())) == spec.as_dict()


class TestPlotSpec:
    def test_graph_type_is_shared_with_matplotlib_api(self) -> None:
        from dyce.viz import GraphType as MatplotlibGraphType

        assert GraphType is MatplotlibGraphType

    def test_default_config_is_not_shared(self) -> None:
        first = ridge_spec(d6)
        second = ridge_spec(d6)
        first.config["responsive"] = False
        assert second.config["responsive"] is True

    def test_figure_dict_excludes_renderer_config(self) -> None:
        spec = ridge_spec(d6)
        assert spec.figure_dict() == {"data": spec.data, "layout": spec.layout}

    def test_figure_from_spec(self) -> None:
        spec = ridge_spec(d6)
        figure = figure_from_spec(spec)
        assert len(figure.data) == len(spec.data)
        assert figure.layout.hovermode == spec.layout["hovermode"]

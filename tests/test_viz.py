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

import warnings
from collections.abc import Generator

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from dyce import H  # noqa: E402
from dyce.viz import (  # noqa: E402
    format_outcome_name,
    format_outcome_name_probability,
    format_probability,
    plot_bar,
    plot_burst,
    plot_line,
)

__all__ = ()


@pytest.fixture(autouse=True)
def _suppress_experimental() -> None:
    warnings.filterwarnings("ignore", category=UserWarning)


@pytest.fixture(autouse=True)
def _close_figures() -> Generator[None, None, None]:
    yield
    plt.close("all")


class TestFormatters:
    def test_format_outcome_name_int(self) -> None:
        from fractions import Fraction

        assert format_outcome_name(3, Fraction(1, 6), H(6)) == "3"

    def test_format_outcome_name_enum(self) -> None:
        from enum import Enum
        from fractions import Fraction

        class Face(Enum):
            HEADS = 1

        assert format_outcome_name(Face.HEADS, Fraction(1, 2), H({1: 1})) == "HEADS"

    def test_format_probability(self) -> None:
        from fractions import Fraction

        result = format_probability(3, Fraction(1, 6), H(6))
        assert "16.67%" in result

    def test_format_outcome_name_probability(self) -> None:
        from fractions import Fraction

        result = format_outcome_name_probability(3, Fraction(1, 6), H(6))
        assert "3" in result
        assert "16.67%" in result


class TestPlotBar:
    def test_single_h_returns_axes(self) -> None:
        ax = plot_bar(H(6))
        assert ax is not None

    def test_labeled_hs(self) -> None:
        ax = plot_bar(2 @ H(6), H(12), labels=["2d6", "d12"])
        # one container (bar group) per histogram
        assert len(ax.containers) == 2

    def test_empty_h(self) -> None:
        ax = plot_bar(H({}))
        assert ax is not None

    def test_no_args(self) -> None:
        ax = plot_bar()
        assert ax is not None

    def test_graph_type_at_most(self) -> None:
        ax = plot_bar(H(6), graph_type="at_most")
        assert ax is not None

    def test_graph_type_at_least(self) -> None:
        ax = plot_bar(H(6), graph_type="at_least")
        assert ax is not None

    def test_horizontal(self) -> None:
        ax = plot_bar(H(6), horizontal=True)
        assert ax is not None

    def test_horizontal_labeled(self) -> None:
        ax = plot_bar(H(6), H(8), labels=["d6", "d8"], horizontal=True)
        assert ax is not None

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_bar(H(6), ax=supplied)
        assert returned is supplied

    def test_bool_outcomes(self) -> None:
        ax = plot_bar(H(6).ge(4))
        assert ax is not None

    def test_labels_partial(self) -> None:
        # labels shorter than hs — extra histograms get empty label
        ax = plot_bar(H(6), H(8), labels=["d6"])
        assert len(ax.containers) == 2


class TestPlotBurst:
    def test_single_h_returns_axes(self) -> None:
        ax = plot_burst(H(6))
        assert ax is not None

    def test_with_compare(self) -> None:
        ax = plot_burst(2 @ H(6), H(6))
        assert ax is not None

    def test_empty_h(self) -> None:
        ax = plot_burst(H({}))
        assert ax is not None

    def test_title(self) -> None:
        ax = plot_burst(H(6), title="d6")
        assert ax.get_title() == "d6"

    def test_custom_formatter(self) -> None:
        ax = plot_burst(H(6), formatter=format_probability)
        assert ax is not None

    def test_custom_compare_formatter(self) -> None:
        ax = plot_burst(H(6), H(6), compare_formatter=format_outcome_name_probability)
        assert ax is not None

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_burst(H(6), ax=supplied)
        assert returned is supplied


class TestPlotLine:
    def test_single_h_returns_axes(self) -> None:
        ax = plot_line(H(6))
        assert ax is not None

    def test_labeled_hs(self) -> None:
        ax = plot_line(2 @ H(6), H(12), labels=["2d6", "d12"])
        assert len(ax.lines) == 2

    def test_empty_h(self) -> None:
        ax = plot_line(H({}))
        assert ax is not None

    def test_graph_type_at_most(self) -> None:
        ax = plot_line(H(6), graph_type="at_most")
        assert ax is not None

    def test_markers_cycled(self) -> None:
        ax = plot_line(H(6), H(6), H(6), markers="ox")
        markers_used = [line.get_marker() for line in ax.lines]
        assert markers_used == ["o", "x", "o"]

    def test_respects_provided_ax(self) -> None:
        _, supplied = plt.subplots()

        returned = plot_line(H(6), ax=supplied)
        assert returned is supplied

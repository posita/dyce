# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import fractions
import random

import pytest

from dyce import H, viz

__all__ = ()


# ---- Tests ---------------------------------------------------------------------------


def test_alphasize() -> None:
    colors = [
        [r / 10, g / 10, b / 10, random.random()]
        for r, g, b in zip(*(range(0, 10, 2), range(3, 9), range(10, 0, -2)))
    ]
    actual_colors = viz.alphasize(colors, 0.8)
    expected_colors = [(r, g, b, 0.8) for r, g, b, _ in colors]
    assert actual_colors == expected_colors
    assert viz.alphasize(colors, -1.0) == colors


def test_display_burst() -> None:
    patches = pytest.importorskip("matplotlib.patches", reason="requires matplotlib")
    pyplot = pytest.importorskip("matplotlib.pyplot", reason="requires matplotlib")

    _, ax = pyplot.subplots()
    d6_2 = 2 @ H(6)
    viz.display_burst(ax, d6_2)
    wedge_labels = [
        w.get_label() for w in ax.get_children()[:22] if isinstance(w, patches.Wedge)
    ]
    assert len(wedge_labels) == 22
    assert wedge_labels == [
        "2.78%",
        "5.56%",
        "8.33%",
        "11.11%",
        "13.89%",
        "16.67%",
        "13.89%",
        "11.11%",
        "8.33%",
        "5.56%",
        "2.78%",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
    ]


def test_display_burst_outer() -> None:
    patches = pytest.importorskip("matplotlib.patches", reason="requires matplotlib")
    pyplot = pytest.importorskip("matplotlib.pyplot", reason="requires matplotlib")

    _, ax = pyplot.subplots()
    d6_2 = 2 @ H(6)
    viz.display_burst(ax, d6_2, viz.labels_cumulative(d6_2))
    wedge_labels = [
        w.get_label() for w in ax.get_children()[:22] if isinstance(w, patches.Wedge)
    ]
    assert len(wedge_labels) == 22
    assert wedge_labels == [
        "2 2.78%; ≥2.78%; ≤100.00%",
        "3 5.56%; ≥8.33%; ≤97.22%",
        "4 8.33%; ≥16.67%; ≤91.67%",
        "5 11.11%; ≥27.78%; ≤83.33%",
        "6 13.89%; ≥41.67%; ≤72.22%",
        "7 16.67%; ≥58.33%; ≤58.33%",
        "8 13.89%; ≥72.22%; ≤41.67%",
        "9 11.11%; ≥83.33%; ≤27.78%",
        "10 8.33%; ≥91.67%; ≤16.67%",
        "11 5.56%; ≥97.22%; ≤8.33%",
        "12 2.78%; ≥100.00%; ≤2.78%",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
    ]


def test_labels_cumulative() -> None:
    labels = tuple(viz.labels_cumulative(2 @ H(6)))
    assert labels == (
        ("2 2.78%; ≥2.78%; ≤100.00%", fractions.Fraction(1, 36)),
        ("3 5.56%; ≥8.33%; ≤97.22%", fractions.Fraction(1, 18)),
        ("4 8.33%; ≥16.67%; ≤91.67%", fractions.Fraction(1, 12)),
        ("5 11.11%; ≥27.78%; ≤83.33%", fractions.Fraction(1, 9)),
        ("6 13.89%; ≥41.67%; ≤72.22%", fractions.Fraction(5, 36)),
        ("7 16.67%; ≥58.33%; ≤58.33%", fractions.Fraction(1, 6)),
        ("8 13.89%; ≥72.22%; ≤41.67%", fractions.Fraction(5, 36)),
        ("9 11.11%; ≥83.33%; ≤27.78%", fractions.Fraction(1, 9)),
        ("10 8.33%; ≥91.67%; ≤16.67%", fractions.Fraction(1, 12)),
        ("11 5.56%; ≥97.22%; ≤8.33%", fractions.Fraction(1, 18)),
        ("12 2.78%; ≥100.00%; ≤2.78%", fractions.Fraction(1, 36)),
    )

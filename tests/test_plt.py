# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import generator_stop

import pytest
import random
import warnings

from dyce.h import H
from dyce import plt as dyce_plt

try:
    import matplotlib.patches
except ImportError:
    warnings.warn("matplotlib not found; {} some tests disabled".format(__name__))
    matplotlib = None  # noqa: F811

__all__ = ()


# ---- Classes -------------------------------------------------------------------------


class TestPlt:
    def test_alphasize(self):
        colors = [
            (r / 10, g / 10, b / 10, random.random())
            for r, g, b in zip(*(range(0, 10, 2), range(3, 9), range(10, 0, -2)))
        ]
        actual_colors = dyce_plt.alphasize(colors, 0.8)
        expected_colors = [(r, g, b, 0.8) for r, g, b, _ in colors]
        assert actual_colors == expected_colors
        assert dyce_plt.alphasize(colors, -1.0) == colors

    @pytest.mark.skipif(matplotlib is None, reason="requires matplotlib")
    def test_display_burst(self):
        _, ax = dyce_plt.matplotlib.pyplot.subplots()
        d6_2 = 2 @ H(6)
        dyce_plt.display_burst(ax, d6_2)
        wedge_labels = [
            w.get_label()
            for w in ax.get_children()[:22]
            if isinstance(w, matplotlib.patches.Wedge)
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

    @pytest.mark.skipif(matplotlib is None, reason="requires matplotlib")
    def test_display_burst_outer(self):
        _, ax = dyce_plt.matplotlib.pyplot.subplots()
        d6_2 = 2 @ H(6)
        dyce_plt.display_burst(ax, d6_2, dyce_plt.labels_cumulative(d6_2))
        wedge_labels = [
            w.get_label()
            for w in ax.get_children()[:22]
            if isinstance(w, matplotlib.patches.Wedge)
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

    def test_labels_cumulative(self):
        labels = tuple(dyce_plt.labels_cumulative(2 @ H(6)))
        assert labels == (
            ("2 2.78%; ≥2.78%; ≤100.00%", 0.027777777777777776),
            ("3 5.56%; ≥8.33%; ≤97.22%", 0.05555555555555555),
            ("4 8.33%; ≥16.67%; ≤91.67%", 0.08333333333333333),
            ("5 11.11%; ≥27.78%; ≤83.33%", 0.1111111111111111),
            ("6 13.89%; ≥41.67%; ≤72.22%", 0.1388888888888889),
            ("7 16.67%; ≥58.33%; ≤58.33%", 0.16666666666666666),
            ("8 13.89%; ≥72.22%; ≤41.67%", 0.1388888888888889),
            ("9 11.11%; ≥83.33%; ≤27.78%", 0.1111111111111111),
            ("10 8.33%; ≥91.67%; ≤16.67%", 0.08333333333333333),
            ("11 5.56%; ≥97.22%; ≤8.33%", 0.05555555555555555),
            ("12 2.78%; ≥100.00%; ≤2.78%", 0.027777777777777776),
        )

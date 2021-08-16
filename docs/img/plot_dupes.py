# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H, P
from dyce.viz import plot_burst


def do_it(style: str) -> None:
    def dupes(p: P):
        for roll, count in p.rolls_with_counts():
            dupes = 0
            for i in range(1, len(roll)):
                if roll[i] == roll[i - 1]:
                    dupes += 1
            yield dupes, count

    res = H(dupes(8 @ P(10)))

    plot_burst(
        res,
        # Should match the corresponding img[alt] text
        desc=r"Chances of rolling $n$ duplicates in 8d10",
        text_color="white" if style == "dark" else "black",
    )

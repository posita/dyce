# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H
from dyce.viz import plot_burst


def do_it(style: str) -> None:
    text_color = "white" if style == "dark" else "black"
    d20 = H(20)
    plot_burst(
        d20,
        outer=(
            ("crit. fail.", d20.le(1)[1]),
            ("fail.", d20.within(2, 14)[0]),
            ("succ.", d20.within(15, 19)[0]),
            ("crit. succ.", d20.ge(20)[1]),
        ),
        inner_color="RdYlBu_r",
        text_color=text_color,
    )

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
    df_4 = 4 @ H((-1, 0, 1))
    d6_2 = 2 @ H(6)
    plot_burst(df_4, d6_2, alpha=0.9, text_color=text_color)

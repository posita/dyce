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
    plot_burst(2 @ H(6), text_color=text_color)

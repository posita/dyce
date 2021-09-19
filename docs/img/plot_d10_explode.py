# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H, P


def do_it(_: str) -> None:
    import matplotlib.pyplot

    for depth in range(6):
        res = (10 @ P(H(10).explode(max_depth=depth))).h(slice(-3, None))
        matplotlib.pyplot.plot(
            *res.distribution_xy(),
            marker=".",
            label=f"{depth} rerolls",
        )

    matplotlib.pyplot.legend()
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title("Modeling taking the three highest of ten exploding d10s")

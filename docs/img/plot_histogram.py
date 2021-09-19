# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from dyce import H


def do_it(_: str) -> None:
    import matplotlib.pyplot

    outcomes, probabilities = (2 @ H(6)).distribution_xy()
    matplotlib.pyplot.bar([str(v) for v in outcomes], probabilities)
    # Should match the corresponding img[alt] text
    matplotlib.pyplot.title("Distribution for 2d6")

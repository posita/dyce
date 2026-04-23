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

r"""
`#!python dyce` revolves around two core primitives.
[`H` objects][dyce.h.H] are histograms (outcomes or individual dice).
[`P` objects][dyce.p.P] are collections of histograms (pools).

Additionally, `dyce` provides [`expand`][dyce.expand], which is useful for substitutions, explosions, and modeling arbitrarily complex computations with dependent terms.
It also provides [`explode_n`][dyce.explode_n] as a convenient shorthand.
<!-- The [`dyce.r`](dyce.r.md) package provides scalars, histograms, pools, operators, etc. for assembling reusable roller trees. -->
"""

from importlib.metadata import PackageNotFoundError, version

from .evaluation import HResult, PResult, TruncationWarning, expand, explode_n
from .h import H, HableT
from .hable import HableOpsMixin
from .p import P, RollCountT, RollProbT, RollT

__all__ = (
    "H",
    "HResult",
    "HableOpsMixin",
    "HableT",
    "P",
    "PResult",
    "RollCountT",
    "RollProbT",
    "RollT",
    "TruncationWarning",
    "expand",
    "explode_n",
)

try:
    __version__: str = version("dyce")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

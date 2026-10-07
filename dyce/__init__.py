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
- [`H`][dyce.H] represents possible outcomes and their weights as integer counts.
  A fair, six-sided die can be represented as `H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})`, or the shorthand `H(6)`.
  The sum of three six-sided dice can be represented as `3 @ H(6)`.
- [`P`][dyce.P] represents an ordered sequence of histograms.
  A pool of three separate six-sided dice can be represented as `3 @ P(H(6))`, or the shorthand `3 @ P(6)`.
  `P`s keep each die separate, so you can select any die or group of dice and calculate the distribution of their summed results.
- [`P.survey`][dyce.P.survey] and [`expand`][dyce.expand] are experimental interfaces useful for modeling mechanics where the outcome of one die affects how others are rolled.
  Examples include: exploding dice, conditional re-rolls, or damage that depends on whether an attack hits.
    - [`explode_n`][dyce.explode_n] is provided as a convenient shorthand.
"""

if True:
    # This needs to come first. Placing it in this block keeps ruff from complaining
    # imports are out-of-order, while still keeping the others sorted.
    from .types import beartype_this_package

    beartype_this_package()

from importlib.metadata import PackageNotFoundError, version

from .evaluation import HResult, PResult, TruncationWarning, expand, explode_n
from .h import H, HableOpsMixin, HableT, quantize_hs
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
    "quantize_hs",
)

try:
    __version__: str = version("dyce")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

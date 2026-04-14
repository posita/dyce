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
Lots of common dice and combinations: d1 through d20, d24, d30, d60, d100, and d00
as well as two and three of d1 through d20. as both [`H`][dyce.H] and [`P`][dyce.P]
objects. For example, a twenty-sided die in [`H`][dyce.H] form is `#!python d20`. In
[`P`][dyce.P] form, it is `#!python pd20`. `#!python 2 @ d10` in [`H`][dyce.H] form is
either `#!python d10_2` or `#!python h2d10`. In [`P`][dyce.P] form, it is is either
`#!python pd10_2` or `#!python p2d10`.

    >>> from dyce.d import d6, d6_3, h3d6, pd6, pd6_3, p3d6
    >>> (3 @ d6) == d6_3 == h3d6 == (3 @ pd6) == pd6_3 == p3d6
    True
    >>> d6_3 is h3d6
    True
    >>> pd6_3 is p3d6
    True
    >>> 3 @ d6 is h3d6  # equivalent, but not the same object
    False
    >>> p3d6.h() is h3d6  # equivalent, but not the same object
    False
    >>> print(h3d6.format(width=65, scaled=True))
    avg |   10.50
    std |    2.96
    var |    8.75
      3 |   0.46% |#
      4 |   1.39% |#####
      5 |   2.78% |###########
      6 |   4.63% |##################
      7 |   6.94% |###########################
      8 |   9.72% |######################################
      9 |  11.57% |##############################################
     10 |  12.50% |##################################################
     11 |  12.50% |##################################################
     12 |  11.57% |##############################################
     13 |   9.72% |######################################
     14 |   6.94% |###########################
     15 |   4.63% |##################
     16 |   2.78% |###########
     17 |   1.39% |#####
     18 |   0.46% |#
"""

from .h import H as _H
from .p import P as _P

d1 = _H(1)
d2 = _H(2)
d3 = _H(3)
d4 = _H(4)
d5 = _H(5)
d6 = _H(6)
d7 = _H(7)
d8 = _H(8)
d9 = _H(9)
d10 = _H(10)
d11 = _H(11)
d12 = _H(12)
d13 = _H(13)
d14 = _H(14)
d15 = _H(15)
d16 = _H(16)
d17 = _H(17)
d18 = _H(18)
d19 = _H(19)
d20 = _H(20)
d24 = _H(24)
d30 = _H(30)
d60 = _H(60)
D66 = d6 * 10 + d6
D666 = d6 * 100 + D66
d100 = _H(100)
d00 = d10 * 10 + d10 - 1
d2_2 = h2d2 = 2 @ d2
d3_2 = h2d3 = 2 @ d3
d4_2 = h2d4 = 2 @ d4
d5_2 = h2d5 = 2 @ d5
d6_2 = h2d6 = 2 @ d6
d7_2 = h2d7 = 2 @ d7
d8_2 = h2d8 = 2 @ d8
d9_2 = h2d9 = 2 @ d9
d10_2 = h2d10 = 2 @ d10
d11_2 = h2d11 = 2 @ d11
d12_2 = h2d12 = 2 @ d12
d13_2 = h2d13 = 2 @ d13
d14_2 = h2d14 = 2 @ d14
d15_2 = h2d15 = 2 @ d15
d16_2 = h2d16 = 2 @ d16
d17_2 = h2d17 = 2 @ d17
d18_2 = h2d18 = 2 @ d18
d19_2 = h2d19 = 2 @ d19
d20_2 = h2d20 = 2 @ d20
d2_3 = h3d2 = 3 @ d2
d3_3 = h3d3 = 3 @ d3
d4_3 = h3d4 = 3 @ d4
d5_3 = h3d5 = 3 @ d5
d6_3 = h3d6 = 3 @ d6
d7_3 = h3d7 = 3 @ d7
d8_3 = h3d8 = 3 @ d8
d9_3 = h3d9 = 3 @ d9
d10_3 = h3d10 = 3 @ d10
d11_3 = h3d11 = 3 @ d11
d12_3 = h3d12 = 3 @ d12
d13_3 = h3d13 = 3 @ d13
d14_3 = h3d14 = 3 @ d14
d15_3 = h3d15 = 3 @ d15
d16_3 = h3d16 = 3 @ d16
d17_3 = h3d17 = 3 @ d17
d18_3 = h3d18 = 3 @ d18
d19_3 = h3d19 = 3 @ d19
d20_3 = h3d20 = 3 @ d20

pd1 = _P(d1)
pd2 = _P(d2)
pd3 = _P(d3)
pd4 = _P(d4)
pd5 = _P(d5)
pd6 = _P(d6)
pd7 = _P(d7)
pd8 = _P(d8)
pd9 = _P(d9)
pd10 = _P(d10)
pd11 = _P(d11)
pd12 = _P(d12)
pd13 = _P(d13)
pd14 = _P(d14)
pd15 = _P(d15)
pd16 = _P(d16)
pd17 = _P(d17)
pd18 = _P(d18)
pd19 = _P(d19)
pd20 = _P(d20)
pd24 = _P(d24)
pd30 = _P(d30)
pd60 = _P(d60)
pD66 = _P(d6 * 10, d6)  # noqa: N816
pD666 = _P(d6 * 100, pD66)  # noqa: N816
pd100 = _P(d100)
pd00 = _P(d10 * 10, d10 - 1)
pd2_2 = p2d2 = 2 @ pd2
pd3_2 = p2d3 = 2 @ pd3
pd4_2 = p2d4 = 2 @ pd4
pd5_2 = p2d5 = 2 @ pd5
pd6_2 = p2d6 = 2 @ pd6
pd7_2 = p2d7 = 2 @ pd7
pd8_2 = p2d8 = 2 @ pd8
pd9_2 = p2d9 = 2 @ pd9
pd10_2 = p2d10 = 2 @ pd10
pd11_2 = p2d11 = 2 @ pd11
pd12_2 = p2d12 = 2 @ pd12
pd13_2 = p2d13 = 2 @ pd13
pd14_2 = p2d14 = 2 @ pd14
pd15_2 = p2d15 = 2 @ pd15
pd16_2 = p2d16 = 2 @ pd16
pd17_2 = p2d17 = 2 @ pd17
pd18_2 = p2d18 = 2 @ pd18
pd19_2 = p2d19 = 2 @ pd19
pd20_2 = p2d20 = 2 @ pd20
pd2_3 = p3d2 = 3 @ pd2
pd3_3 = p3d3 = 3 @ pd3
pd4_3 = p3d4 = 3 @ pd4
pd5_3 = p3d5 = 3 @ pd5
pd6_3 = p3d6 = 3 @ pd6
pd7_3 = p3d7 = 3 @ pd7
pd8_3 = p3d8 = 3 @ pd8
pd9_3 = p3d9 = 3 @ pd9
pd10_3 = p3d10 = 3 @ pd10
pd11_3 = p3d11 = 3 @ pd11
pd12_3 = p3d12 = 3 @ pd12
pd13_3 = p3d13 = 3 @ pd13
pd14_3 = p3d14 = 3 @ pd14
pd15_3 = p3d15 = 3 @ pd15
pd16_3 = p3d16 = 3 @ pd16
pd17_3 = p3d17 = 3 @ pd17
pd18_3 = p3d18 = 3 @ pd18
pd19_3 = p3d19 = 3 @ pd19
pd20_3 = p3d20 = 3 @ pd20

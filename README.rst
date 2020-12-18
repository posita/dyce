.. -*- encoding: utf-8 -*-
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Please keep each sentence on its own unwrapped line.
    It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
    Thank you!

    WARNING: THIS DOCUMENT MUST BE SELF-CONTAINED.
    ALL LINKS MUST BE ABSOLUTE.
    This file is used on GitHub and PyPi (via setup.py).
    There is no guarantee that other docs/resources will be available where this content is displayed.

Copyright and other protections apply.
Please see the accompanying |LICENSE|_ file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its originals, then please contact the author before viewing or using this software in any capacity.

.. |LICENSE| replace:: ``LICENSE``
.. _`LICENSE`: https://dyce.readthedocs.org/en/master/LICENSE.html

.. image:: https://travis-ci.org/posita/dyce.svg?branch=master
   :target: https://travis-ci.org/posita/dyce?branch=master
   :alt: [Build Status]

Curious about integrating your project with the above services?
Jeff Knupp (|@jeffknupp|_) `describes how <https://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/>`__.

.. |@jeffknupp| replace:: **@jeffknupp**
.. _`@jeffknupp`: https://github.com/jeffknupp

``dyce`` - Simple Python tools for dice-based probabilities
===========================================================

.. image:: https://img.shields.io/pypi/v/dycelib.svg
   :target: https://pypi.python.org/pypi/dycelib
   :alt: [master Version]

.. image:: https://readthedocs.org/projects/dyce/badge/?version=master
   :target: https://dyce.readthedocs.org/en/master/
   :alt: [master Documentation]

.. image:: https://img.shields.io/pypi/l/dycelib.svg
   :target: http://opensource.org/licenses/MIT
   :alt: [master License]

.. image:: https://img.shields.io/pypi/pyversions/dycelib.svg
   :target: https://pypi.python.org/pypi/dycelib
   :alt: [master Supported Python Versions]

.. image:: https://img.shields.io/pypi/implementation/dycelib.svg
   :target: https://pypi.python.org/pypi/dycelib
   :alt: [master Supported Python Implementations]

.. image:: https://img.shields.io/pypi/status/dycelib.svg
   :target: https://pypi.python.org/pypi/dycelib
   :alt: [master Development Stage]

..

``dyce`` is a pure-Python library for exploring dice probabilities.
Inspired by `AnyDice <https://anydice.com/>`_, ``dyce`` provides Pythonic syntax and operators for rolling dice and computing weighted outcomes.

``dyce`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the |LICENSE|_ file for details.
Source code is `available on GitHub <https://github.com/posita/dyce>`__.
See `the docs <https://dyce.readthedocs.org/en/master/>`__ for more information.

Examples
--------

``dyce`` provides two key primitives: ``H`` for histograms (individual dice or outcomes) and ``D`` for collections of histograms (sets of multiple dice)::

  >>> from dyce import D, H

Both support arithmetic operations.
Those familiar with various `game notations <https://en.wikipedia.org/wiki/Dice_notation>`__ should be able to adapt quickly.
``2d6`` is::

  >>> 2@D(6)
  D(6, 6)

Note the use of Python’s matrix multiplication operator (``@``) to express the number of dice.

Individual dice are histograms.
A fudge die can be expressed as::

  >>> H((-1, 0, 1))
  H({-1: 1, 0: 1, 1: 1})

Four fudge dice can be expressed as::

  >>> 4@D(_)
  D(H({-1: 1, 0: 1, 1: 1}), H({-1: 1, 0: 1, 1: 1}), H({-1: 1, 0: 1, 1: 1}), H({-1: 1, 0: 1, 1: 1}))

Arithmetic operations implicitly de-normalize dice sets into histograms.
``3×(2d6+4)`` is::

  >>> 3*(2@D(6)+4)
  H({18: 1, 21: 2, 24: 3, 27: 4, 30: 5, 33: 6, 36: 5, 39: 4, 42: 3, 45: 2, 48: 1})

When computing outcomes involving multiple dice, slices select subsets.
Face values are ordered from greatest to least.
Summing the least two face values when rolling three six-sided dice would be::

  >>> (3@D(6))[:2]
  H({2: 16, 3: 27, 4: 34, 5: 36, 6: 34, 7: 27, 8: 19, 9: 12, 10: 7, 11: 3, 12: 1})

Arbitrary iterables can be used for more flexibility.
Summing the greatest and the least faces of an entire standard six-die polygonal set would be::

  >>> h10 = H(10)-1  # 0-9
  >>> D(4, 6, 8, h10, 12, 20)[0,-1]
  H({1: 1, 2: 32, 3: 273, 4: 1384, ..., 21: 20736, 22: 9240, 23: 3360, 24: 810})

Histograms provide rudimentary formatting for convenience::

  >>> print((2@D(6)).h().format(width=80))
  avg |    7.00
    2 |   2.78% |#
    3 |   5.56% |###
    4 |   8.33% |#####
    5 |  11.11% |#######
    6 |  13.89% |#########
    7 |  16.67% |##########
    8 |  13.89% |#########
    9 |  11.11% |#######
   10 |   8.33% |#####
   11 |   5.56% |###
   12 |   2.78% |#

Issues
------

If you find a bug, or want a feature, please `file an issue <https://github.com/posita/dyce/issues>`__ (if it has not already been filed).
If you are willing and able, consider `contributing <https://dyce.readthedocs.org/en/master/contrib.html>`__.

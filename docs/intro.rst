.. -*- encoding: utf-8 -*-
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    Please keep each sentence on its own unwrapped line.
    It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
    Thank you!

.. toctree::

Copyright and other protections apply.
Please see the accompanying :doc:`LICENSE <LICENSE>` file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If that file is missing or appears to be modified from its originals, then please contact the author before viewing or using this software in any capacity.

Introduction
============

``dyce`` is a pure-Python library for exploring dice probabilities designed to be immediately and broadly useful with minimal additional investment beyond basic knowledge of Python.
Inspired by `AnyDice <https://anydice.com/>`_, ``dyce`` leverages Pythonic syntax and operators for rolling dice and computing weighted outcomes.
While Python is not as terse as a dedicated grammar, it is quite sufficient.
Those familiar with various `game notations <https://en.wikipedia.org/wiki/Dice_notation>`__ should be able to adapt quickly.

Examples
--------

``dyce`` provides two key primitives: ``H`` for histograms (individual dice or outcomes) and ``D`` for collections of histograms (sets of multiple dice)::

  >>> from dyce import D, H

Both support arithmetic operations.

Histograms are used to express individual dice and results.
A six-sided die can be expressed as::

  >>> H(6)
  H(6)

``H(n)`` is shorthand for explicitly enumerating faces :math:`[{{1} .. {n}}]`, each with a frequency of 1::

  >>> H(6) == H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})
  True

Tuples with repeating faces are accumulated.
A six-sided “2, 3, 3, 4, 4, 5” die can be expressed as::

  >>> H((2, 3, 3, 4, 4, 5))
  H({2: 1, 3: 2, 4: 2, 5: 1})

A fudge die can be expressed as::

  >>> H((-1, 0, 1))
  H({-1: 1, 0: 1, 1: 1})

Python’s matrix multiplication operator (``@``) is used to express the number of a particular die (roughly equivalent to the “``d``” operator in common notations).
A set of two six-sided dice (``2d6``) is::

  >>> 2@D(H(6))
  D(6, 6)

``D(n)`` is shorthand for ``D(H(n))``, if ``n`` is an integer.
The above can be expressed more succinctly::

  >>> 2@D(6)
  D(6, 6)

Dice sets can be compared to histograms::

  >>> 2@D(6) == 2@H(6)
  True

Arithmetic operations implicitly flatten dice sets into histograms.
``3×(2d6+4)`` is::

  >>> 3*(2@D(6)+4)
  H({18: 1, 21: 2, 24: 3, 27: 4, 30: 5, 33: 6, 36: 5, 39: 4, 42: 3, 45: 2, 48: 1})

In interpreting the results, we see there is one way to make ``18``, two ways to make ``21``, three ways to make ``24``, etc.

Histograms are sufficient for most calculations.
However, dice sets are useful for taking only some of the set’s faces.
This is done using Python’s indexing operator (``[…]``).
Indexes can be integers, slices, or iterables thereof.
Faces are ordered from greatest to least.
Summing the least two faces when rolling three six-sided dice would be::

  >>> d6_3 = 3@D(6)
  >>> d6_3
  D(6, 6, 6)
  >>> d6_3[:2]
  H({2: 16, 3: 27, 4: 34, 5: 36, 6: 34, 7: 27, 8: 19, 9: 12, 10: 7, 11: 3, 12: 1})

Selecting the least, middle, or greatest face when rolling three six-sided dice would be::

  >>> d6_3[0]
  H({1: 91, 2: 61, 3: 37, 4: 19, 5: 7, 6: 1})
  >>> d6_3[1]
  H({1: 16, 2: 40, 3: 52, 4: 52, 5: 40, 6: 16})
  >>> d6_3[-1]
  H({1: 1, 2: 7, 3: 19, 4: 37, 5: 61, 6: 91})

Summing the greatest and the least faces of an entire standard six-die polygonal set would be::

  >>> H(10)-1  # a common “d10” with faces [0 .. 9]
  H({0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1})
  >>> D(4, 6, 8, _, 12, 20)[0, -1]
  H({1: 1, 2: 32, 3: 273, 4: 1384, ..., 21: 20736, 22: 9240, 23: 3360, 24: 810})

Histograms provide rudimentary formatting for convenience::

  >>> print((2@H(6)).format())
  avg |    7.00
    2 |   2.78% |##
    3 |   5.56% |####
    4 |   8.33% |######
    5 |  11.11% |########
    6 |  13.89% |##########
    7 |  16.67% |############
    8 |  13.89% |##########
    9 |  11.11% |########
   10 |   8.33% |######
   11 |   5.56% |####
   12 |   2.78% |##

If |matplotlib|_ is installed (e.g., via |jupyter|_), :mod:`dyce.plt` provides some conveniences::

  >>> from matplotlib.pyplot import show
  >>> from dyce.plt import plot_burst
  >>> h = 4@H((-1, 0, 1))
  >>> fix, ax = plot_burst(h)

Calling :func:`show` presents:

.. image:: plot_burst_1.png

The outer ring and corresponding labels can be overridden::

  >>> d20 = D(20)
  >>> fig, ax = plot_burst(d20.h(), outer=(
  ...   ("crit. fail.", d20.le(1)[1]),
  ...   ("fail.", d20.within(2, 14)[0]),
  ...   ("succ.", d20.within(15, 19)[0]),
  ...   ("crit. succ.", d20.ge(20)[1]),
  ... ), graph_color="RdYlBu_r")

Calling :func:`show` presents:

.. image:: plot_burst_2.png

.. |matplotlib| replace:: ``matplotlib``
.. _`matplotlib`: https://matplotlib.org/
.. |jupyter| replace:: ``jupyter``
.. _`jupyter`: https://jupyter.org/

License
-------

``dyce`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the :doc:`LICENSE <LICENSE>` file for details.
Source code is `available on GitHub <https://github.com/posita/dyce>`__.

Installation
------------

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/dyce/>`__):

.. code-block:: console

   % pip install dycelib
   ...

Alternately, you can download the sources (e.g., `from GitHub <https://github.com/posita/dyce>`__) and run ``setup.py``:

.. code-block:: console

   % git clone https://github.com/posita/dyce
   ...
   % cd dyce
   % python setup.py install
   ...

Requirements
------------

A modern version of Python is required:

* `cPython <https://www.python.org/>`_ (3.6+)
* `PyPy <http://pypy.org/>`_ (Python 3.6+ compatible)

``dyce`` has the following dependencies (which will be installed automatically):

* |typing|_
* |typing-extensions|_

.. |typing| replace:: ``typing``
.. _`typing`: https://pypi.org/project/typing/
.. |typing-extensions| replace:: ``typing-extensions``
.. _`typing-extensions`: https://pypi.org/project/typing-extensions/

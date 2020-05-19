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

``dyce`` is a Python library of simple tools for working with dice-based probabilities.

License
-------

``dyce`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the :doc:`LICENSE <LICENSE>` file for details.
Source code is `available on GitHub <https://github.com/posita/dyce>`__.

Installation
------------

This project is not meant to be installed as is, but rather cloned and then modified as necessary.
It is intended that derived projects allow installation via ``pip``.

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/dyce/>`__):

.. code-block:: console

   % pip install dyce
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

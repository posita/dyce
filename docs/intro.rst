.. -*- encoding: utf-8 -*-
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>> IMPORTANT: READ THIS BEFORE EDITING! <<<<<<<<<<<<<<<
    >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    Please keep each sentence on its own unwrapped line.
    It looks like crap in a text editor, but it has no effect on rendering, and it allows much more useful diffs.
    Thank you!

.. toctree::
   :maxdepth: 3
   :hidden:

Copyright and other protections apply.
Please see the accompanying :doc:`LICENSE <LICENSE>` file for rights and restrictions governing use of this software.
All rights not expressly waived or licensed are reserved.
If those files are missing or appear to be modified from their originals, then please contact the author before viewing or using this software in any capacity.

Introduction
============

``_skel`` is a project skeleton for Python.

License
-------

``_skel`` is licensed under the `MIT License <https://opensource.org/licenses/MIT>`_.
See the :doc:`LICENSE <LICENSE>` file for details.
Source code is `available on GitHub <https://github.com/posita/_skel>`__.

Installation
------------

This project is not meant to be installed as is, but rather cloned and then modified as necessary.
It is intended that derived projects allow installation via ``pip``.

Installation can be performed via ``pip`` (which will download and install the `latest release <https://pypi.python.org/pypi/_skel/>`__):

.. code-block:: console

   % pip install _skel
   ...

Alternately, you can download the sources (e.g., `from GitHub <https://github.com/posita/_skel>`__) and run ``setup.py``:

.. code-block:: console

   % git clone https://github.com/posita/_skel
   ...
   % cd _skel
   % python setup.py install
   ...

Requirements
------------

A modern version of Python is required:

* `cPython <https://www.python.org/>`_ (2.7 or 3.3+)
* `PyPy <http://pypy.org/>`_ (Python 2.7 or 3.3+ compatible)

Python 2.6 will *not* work.

``_skel`` has the following dependencies (which will be installed automatically):

* |future|_

.. |future| replace:: ``future``
.. _`future`: http://python-future.org/

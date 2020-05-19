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

Contributing to ``dyce``
========================

There are several ways you can contribute.

Filing Issues
-------------

You can `file new issues <https://github.com/posita/dyce/issues>`__ as you find them.
Please avoid duplicating issues.
`“Writing Effective Bug Reports” by Elisabeth Hendrickson <http://testobsessed.com/wp-content/uploads/2011/07/webr.pdf>`__ (PDF) may be helpful.

Submission Guidelines
---------------------

If you are willing and able, consider `submitting a pull request <https://github.com/posita/dyce/pulls>`__ (PR) with a fix.
There are only a few guidelines:

*   If it is not already present, please add your name (and optionally your GitHub username, email, website address, or other contact information) to the :doc:`LICENSE <LICENSE>` file:

    .. code-block:: rst

       ...
       *   `Gordon the Turtle <https://github.com/GordonTheTurtle>`_
       ...

*   Try to follow the source conventions as you observe them.
    (Note: I have purposely avoided aspects of `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_, in part because I have adopted conventions developed from my experiences with other languages, but mostly because I am growing older and more stubborn.)

..

*   Provide tests where feasible and appropriate.
    At the very least, existing tests should not fail.
    (There are exceptions, but if there is any doubt, they probably do not apply.)

    Unit tests live in ``./tests`` and can be run with `Tox <https://tox.readthedocs.org/>`_ or `pytest <https://docs.pytest.org/>`_.
    A helper script is provided for setting up an isolated development environment.
    For example:

    .. code-block:: sh

      [PYTHON=/path/to/python] ./helpers/venvsetup.sh
      tox [TOX_ARGS... [-- PYTEST_ARGS...]]
      pytest [PYTEST_ARGS...]

*   If you need me, mention me (|@posita|_) in your comment, and describe specifically how I can help.

.. |@posita| replace:: **@posita**
.. _`@posita`: https://github.com/posita

*   If you want feedback on a work-in-progress (WIP), create a PR and prefix its title with something like, “``NEED FEEDBACK -``”.

..

*   If your PR is still in progress, but you are not blocked on anything, prefix the title with something like, “``WIP -``”.

..

*   Once you are ready for a merge, resolve any merge conflicts, squash your commits, and provide a useful commit message.
    (`This <https://robots.thoughtbot.com/git-interactive-rebase-squash-amend-rewriting-history>`__ and `this <http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html>`__ may be helpful.)
    Then prefix the PR’s title to something like, “``READY FOR MERGE -``”.
    I will try to get to it as soon as I can.

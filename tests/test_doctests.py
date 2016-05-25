#-*- encoding: utf-8; grammar-ext: py; mode: python -*-

#=========================================================================
"""
  Copyright |(c)| 2015-2016 `Matt Bogosian`_ (|@posita|_).

  .. |(c)| unicode:: u+a9
  .. _`Matt Bogosian`: mailto:mtb19@columbia.edu
  .. |@posita| replace:: **@posita**
  .. _`@posita`: https://github.com/posita

  Please see the accompanying ``LICENSE`` (or ``LICENSE.txt``) file for
  rights and restrictions governing use of this software. All rights not
  expressly waived or licensed are reserved. If such a file did not
  accompany this software, then please contact the author before viewing
  or using this software in any capacity.
"""
#=========================================================================

from __future__ import (
    absolute_import, division, print_function, unicode_literals,
)
from builtins import * # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import * # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

#---- Imports ------------------------------------------------------------

import doctest
import logging
import os
from os import path
import re
import types

import _skel
import tests

#---- Constants ----------------------------------------------------------

__all__ = (
    'load_tests',
    'mkloadtests',
)

_PATH_RE = r'(' + re.escape(path.sep) + r'.*)?$'

_DOCTEST_ROOTS = (
    _skel,
    tests,
)

_LOGGER = logging.getLogger(__name__)

#---- Functions ----------------------------------------------------------

#=========================================================================
def load_tests(_, tests, __): # pylint: disable=redefined-outer-name
    """
    >>> True is not False
    True
    """
    in_len = tests.countTestCases()
    tests = _load_tests(_, tests, __)
    out_len = tests.countTestCases()
    # Test whether at least one doctest is found (which could be the
    # doctest for this function)
    assert in_len < out_len

    return tests

#=========================================================================
def mkloadtests(roots):
    """
    Creates the `load_tests` hook function to be called by
    `unittest.loadTestsFromModule` during unittest discovery to find and
    include all `doctest`s. To work with `setuptools`, this function must
    be in whatever module is passed to `setuptools.setup` via the
    ``test_suite`` argument.

    When iterated over, ``roots`` must provide either the root module or
    pairs of strings in the form ``( 'root_mod_path', 'root_mod_name' )``,
    where ``root_mod_path`` is the path to the root module and
    ``root_mod_name`` is the name of that module (as it would be used in
    an ``import`` statement).

    To use in a module:

    .. code-block:: python
        :linenos:

        import mymodule
        ROOTS = ( mymodule, ) # equivalent to ( ( mymodule.__file__, mymodule.__name__ ), )
        load_tests = mkloadtests(ROOTS)

    :param iterable roots: the root definitions from which to discover the
        doctests

    :note: I should *not* have to write this myself. *Grrr!*
    """
    def load_tests(_, tests, __): # pylint: disable=redefined-outer-name,unused-argument
        finder = doctest.DocTestFinder(exclude_empty=False)

        for root_mod in roots:
            if isinstance(root_mod, types.ModuleType):
                root_mod_path, root_mod_name = root_mod.__file__, root_mod.__name__
            else:
                root_mod_path, root_mod_name = root_mod

            if path.splitext(path.basename(root_mod_path))[0] == '__init__':
                root_mod_path = path.dirname(root_mod_path)

            if path.isfile(root_mod_path):
                root_mod_iter = ( ( path.dirname(root_mod_path), None, ( path.basename(root_mod_path), ) ), )
            else:
                root_mod_iter = os.walk(root_mod_path)

            for dir_name, _, file_names in root_mod_iter:
                if not re.match(re.escape(root_mod_path) + _PATH_RE, dir_name):
                    continue

                mod_name = dir_name[len(root_mod_path):].replace(path.sep, '.').strip('.')

                if mod_name:
                    mod_name = root_mod_name + '.' + mod_name
                else:
                    mod_name = root_mod_name

                for file_name in file_names:
                    if not file_name.endswith('.py'):
                        continue

                    if file_name == '__init__.py':
                        test_mod_name = mod_name
                    else:
                        test_mod_name = mod_name + '.' + path.splitext(file_name)[0]

                    try:
                        tests.addTest(doctest.DocTestSuite(test_mod_name, test_finder=finder))
                    except Exception as err: # pylint: disable=broad-except
                        _LOGGER.warning('unable to load doctests from %s (%s)', test_mod_name, err)

        return tests

    return load_tests

#=========================================================================
_load_tests = mkloadtests(_DOCTEST_ROOTS)

#---- Initialization -----------------------------------------------------

if __name__ == '__main__':
    from unittest import main
    main()

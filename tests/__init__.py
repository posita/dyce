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

import logging
import os
import sys
import unittest

#---- Constants ----------------------------------------------------------

__all__ = ()

_LOG_LVL = os.environ.get('_LOG_LVL')
_LOG_LVL = logging.WARNING if not _LOG_LVL else logging.getLevelName(_LOG_LVL)
_LOG_FMT = os.environ.get('_LOG_FMT')

#---- Initialization -----------------------------------------------------

# Python 3.4 complains that the assert*Regexp* methods are deprecated in
# favor of the analogous assert*Regex methods, which Python 2.7's unittest
# doesn't have; this monkey patch fixes all that nonsense
if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
    unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

if not hasattr(unittest.TestCase, 'assertRegex'):
    unittest.TestCase.assertRegex = unittest.TestCase.assertRegexpMatches

if not hasattr(unittest.TestCase, 'assertNotRegex'):
    unittest.TestCase.assertNotRegex = unittest.TestCase.assertNotRegexpMatches

logging.basicConfig(format=_LOG_FMT)
logging.getLogger().setLevel(_LOG_LVL)

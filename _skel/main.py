# -*- encoding: utf-8; test-case-name: tests.test_main -*-

# ========================================================================
"""
Copyright and other protections apply. Please see the accompanying
:doc:`LICENSE <LICENSE>` and :doc:`CREDITS <CREDITS>` file(s) for rights
and restrictions governing use of this software. All rights not expressly
waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before
viewing or using this software in any capacity.
"""
# ========================================================================

from __future__ import absolute_import, division, print_function

TYPE_CHECKING = False  # from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

from builtins import *  # noqa: F401,F403 # pylint: disable=redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import
from future.builtins.disabled import *  # noqa: F401,F403 # pylint: disable=no-name-in-module,redefined-builtin,unused-wildcard-import,useless-suppression,wildcard-import

# ---- Imports -----------------------------------------------------------

import argparse
import logging
import os
import sys

from .version import __release__

# ---- Data --------------------------------------------------------------

__all__ = ()

_LOGGER = logging.getLogger(__name__)

_LOG_FMT_ENV = 'LOG_FMT'
_LOG_FMT_DFLT = '%(message)s'
_LOG_LVL_ENV = 'LOG_LVL'
_LOG_LVL_DFLT = logging.getLevelName(logging.WARNING)

# ---- Exceptions --------------------------------------------------------

# ---- Decorators --------------------------------------------------------

# ---- Classes -----------------------------------------------------------

# ========================================================================
class Template(object):
    """
    TODO
    """

    __slots__ = (
        '_todo',
    )

    # ---- Data ----------------------------------------------------------

    # ---- Static methods ------------------------------------------------

    # ---- Class methods -------------------------------------------------

    # ---- Inner classes -------------------------------------------------

    # ---- Constructor ---------------------------------------------------

    def __init__(self,
        todo=None,  # type: typing.Any
    ):  # type: (...) -> None
        """
        :param todo: the todo to associate with this object
        """
        super().__init__()  # type: ignore
        self._todo = todo

    # ---- Overrides -----------------------------------------------------

    def todohook(self):  # type: (...) -> None
        """
        Hook method to TODO.

        >>> True is True and False is False
        True
        """

    # ---- Properties ----------------------------------------------------

    @property
    def todo(self):  # type: (...) -> typing.Any
        """
        The todo associated with this object.
        """
        return self._todo

    @todo.setter
    def todo(self,
        todo,  # type: typing.Any
    ):  # type: (...) -> None
        self._todo = todo

    # ---- Methods -------------------------------------------------------

# ---- Functions ---------------------------------------------------------

# ========================================================================
def configlogging():  # type: (...) -> None
    log_lvl_name = os.environ.get(_LOG_LVL_ENV) or _LOG_LVL_DFLT

    try:
        log_lvl = int(log_lvl_name, 0)
    except (TypeError, ValueError):
        log_lvl = 0
        log_lvl = logging.getLevelName(log_lvl_name)  # type: ignore

    log_fmt = os.environ.get(_LOG_FMT_ENV, _LOG_FMT_DFLT)
    logging.basicConfig(format=log_fmt)
    logging.getLogger().setLevel(log_lvl)
    from . import LOGGER
    LOGGER.setLevel(log_lvl)

# ========================================================================
def main():  # type: (...) -> None
    configlogging()
    sys.exit(_main())

# ========================================================================
def _main(
    argv=None,  # type: typing.Optional[typing.Sequence[typing.Text]]
):  # type: (...) -> int
    parser = _parser()
    ns = parser.parse_args(argv)

    assert ns

    return 0

# ========================================================================
def _parser(
    prog=None,  # type: typing.Optional[typing.Text]
):  # type: (...) -> argparse.ArgumentParser
    description = u"""
TODO
""".strip()

    log_lvls = u', '.join(u'"{}"'.format(logging.getLevelName(l)) for l in (logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG))
    epilog = u"""
The environment variables {log_lvl} and {log_fmt} can be used to configure logging output.
If set, {log_lvl} must be an integer, or one of (from least to most verbose): {log_lvls}.
It defaults to "{log_lvl_dflt}".
If set, {log_fmt} must be a logging format compatible with Python's ``logging`` module.
It defaults to "{log_fmt_dflt}".
""".strip().format(log_fmt=_LOG_FMT_ENV, log_fmt_dflt=_LOG_FMT_DFLT, log_lvl=_LOG_LVL_ENV, log_lvl_dflt=_LOG_LVL_DFLT, log_lvls=log_lvls)

    parser = argparse.ArgumentParser(prog=prog, description=description, epilog=epilog)

    parser.add_argument(u'-V', u'--version', action='version', version=u'%(prog)s {}'.format(__release__))

    return parser

# ---- Initialization ----------------------------------------------------

if __name__ == '__main__':
    pass

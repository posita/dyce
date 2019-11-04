# -*- encoding: utf-8; test-case-name: tests.test_main -*-
# ======================================================================================
"""
Copyright and other protections apply. Please see the accompanying :doc:`LICENSE
<LICENSE>` file for rights and restrictions governing use of this software. All rights
not expressly waived or licensed are reserved. If those files are missing or appear to
be modified from their originals, then please contact the author before viewing or using
this software in any capacity.
"""
# ======================================================================================

# from __future__ import generator_stop
from typing import *  # noqa: F401,F403 # pylint: disable=unused-wildcard-import,wildcard-import


# ---- Imports -------------------------------------------------------------------------


import argparse
import logging
import os
import sys

from .version import __release__


# ---- Data ----------------------------------------------------------------------------


__all__ = ()

_LOGGER = logging.getLogger(__name__)

_LOG_FMT_ENV = "LOG_FMT"
_LOG_FMT_DFLT = "%(message)s"
_LOG_LVL_ENV = "LOG_LVL"
_LOG_LVL_DFLT = logging.getLevelName(logging.WARNING)


# ---- Exceptions ----------------------------------------------------------------------


# ---- Decorators ----------------------------------------------------------------------


# ---- Classes -------------------------------------------------------------------------


class Template(object):
    """
    TODO
    """

    __slots__ = ("_todo",)

    # ---- Data ------------------------------------------------------------------------

    # ---- Static methods --------------------------------------------------------------

    # ---- Class methods ---------------------------------------------------------------

    # ---- Inner classes ---------------------------------------------------------------

    # ---- Constructor -----------------------------------------------------------------

    def __init__(self, todo: Any = None,) -> None:  # noqa: F405
        """
        :param todo: the todo to associate with this object
        """
        super().__init__()
        self._todo = todo

    # ---- Overrides -------------------------------------------------------------------

    def todohook(self) -> None:
        """
        Hook method to TODO.

        >>> True is True and False is False
        True
        """

    # ---- Properties ------------------------------------------------------------------

    @property
    def todo(self) -> Any:  # noqa: F405
        """
        The todo associated with this object.
        """
        return self._todo

    @todo.setter
    def todo(self, todo: Any,) -> None:  # noqa: F405
        self._todo = todo

    # ---- Methods ---------------------------------------------------------------------


# ---- Functions -----------------------------------------------------------------------


def configlogging() -> None:
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


def main() -> None:
    configlogging()
    sys.exit(_main())


def _main(argv: Optional[Sequence[Text]] = None,) -> int:  # noqa: F405
    parser = _parser()
    ns = parser.parse_args(argv)

    assert ns

    return 0


def _parser(prog: Optional[Text] = None,) -> argparse.ArgumentParser:  # noqa: F405
    description = """
TODO
""".strip()

    log_lvls = ", ".join(
        '"{}"'.format(logging.getLevelName(lvl))
        for lvl in (
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
        )
    )
    epilog = """
The environment variables {log_lvl} and {log_fmt} can be used to configure logging output.
If set, {log_lvl} must be an integer, or one of (from least to most verbose): {log_lvls}.
It defaults to "{log_lvl_dflt}".
If set, {log_fmt} must be a logging format compatible with Python's ``logging`` module.
It defaults to "{log_fmt_dflt}".
""".strip().format(
        log_fmt=_LOG_FMT_ENV,
        log_fmt_dflt=_LOG_FMT_DFLT,
        log_lvl=_LOG_LVL_ENV,
        log_lvl_dflt=_LOG_LVL_DFLT,
        log_lvls=log_lvls,
    )

    parser = argparse.ArgumentParser(prog=prog, description=description, epilog=epilog)

    parser.add_argument(
        "-V", "--version", action="version", version="%(prog)s {}".format(__release__)
    )

    return parser


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    main()

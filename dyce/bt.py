# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import os
from typing import Callable, Tuple, TypeVar, cast

__all__ = ("beartype",)


# ---- Types ---------------------------------------------------------------------------


_T = TypeVar("_T")


# ---- Functions -----------------------------------------------------------------------


def identity(__: _T) -> _T:
    return __


beartype: Callable[[_T], _T] = identity
__version_info__: Tuple[int, ...] = (0,)
_DYCE_BEARTYPE = os.environ.get("DYCE_BEARTYPE", "on")
_beartype_on: bool
_truthy = ("on", "t", "true", "yes")
_falsy = ("off", "f", "false", "no")

try:
    _beartype_on = bool(int(_DYCE_BEARTYPE))
except ValueError:
    if _DYCE_BEARTYPE.lower() in _truthy:
        _beartype_on = True
    elif _DYCE_BEARTYPE.lower() in _falsy:
        _beartype_on = False
    else:
        _booleany = _truthy + _falsy
        raise EnvironmentError(
            f"unrecognized value ({_DYCE_BEARTYPE}) for DYCE_BEARTYPE environment variable (should be one of an integer or {', '.join(_booleany)})"
        )

if _beartype_on:
    try:
        from beartype import __version_info__ as _version_info
        from beartype import beartype as _beartype

        __version_info__ = _version_info
        beartype = cast(Callable[[_T], _T], _beartype)
    except ImportError:
        pass

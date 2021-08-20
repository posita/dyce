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
import warnings
from typing import Callable, TypeVar, cast

__all__ = ("beartype",)


# ---- Types ---------------------------------------------------------------------------


_T = TypeVar("_T")


# ---- Functions -----------------------------------------------------------------------


def identity(__: _T) -> _T:
    return __


# ---- Initialization ------------------------------------------------------------------


beartype: Callable[[_T], _T] = identity

_DYCE_BEARTYPE = os.environ.get("DYCE_BEARTYPE", "on")
_truthy = ("on", "t", "true", "yes")
_falsy = ("off", "f", "false", "no")
_use_beartype_if_available: bool

try:
    _use_beartype_if_available = bool(int(_DYCE_BEARTYPE))
except ValueError:
    if _DYCE_BEARTYPE.lower() in _truthy:
        _use_beartype_if_available = True
    elif _DYCE_BEARTYPE.lower() in _falsy:
        _use_beartype_if_available = False
    else:
        raise EnvironmentError(
            f"""unrecognized value ({_DYCE_BEARTYPE}) for DYCE_BEARTYPE environment variable (should be "{'", "'.join(_truthy + _falsy)}", or an integer)"""
        )

if _use_beartype_if_available:
    try:
        import beartype as _beartype

        if _beartype.__version_info__ >= (0, 8):
            beartype = cast(Callable[[_T], _T], _beartype.beartype)
        else:
            warnings.warn(
                f"beartype>=0.8 required, but beartype=={_beartype.__version__} found; disabled"
            )
    except ImportError:
        pass

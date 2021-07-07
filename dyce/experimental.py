# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import warnings
from functools import wraps
from typing import TypeVar

__all__ = ()


# ---- Types ---------------------------------------------------------------------------


_WrappedT = TypeVar("_WrappedT")


# ---- Exceptions ----------------------------------------------------------------------


class ExperimentalWarning(PendingDeprecationWarning):
    pass


# ---- Decorators ----------------------------------------------------------------------


def experimental(f: _WrappedT) -> _WrappedT:
    """
    Decorator to mark an interface as experimental. Warns on *f*'s first use.
    """
    _wrapped: _WrappedT
    warned = False

    @wraps(f)  # type: ignore
    def _wrapped(*args, **kw):
        nonlocal warned

        if not warned:
            warnings.warn(
                f"{f.__qualname__} should be considered experimental and may disappear in future versions",
                category=ExperimentalWarning,
                stacklevel=2,
            )
            warned = True

        return f(*args, **kw)

    return _wrapped

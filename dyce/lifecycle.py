# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import warnings
from collections.abc import Callable
from functools import wraps
from typing import TypeVar, cast

__all__ = ()


# ---- Types ---------------------------------------------------------------------------


_WrappedT = TypeVar("_WrappedT", bound=Callable)


# ---- Exceptions ----------------------------------------------------------------------


class ExperimentalWarning(PendingDeprecationWarning):
    __slots__ = ()


# ---- Decorators ----------------------------------------------------------------------


def deprecated(f: _WrappedT) -> _WrappedT:
    r"""
    Decorator to mark an interface as deprecated. Warns on *f*’s first use.
    """
    return _warn_decr(
        f,
        DeprecationWarning,
        f"{f.__qualname__} is deprecated and will likely be removed in the next major release",
    )


def experimental(f: _WrappedT) -> _WrappedT:
    r"""
    Decorator to mark an interface as experimental. Warns on *f*’s first use.
    """
    return _warn_decr(
        f,
        ExperimentalWarning,
        f"{f.__qualname__} should be considered experimental and may change or disappear in future versions",
    )


def _warn_decr(f: _WrappedT, category: type[Warning], warning_txt: str) -> _WrappedT:
    @wraps(f)
    def _wrapped(*args: object, **kw: object) -> object:
        warnings.warn(
            warning_txt,
            category=category,
            stacklevel=2,
        )

        return f(*args, **kw)

    return cast("_WrappedT", _wrapped)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Please keep each docstring sentence on its own unwrapped line. It looks like crap in a
# text editor, but it has no effect on rendering, and it allows much more useful diffs.
# (This does not apply to code comments.) Thank you!
# ======================================================================================

import functools
import inspect
import sys
import warnings
from collections.abc import Callable
from typing import ParamSpec, TypeVar

if sys.version_info >= (3, 13):
    from warnings import deprecated  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import deprecated

__all__ = ("ExperimentalWarning", "deprecated", "experimental")

_ParamsT = ParamSpec("_ParamsT")
_ReturnT = TypeVar("_ReturnT")


class ExperimentalWarning(UserWarning):
    pass


experimental_msg = (
    "`%s` is experimental; its interface may change or it may be removed in a future"
    " release."
)


def experimental(fn: Callable[_ParamsT, _ReturnT]) -> Callable[_ParamsT, _ReturnT]:
    r"""
    Decorator that emits an [`ExperimentalWarning`][dyce.lifecycle.ExperimentalWarning] at each call site and prepends a warning admonition to the callable’s docstring.
    """
    msg = experimental_msg % fn.__qualname__  # ty: ignore[unresolved-attribute]
    admonition = f'!!! warning "Experimental"\n\n    {msg}'
    original_doc = inspect.cleandoc(fn.__doc__ or "")

    @functools.wraps(fn)
    def wrapper(*args: _ParamsT.args, **kwargs: _ParamsT.kwargs) -> _ReturnT:
        warnings.warn(msg, ExperimentalWarning, stacklevel=2)
        return fn(*args, **kwargs)

    wrapper.__doc__ = admonition + ("\n\n" + original_doc if original_doc else "")
    return wrapper

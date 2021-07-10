# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import (
    Protocol,
    SupportsAbs,
    SupportsFloat,
    SupportsInt,
    TypeVar,
    runtime_checkable,
)

__all__ = ("OutcomeP", "SupportsArithmetic", "SupportsBitwise")


# ---- Types ---------------------------------------------------------------------------


_T_co = TypeVar("_T_co", covariant=True)


@runtime_checkable
class SupportsArithmetic(Protocol[_T_co], metaclass=ABCMeta):
    @abstractmethod
    def __lt__(self, other) -> bool:
        ...

    @abstractmethod
    def __le__(self, other) -> bool:
        ...

    @abstractmethod
    def __ge__(self, other) -> bool:
        ...

    @abstractmethod
    def __gt__(self, other) -> bool:
        ...

    @abstractmethod
    def __add__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __radd__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __sub__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rsub__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __mul__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rmul__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __truediv__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rtruediv__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __floordiv__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rfloordiv__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __mod__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rmod__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __pow__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __rpow__(self, other) -> _T_co:
        ...

    @abstractmethod
    def __neg__(self) -> _T_co:
        ...

    @abstractmethod
    def __pos__(self) -> _T_co:
        ...


@runtime_checkable
class SupportsBitwise(Protocol[_T_co], metaclass=ABCMeta):
    @abstractmethod
    def __and__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __rand__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __xor__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __rxor__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __or__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __ror__(self, other: SupportsInt) -> _T_co:
        ...

    @abstractmethod
    def __invert__(self) -> _T_co:
        ...


@runtime_checkable
class OutcomeP(
    SupportsAbs[_T_co],
    SupportsFloat,
    SupportsArithmetic[_T_co],
    Protocol[_T_co],
    metaclass=ABCMeta,
):
    # Must be able to instantiate it
    @abstractmethod
    def __init__(self, *args, **kw):
        # pylint: disable=super-init-not-called
        ...

    @abstractmethod
    def __hash__(self) -> int:
        ...

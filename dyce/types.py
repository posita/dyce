# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import re
import sys
from abc import abstractmethod
from operator import __getitem__, __index__
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .bt import identity  # noqa: F401
from .bt import beartype

__all__ = ("OutcomeT",)


# ---- Types ---------------------------------------------------------------------------

_S = TypeVar("_S")
_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_TT = TypeVar("_TT", bound="type")


if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated  # noqa: F401


if sys.version_info >= (3, 8):
    from typing import Protocol
    from typing import SupportsAbs as _SupportsAbs
    from typing import SupportsFloat as _SupportsFloat
    from typing import SupportsIndex as _SupportsIndex
    from typing import SupportsInt as _SupportsInt
    from typing import runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

    @runtime_checkable
    class _SupportsAbs(Protocol[_T_co]):
        __slots__: Tuple[str, ...] = ()

        @abstractmethod
        def __abs__(self) -> _T_co:
            ...

    @runtime_checkable
    class _SupportsFloat(Protocol):
        __slots__: Tuple[str, ...] = ()

        @abstractmethod
        def __float__(self) -> float:
            ...

    @runtime_checkable
    class _SupportsIndex(Protocol):
        __slots__: Tuple[str, ...] = ()

        @abstractmethod
        def __index__(self) -> int:
            ...

    @runtime_checkable
    class _SupportsInt(Protocol):
        __slots__: Tuple[str, ...] = ()

        @abstractmethod
        def __int__(self) -> int:
            ...


_ProtocolMeta: Any = type(Protocol)


class CachingProtocolMeta(_ProtocolMeta):
    """
    Stand-in for ``#!python Protocol``’s base class that caches results of ``#!python
    __instancecheck__``, (which is otherwise [really 🤬ing
    expensive](https://github.com/python/mypy/issues/3186#issuecomment-885718629)). (At
    the time this was introduced, it resulted in about a 5× performance increase for
    unit tests.) The downside is that this will yield unpredictable results for objects
    whose methods don’t stem from any type (e.g., are assembled at runtime). I don’t
    know of any real-world case where that would be true. We’ll jump off that bridge
    when we come to it.
    """

    def __new__(
        mcls: Type[_TT],
        name: str,
        bases: Tuple[Type, ...],
        namespace: Dict[str, Any],
        **kw: Any,
    ) -> _TT:
        # See <https://github.com/python/mypy/issues/9282>
        cls = super().__new__(mcls, name, bases, namespace, **kw)  # type: ignore
        # Prefixing this class member with "_abc_" is necessary to prevent it from being
        # considered part of the Protocol. (See
        # <https://github.com/python/cpython/blob/main/Lib/typing.py>.)
        cache: Dict[Tuple[type, type], bool] = {}
        cls._abc_inst_check_cache = cache

        return cls

    def __instancecheck__(self, inst: Any) -> bool:
        inst_t = type(inst)

        if (self, inst_t) not in self._abc_inst_check_cache:
            self._abc_inst_check_cache[self, inst_t] = super().__instancecheck__(inst)

        return self._abc_inst_check_cache[self, inst_t]


def _assert_isinstance(*num_ts: type, target_t: type) -> None:
    for num_t in num_ts:
        assert isinstance(num_t, _SupportsInt)
        assert isinstance(num_t(0), target_t)


@runtime_checkable
class SupportsAbs(
    _SupportsAbs[_T_co],
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()


# For each Protocol herein, we also define a type annotation of the form "...T" and a
# tuple of classes of the form `_...Cs` such as that which follows. While theoretically
# redundant, in practice these provide more efficient lookups for basic types:
#
#   def do_something(val: Union[str, AbsT]):
#     if instance(val, _AbsCs):  # <- fastest if val is an int, float, or bool
#       ...
#     ...
#
# Two entries are needed to accommodate the asymmetry between type annotations and
# runtime-checkable instances.
_assert_isinstance(int, float, bool, target_t=SupportsAbs)
AbsT = Union[int, float, bool, SupportsAbs]
_AbsCs = (int, float, bool, SupportsAbs)


@runtime_checkable
class SupportsFloat(
    _SupportsFloat,
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()


_assert_isinstance(int, float, bool, target_t=SupportsFloat)
FloatT = Union[int, float, bool, SupportsFloat]
_FloatCs = (int, float, bool, SupportsFloat)


@runtime_checkable
class SupportsInt(
    _SupportsInt,
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()


_assert_isinstance(int, float, bool, target_t=SupportsInt)
IntT = Union[int, float, bool, SupportsInt]
_IntCs = (int, float, bool, SupportsInt)


@runtime_checkable
class SupportsIndex(
    _SupportsIndex,
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()


_assert_isinstance(int, bool, target_t=SupportsIndex)
IndexT = Union[int, bool, SupportsIndex]
_IndexCs = (int, bool, SupportsIndex)


@runtime_checkable
class SupportsArithmetic(
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()

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


_assert_isinstance(int, float, bool, target_t=SupportsArithmetic)
ArithmeticT = Union[int, float, bool, SupportsArithmetic]
_ArithmeticCs = (int, float, bool, SupportsArithmetic)


@runtime_checkable
class SupportsBitwise(
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()

    @abstractmethod
    def __and__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __rand__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __xor__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __rxor__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __or__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __ror__(self, other: IntT) -> _T_co:
        ...

    @abstractmethod
    def __invert__(self) -> _T_co:
        ...


_assert_isinstance(int, bool, target_t=SupportsBitwise)
BitwiseT = Union[int, bool, SupportsBitwise]
_BitwiseCs = (int, bool, SupportsBitwise)


@runtime_checkable
class SupportsOutcome(
    SupportsAbs[_T_co],
    SupportsFloat,
    SupportsArithmetic[_T_co],
    Protocol[_T_co],
    metaclass=CachingProtocolMeta,
):
    __slots__: Tuple[str, ...] = ()

    # Must be able to instantiate it
    @abstractmethod
    def __init__(self, *args: Any, **kw: Any):
        ...

    @abstractmethod
    def __hash__(self) -> int:
        ...


_assert_isinstance(int, float, bool, target_t=SupportsOutcome)
OutcomeT = Union[int, float, bool, SupportsOutcome]
_OutcomeCs = (int, float, bool, SupportsOutcome)

_GetItemT = Union[IndexT, slice]

if sys.version_info >= (3, 8):

    @runtime_checkable
    class _RationalInitializerT(
        Protocol[_T_co],
        metaclass=CachingProtocolMeta,
    ):
        # TODO(posita): See <https://github.com/python/mypy/issues/11013>
        # __slots__: Tuple[str, ...] = ()

        def __call__(self, numerator: int, denominator: int) -> _T_co:
            ...


else:
    _RationalInitializerT = Callable[[int, int], _T_co]


# ---- Functions -----------------------------------------------------------------------


@beartype
def as_int(val: IntT) -> int:
    r"""
    Helper function to losslessly coerce *val* into an ``#!python int``. Raises
    ``#!python TypeError`` if that cannot be done.
    """
    int_val = int(val)

    if int_val != val:
        raise TypeError(f"cannot (losslessly) coerce {val} to an int")

    return int_val


@beartype
def getitems(seq: Sequence[_T], keys: Iterable[_GetItemT]) -> Iterator[_T]:
    for key in keys:
        if isinstance(key, slice):
            yield from __getitem__(seq, key)
        else:
            yield __getitem__(seq, __index__(key))


@beartype
def natural_key(val: Any) -> Tuple[Union[int, str], ...]:
    return tuple(int(s) if s.isdigit() else s for s in re.split(r"(\d+)", str(val)))


@beartype
def sorted_outcomes(vals: Iterable[_T]) -> List[_T]:
    vals = list(vals)

    try:
        vals.sort()
    except TypeError:
        # This is for outcomes that don't support direct comparisons, like symbolic
        # representations
        vals.sort(key=natural_key)

    return vals

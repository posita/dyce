# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from decimal import Decimal
from math import ceil, floor, trunc
from numbers import Integral, Real
from operator import (
    __abs__,
    __add__,
    __and__,
    __eq__,
    __floordiv__,
    __ge__,
    __gt__,
    __invert__,
    __le__,
    __lshift__,
    __lt__,
    __mod__,
    __mul__,
    __ne__,
    __neg__,
    __or__,
    __pos__,
    __pow__,
    __rshift__,
    __sub__,
    __truediv__,
    __xor__,
)
from typing import Optional, Tuple, Union, overload

from dyce.bt import beartype

__all__ = ("Numberwang", "Wangernumb")


# ---- Types ---------------------------------------------------------------------------


_IntegralT = Union[int, Integral]
_RealT = Union[float, Real]


# ---- Classes -------------------------------------------------------------------------


class Numberwang(Integral):
    __slots__: Tuple[str, ...] = ("val",)

    @beartype
    def __init__(self, arg: _RealT = 0):
        self.val = int(arg)

    @beartype
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.val})"

    @beartype
    def __lt__(self, other) -> bool:
        return __lt__(self.val, other)

    @beartype
    def __le__(self, other) -> bool:
        return __le__(self.val, other)

    @beartype
    def __eq__(self, other) -> bool:
        return __eq__(self.val, other)

    @beartype
    def __ne__(self, other) -> bool:
        return __ne__(self.val, other)

    @beartype
    def __ge__(self, other) -> bool:
        return __ge__(self.val, other)

    @beartype
    def __gt__(self, other) -> bool:
        return __gt__(self.val, other)

    @beartype
    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.val))

    @overload
    def __add__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __add__(self, other: _RealT) -> Real:
        ...

    @overload
    def __add__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __add__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__add__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__add__(self.val, other))
        else:
            return __add__(self.val, other)

    @overload
    def __radd__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __radd__(self, other: _RealT) -> Real:
        ...

    @overload
    def __radd__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __radd__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__add__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__add__(other, self.val))
        else:
            return __add__(other, self.val)

    @overload
    def __sub__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __sub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __sub__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __sub__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__sub__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__sub__(self.val, other))
        else:
            return __sub__(self.val, other)

    @overload
    def __rsub__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rsub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rsub__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rsub__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__sub__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__sub__(other, self.val))
        else:
            return __sub__(other, self.val)

    @overload
    def __mul__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __mul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mul__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __mul__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__mul__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mul__(self.val, other))
        else:
            return __mul__(self.val, other)

    @overload
    def __rmul__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rmul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmul__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rmul__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__mul__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mul__(other, self.val))
        else:
            return __mul__(other, self.val)

    @overload
    def __truediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __truediv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __truediv__(self, other):
        if isinstance(other, (float, Numberwang, Wangernumb, Real)):
            return Wangernumb(__truediv__(self.val, other))
        else:
            return __truediv__(self.val, other)

    @overload
    def __rtruediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rtruediv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rtruediv__(self, other):
        if isinstance(other, (float, Numberwang, Wangernumb, Real)):
            return Wangernumb(__truediv__(other, self.val))
        else:
            return __truediv__(other, self.val)

    @overload  # type: ignore
    def __floordiv__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __floordiv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __floordiv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __floordiv__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__floordiv__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__floordiv__(self.val, other))
        else:
            return __floordiv__(self.val, other)

    @overload  # type: ignore
    def __rfloordiv__(self, other: _IntegralT) -> Integral:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: _RealT) -> Real:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rfloordiv__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__floordiv__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__floordiv__(other, self.val))
        else:
            return __floordiv__(other, self.val)

    @overload
    def __mod__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __mod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mod__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __mod__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__mod__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mod__(self.val, other))
        else:
            return __mod__(self.val, other)

    @overload
    def __rmod__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rmod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmod__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rmod__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__mod__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mod__(other, self.val))
        else:
            return __mod__(other, self.val)

    @overload  # type: ignore
    def __pow__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __pow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __pow__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __pow__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__pow__(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__pow__(self.val, other))
        else:
            return __pow__(self.val, other)

    @overload
    def __rpow__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rpow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rpow__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rpow__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__pow__(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(__pow__(other, self.val))
        else:
            return __pow__(other, self.val)

    @beartype
    def __lshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__lshift__(self.val, other))
        elif isinstance(other, Integral):
            return __lshift__(self.val, other)
        else:
            return NotImplemented

    @beartype
    def __rlshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__lshift__(other, self.val))
        elif isinstance(other, Integral):
            return __lshift__(other, self.val)
        else:
            return NotImplemented

    @beartype
    def __rshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__rshift__(self.val, other))
        elif isinstance(other, Integral):
            return __rshift__(self.val, other)
        else:
            return NotImplemented

    @beartype
    def __rrshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__rshift__(other, self.val))
        elif isinstance(other, Integral):
            return __rshift__(other, self.val)
        else:
            return NotImplemented

    @beartype
    def __and__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__and__(self.val, other))
        elif isinstance(other, Integral):
            return __and__(self.val, other)
        else:
            return NotImplemented

    @beartype
    def __rand__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__and__(other, self.val))
        elif isinstance(other, Integral):
            return __and__(other, self.val)
        else:
            return NotImplemented

    @beartype
    def __xor__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__xor__(self.val, other))
        elif isinstance(other, Integral):
            return __xor__(self.val, other)
        else:
            return NotImplemented

    @beartype
    def __rxor__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__xor__(other, self.val))
        elif isinstance(other, Integral):
            return __xor__(other, self.val)
        else:
            return NotImplemented

    @beartype
    def __or__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__or__(self.val, other))
        elif isinstance(other, Integral):
            return __or__(self.val, other)
        else:
            return NotImplemented

    @beartype
    def __ror__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(__or__(other, self.val))
        elif isinstance(other, Integral):
            return __or__(other, self.val)
        else:
            return NotImplemented

    @beartype
    def __neg__(self) -> "Numberwang":
        return Numberwang(__neg__(self.val))

    @beartype
    def __pos__(self) -> "Numberwang":
        return Numberwang(__pos__(self.val))

    @beartype
    def __abs__(self) -> "Numberwang":
        return Numberwang(__abs__(self.val))

    @beartype
    def __invert__(self) -> "Numberwang":
        return Numberwang(__invert__(self.val))

    @beartype
    def __int__(self) -> int:
        return self.val

    @beartype
    def __round__(self, ndigits: Optional[_IntegralT] = None) -> int:
        if ndigits is None:
            return round(self.val)
        else:
            return round(self.val, int(ndigits))

    @beartype
    def __trunc__(self) -> int:
        return trunc(self.val)

    @beartype
    def __floor__(self) -> int:
        return floor(self.val)

    @beartype
    def __ceil__(self) -> int:
        return ceil(self.val)


Integral.register(Numberwang)
assert isinstance(Numberwang(0), Real)
assert isinstance(Numberwang(0), Integral)


class Wangernumb(Real):
    __slots__: Tuple[str, ...] = ("val",)

    @beartype
    def __init__(self, arg: _RealT = 0):
        self.val = float(arg)

    @beartype
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.val})"

    @beartype
    def __lt__(self, other) -> bool:
        return __lt__(self.val, other)

    @beartype
    def __le__(self, other) -> bool:
        return __le__(self.val, other)

    @beartype
    def __eq__(self, other) -> bool:
        return __eq__(self.val, other)

    @beartype
    def __ne__(self, other) -> bool:
        return __ne__(self.val, other)

    @beartype
    def __ge__(self, other) -> bool:
        return __ge__(self.val, other)

    @beartype
    def __gt__(self, other) -> bool:
        return __gt__(self.val, other)

    @beartype
    def __hash__(self) -> int:
        return hash(self.val)

    @overload
    def __add__(self, other: _RealT) -> Real:
        ...

    @overload
    def __add__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __add__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__add__(self.val, other))
        else:
            return __add__(self.val, other)

    @overload
    def __radd__(self, other: _RealT) -> Real:
        ...

    @overload
    def __radd__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __radd__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__add__(other, self.val))
        else:
            return __add__(other, self.val)

    @overload
    def __sub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __sub__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __sub__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__sub__(self.val, other))
        else:
            return __sub__(self.val, other)

    @overload
    def __rsub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rsub__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rsub__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__sub__(other, self.val))
        else:
            return __sub__(other, self.val)

    @overload
    def __mul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mul__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __mul__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mul__(self.val, other))
        else:
            return __mul__(self.val, other)

    @overload
    def __rmul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmul__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rmul__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mul__(other, self.val))
        else:
            return __mul__(other, self.val)

    @overload
    def __truediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __truediv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __truediv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__truediv__(self.val, other))
        else:
            return __truediv__(self.val, other)

    @overload
    def __rtruediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rtruediv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rtruediv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__truediv__(other, self.val))
        else:
            return __truediv__(other, self.val)

    @overload  # type: ignore
    def __floordiv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __floordiv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __floordiv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__floordiv__(self.val, other))
        else:
            return __floordiv__(self.val, other)

    @overload  # type: ignore
    def __rfloordiv__(self, other: _RealT) -> Real:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rfloordiv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__floordiv__(other, self.val))
        else:
            return __floordiv__(other, self.val)

    @overload
    def __mod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mod__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __mod__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mod__(self.val, other))
        else:
            return __mod__(self.val, other)

    @overload
    def __rmod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmod__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rmod__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(__mod__(other, self.val))
        else:
            return __mod__(other, self.val)

    @overload
    def __pow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __pow__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __pow__(self, other):
        val = __pow__(self.val, other)

        if isinstance(val, Real):
            return Wangernumb(val)
        else:
            return val

    @overload
    def __rpow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rpow__(self, other: Decimal) -> Decimal:
        ...

    @beartype
    def __rpow__(self, other):
        val = __pow__(other, self.val)

        if isinstance(val, Real):
            return Wangernumb(val)
        else:
            return val

    @beartype
    def __neg__(self) -> Real:
        return Wangernumb(__neg__(self.val))

    @beartype
    def __pos__(self) -> Real:
        return Wangernumb(__pos__(self.val))

    @beartype
    def __abs__(self) -> Real:
        return Wangernumb(__abs__(self.val))

    @beartype
    def __float__(self) -> float:
        return self.val

    @overload  # type: ignore
    def __round__(self) -> int:
        ...

    @overload
    def __round__(self, ndigits: _IntegralT) -> float:
        ...

    @beartype
    def __round__(self, ndigits: Optional[_IntegralT] = None) -> Union[int, float]:  # type: ignore
        if ndigits is None:
            return round(self.val)
        else:
            return round(self.val, int(ndigits))

    @beartype
    def __trunc__(self) -> int:
        return trunc(self.val)

    @beartype
    def __floor__(self) -> int:
        return floor(self.val)

    @beartype
    def __ceil__(self) -> int:
        return ceil(self.val)


Real.register(Wangernumb)
assert isinstance(Wangernumb(0), Real)

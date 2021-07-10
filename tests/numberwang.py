from decimal import Decimal
from math import ceil, floor, trunc
from numbers import Integral, Real
from operator import abs as op_abs
from operator import add as op_add
from operator import and_ as op_and
from operator import eq as op_eq
from operator import floordiv as op_floordiv
from operator import ge as op_ge
from operator import gt as op_gt
from operator import invert as op_invert
from operator import le as op_le
from operator import lshift as op_lshift
from operator import lt as op_lt
from operator import mod as op_mod
from operator import mul as op_mul
from operator import ne as op_ne
from operator import neg as op_neg
from operator import or_ as op_or
from operator import pos as op_pos
from operator import pow as op_pow
from operator import rshift as op_rshift
from operator import sub as op_sub
from operator import truediv as op_truediv
from operator import xor as op_xor
from typing import Union, overload

__all__ = ("Numberwang", "Wangernumb")


# ---- Types ---------------------------------------------------------------------------


_IntegralT = Union[int, Integral]
_RealT = Union[float, Real]


# ---- Classes -------------------------------------------------------------------------


class Numberwang(Integral):
    def __init__(self, arg: _RealT = 0):
        self.val = int(arg)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.val})"

    def __lt__(self, other) -> bool:
        return op_lt(self.val, other)

    def __le__(self, other) -> bool:
        return op_le(self.val, other)

    def __eq__(self, other) -> bool:
        return op_eq(self.val, other)

    def __ne__(self, other) -> bool:
        return op_ne(self.val, other)

    def __ge__(self, other) -> bool:
        return op_ge(self.val, other)

    def __gt__(self, other) -> bool:
        return op_gt(self.val, other)

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

    def __add__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_add(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_add(self.val, other))
        else:
            return op_add(self.val, other)

    @overload
    def __radd__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __radd__(self, other: _RealT) -> Real:
        ...

    @overload
    def __radd__(self, other: Decimal) -> Decimal:
        ...

    def __radd__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_add(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_add(other, self.val))
        else:
            return op_add(other, self.val)

    @overload
    def __sub__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __sub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __sub__(self, other: Decimal) -> Decimal:
        ...

    def __sub__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_sub(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_sub(self.val, other))
        else:
            return op_sub(self.val, other)

    @overload
    def __rsub__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rsub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rsub__(self, other: Decimal) -> Decimal:
        ...

    def __rsub__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_sub(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_sub(other, self.val))
        else:
            return op_sub(other, self.val)

    @overload
    def __mul__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __mul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mul__(self, other: Decimal) -> Decimal:
        ...

    def __mul__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_mul(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mul(self.val, other))
        else:
            return op_mul(self.val, other)

    @overload
    def __rmul__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rmul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmul__(self, other: Decimal) -> Decimal:
        ...

    def __rmul__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_mul(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mul(other, self.val))
        else:
            return op_mul(other, self.val)

    @overload
    def __truediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __truediv__(self, other: Decimal) -> Decimal:
        ...

    def __truediv__(self, other):
        if isinstance(other, (float, Numberwang, Wangernumb, Real)):
            return Wangernumb(op_truediv(self.val, other))
        else:
            return op_truediv(self.val, other)

    @overload
    def __rtruediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rtruediv__(self, other: Decimal) -> Decimal:
        ...

    def __rtruediv__(self, other):
        if isinstance(other, (float, Numberwang, Wangernumb, Real)):
            return Wangernumb(op_truediv(other, self.val))
        else:
            return op_truediv(other, self.val)

    @overload  # type: ignore
    def __floordiv__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __floordiv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __floordiv__(self, other: Decimal) -> Decimal:
        ...

    def __floordiv__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_floordiv(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_floordiv(self.val, other))
        else:
            return op_floordiv(self.val, other)

    @overload  # type: ignore
    def __rfloordiv__(self, other: _IntegralT) -> Integral:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: _RealT) -> Real:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: Decimal) -> Decimal:
        ...

    def __rfloordiv__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_floordiv(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_floordiv(other, self.val))
        else:
            return op_floordiv(other, self.val)

    @overload
    def __mod__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __mod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mod__(self, other: Decimal) -> Decimal:
        ...

    def __mod__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_mod(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mod(self.val, other))
        else:
            return op_mod(self.val, other)

    @overload
    def __rmod__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rmod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmod__(self, other: Decimal) -> Decimal:
        ...

    def __rmod__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_mod(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mod(other, self.val))
        else:
            return op_mod(other, self.val)

    @overload  # type: ignore
    def __pow__(  # pylint: disable=signature-differs
        self, other: _IntegralT
    ) -> Integral:
        ...

    @overload
    def __pow__(self, other: _RealT) -> Real:  # pylint: disable=signature-differs
        ...

    @overload
    def __pow__(self, other: Decimal) -> Decimal:  # pylint: disable=signature-differs
        ...

    def __pow__(self, other):  # pylint: disable=signature-differs
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_pow(self.val, other))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_pow(self.val, other))
        else:
            return op_pow(self.val, other)

    @overload
    def __rpow__(self, other: _IntegralT) -> Integral:
        ...

    @overload
    def __rpow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rpow__(self, other: Decimal) -> Decimal:
        ...

    def __rpow__(self, other):
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_pow(other, self.val))
        elif isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_pow(other, self.val))
        else:
            return op_pow(other, self.val)

    def __lshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_lshift(self.val, other))
        elif isinstance(other, Integral):
            return op_lshift(self.val, other)
        else:
            return NotImplemented

    def __rlshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_lshift(other, self.val))
        elif isinstance(other, Integral):
            return op_lshift(other, self.val)
        else:
            return NotImplemented

    def __rshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_rshift(self.val, other))
        elif isinstance(other, Integral):
            return op_rshift(self.val, other)
        else:
            return NotImplemented

    def __rrshift__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_rshift(other, self.val))
        elif isinstance(other, Integral):
            return op_rshift(other, self.val)
        else:
            return NotImplemented

    def __and__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_and(self.val, other))
        elif isinstance(other, Integral):
            return op_and(self.val, other)
        else:
            return NotImplemented

    def __rand__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_and(other, self.val))
        elif isinstance(other, Integral):
            return op_and(other, self.val)
        else:
            return NotImplemented

    def __xor__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_xor(self.val, other))
        elif isinstance(other, Integral):
            return op_xor(self.val, other)
        else:
            return NotImplemented

    def __rxor__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_xor(other, self.val))
        elif isinstance(other, Integral):
            return op_xor(other, self.val)
        else:
            return NotImplemented

    def __or__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_or(self.val, other))
        elif isinstance(other, Integral):
            return op_or(self.val, other)
        else:
            return NotImplemented

    def __ror__(self, other) -> Integral:
        if isinstance(other, (int, Numberwang)):
            return Numberwang(op_or(other, self.val))
        elif isinstance(other, Integral):
            return op_or(other, self.val)
        else:
            return NotImplemented

    def __neg__(self) -> "Numberwang":
        return Numberwang(op_neg(self.val))

    def __pos__(self) -> "Numberwang":
        return Numberwang(op_pos(self.val))

    def __abs__(self) -> "Numberwang":
        return Numberwang(op_abs(self.val))

    def __invert__(self) -> "Numberwang":
        return Numberwang(op_invert(self.val))

    def __int__(self) -> int:
        return self.val

    def __round__(self, ndigits: _IntegralT = None) -> "Numberwang":  # type: ignore
        if ndigits is None:
            return Numberwang(round(self.val))
        else:
            return Numberwang(round(self.val, int(ndigits)))

    def __trunc__(self) -> "Numberwang":  # type: ignore
        return Numberwang(trunc(self.val))

    def __floor__(self) -> "Numberwang":  # type: ignore
        return Numberwang(floor(self.val))

    def __ceil__(self) -> "Numberwang":  # type: ignore
        return Numberwang(ceil(self.val))


Integral.register(Numberwang)
assert isinstance(Numberwang(0), Real)
assert isinstance(Numberwang(0), Integral)


class Wangernumb(Real):
    def __init__(self, arg: _RealT = 0):
        self.val = float(arg)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.val})"

    def __lt__(self, other) -> bool:
        return op_lt(self.val, other)

    def __le__(self, other) -> bool:
        return op_le(self.val, other)

    def __eq__(self, other) -> bool:
        return op_eq(self.val, other)

    def __ne__(self, other) -> bool:
        return op_ne(self.val, other)

    def __ge__(self, other) -> bool:
        return op_ge(self.val, other)

    def __gt__(self, other) -> bool:
        return op_gt(self.val, other)

    def __hash__(self) -> int:
        return hash(self.val)

    @overload
    def __add__(self, other: _RealT) -> Real:
        ...

    @overload
    def __add__(self, other: Decimal) -> Decimal:
        ...

    def __add__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_add(self.val, other))
        else:
            return op_add(self.val, other)

    @overload
    def __radd__(self, other: _RealT) -> Real:
        ...

    @overload
    def __radd__(self, other: Decimal) -> Decimal:
        ...

    def __radd__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_add(other, self.val))
        else:
            return op_add(other, self.val)

    @overload
    def __sub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __sub__(self, other: Decimal) -> Decimal:
        ...

    def __sub__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_sub(self.val, other))
        else:
            return op_sub(self.val, other)

    @overload
    def __rsub__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rsub__(self, other: Decimal) -> Decimal:
        ...

    def __rsub__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_sub(other, self.val))
        else:
            return op_sub(other, self.val)

    @overload
    def __mul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mul__(self, other: Decimal) -> Decimal:
        ...

    def __mul__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mul(self.val, other))
        else:
            return op_mul(self.val, other)

    @overload
    def __rmul__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmul__(self, other: Decimal) -> Decimal:
        ...

    def __rmul__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mul(other, self.val))
        else:
            return op_mul(other, self.val)

    @overload
    def __truediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __truediv__(self, other: Decimal) -> Decimal:
        ...

    def __truediv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_truediv(self.val, other))
        else:
            return op_truediv(self.val, other)

    @overload
    def __rtruediv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rtruediv__(self, other: Decimal) -> Decimal:
        ...

    def __rtruediv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_truediv(other, self.val))
        else:
            return op_truediv(other, self.val)

    @overload  # type: ignore
    def __floordiv__(self, other: _RealT) -> Real:
        ...

    @overload
    def __floordiv__(self, other: Decimal) -> Decimal:
        ...

    def __floordiv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_floordiv(self.val, other))
        else:
            return op_floordiv(self.val, other)

    @overload  # type: ignore
    def __rfloordiv__(self, other: _RealT) -> Real:  # type: ignore
        ...

    @overload
    def __rfloordiv__(self, other: Decimal) -> Decimal:
        ...

    def __rfloordiv__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_floordiv(other, self.val))
        else:
            return op_floordiv(other, self.val)

    @overload
    def __mod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __mod__(self, other: Decimal) -> Decimal:
        ...

    def __mod__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mod(self.val, other))
        else:
            return op_mod(self.val, other)

    @overload
    def __rmod__(self, other: _RealT) -> Real:
        ...

    @overload
    def __rmod__(self, other: Decimal) -> Decimal:
        ...

    def __rmod__(self, other):
        if isinstance(other, (float, Wangernumb)):
            return Wangernumb(op_mod(other, self.val))
        else:
            return op_mod(other, self.val)

    @overload
    def __pow__(self, other: _RealT) -> Real:
        ...

    @overload
    def __pow__(self, other: Decimal) -> Decimal:
        ...

    def __pow__(self, other):
        val = op_pow(self.val, other)

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

    def __rpow__(self, other):
        val = op_pow(other, self.val)

        if isinstance(val, Real):
            return Wangernumb(val)
        else:
            return val

    def __neg__(self) -> Real:
        return Wangernumb(op_neg(self.val))

    def __pos__(self) -> Real:
        return Wangernumb(op_pos(self.val))

    def __abs__(self) -> Real:
        return Wangernumb(op_abs(self.val))

    def __float__(self) -> float:
        return self.val

    @overload  # type: ignore
    def __round__(self) -> Numberwang:  # pylint: disable=signature-differs
        ...

    @overload
    def __round__(  # pylint: disable=signature-differs
        self, ndigits: _IntegralT
    ) -> Real:
        ...

    def __round__(self, ndigits: _IntegralT = None) -> Real:
        if ndigits is None:
            return Numberwang(round(self.val))
        else:
            return Wangernumb(round(self.val, int(ndigits)))

    def __trunc__(self) -> _IntegralT:  # type: ignore
        return Numberwang(trunc(self.val))

    def __floor__(self) -> Real:  # type: ignore
        return Wangernumb(floor(self.val))

    def __ceil__(self) -> Real:  # type: ignore
        return Wangernumb(ceil(self.val))


Real.register(Wangernumb)
assert isinstance(Wangernumb(0), Real)

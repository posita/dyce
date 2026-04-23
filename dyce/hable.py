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

from typing import TypeVar, overload

import optype

from .h import H, HableT, _flatten_to_h

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")

__all__ = ("HableOpsMixin",)


class HableOpsMixin(HableT[_T_co]):
    r"""
    An abstract mixin that provides all [`H`][dyce.H] math operators for types implementing the [`HableT`][dyce.HableT] protocol.
    Each operator delegates to the [`H`][dyce.H] object returned by [`h()`][dyce.HableT.h].

    This class also inherits from [`HableT`][dyce.HableT].
    Subclasses are required to define [`h()`][dyce.HableT.h].
    """

    __slots__ = ()

    # ---- Forward operators -----------------------------------------------------------

    @overload
    def __add__(
        self: "HableOpsMixin[optype.CanAdd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __add__(
        self: "HableOpsMixin[_T]", rhs: optype.CanAdd[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __add__(self, rhs: object) -> H[object]:
        return self.h().__add__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __sub__(
        self: "HableOpsMixin[optype.CanSub[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __sub__(
        self: "HableOpsMixin[_T]", rhs: optype.CanSub[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __sub__(self, rhs: object) -> H[object]:
        return self.h().__sub__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __mul__(
        self: "HableOpsMixin[optype.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __mul__(
        self: "HableOpsMixin[_T]", rhs: optype.CanMul[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __mul__(self, rhs: object) -> H[object]:
        return self.h().__mul__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __truediv__(
        self: "HableOpsMixin[optype.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __truediv__(
        self: "HableOpsMixin[_T]", rhs: optype.CanTruediv[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __truediv__(self, rhs: object) -> H[object]:
        return self.h().__truediv__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __floordiv__(
        self: "HableOpsMixin[optype.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __floordiv__(
        self: "HableOpsMixin[_T]", rhs: optype.CanFloordiv[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __floordiv__(self, rhs: object) -> H[object]:
        return self.h().__floordiv__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __mod__(
        self: "HableOpsMixin[optype.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __mod__(
        self: "HableOpsMixin[_T]", rhs: optype.CanMod[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __mod__(self, rhs: object) -> H[object]:
        return self.h().__mod__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __pow__(
        self: "HableOpsMixin[optype.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __pow__(
        self: "HableOpsMixin[_T]", rhs: optype.CanPow2[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __pow__(self, rhs: object) -> H[object]:
        return self.h().__pow__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __lshift__(
        self: "HableOpsMixin[optype.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __lshift__(
        self: "HableOpsMixin[_T]", rhs: optype.CanLshift[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __lshift__(self, rhs: object) -> H[object]:
        return self.h().__lshift__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __rshift__(
        self: "HableOpsMixin[optype.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rshift__(
        self: "HableOpsMixin[_T]", rhs: optype.CanRshift[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rshift__(self, rhs: object) -> H[object]:
        return self.h().__rshift__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __and__(
        self: "HableOpsMixin[optype.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __and__(
        self: "HableOpsMixin[_T]", rhs: optype.CanAnd[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __and__(self, rhs: object) -> H[object]:
        return self.h().__and__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __or__(
        self: "HableOpsMixin[optype.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __or__(
        self: "HableOpsMixin[_T]", rhs: optype.CanOr[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __or__(self, rhs: object) -> H[object]:
        return self.h().__or__(_flatten_to_h(rhs))  # type: ignore[operator]

    @overload
    def __xor__(
        self: "HableOpsMixin[optype.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __xor__(
        self: "HableOpsMixin[_T]", rhs: optype.CanXor[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __xor__(self, rhs: object) -> H[object]:
        return self.h().__xor__(_flatten_to_h(rhs))  # type: ignore[operator]

    # ---- Reflected operators ---------------------------------------------------------

    @overload
    def __radd__(
        self: "HableOpsMixin[optype.CanRAdd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __radd__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRAdd[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __radd__(self, lhs: object) -> H[object]:
        return self.h().__radd__(lhs)  # type: ignore[operator]

    @overload
    def __rsub__(
        self: "HableOpsMixin[optype.CanRSub[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rsub__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRSub[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rsub__(self, lhs: object) -> H[object]:
        return self.h().__rsub__(lhs)  # type: ignore[operator]

    @overload
    def __rmul__(
        self: "HableOpsMixin[optype.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rmul__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRMul[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rmul__(self, lhs: object) -> H[object]:
        return self.h().__rmul__(lhs)  # type: ignore[operator]

    @overload
    def __rtruediv__(
        self: "HableOpsMixin[optype.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rtruediv__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRTruediv[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rtruediv__(self, lhs: object) -> H[object]:
        return self.h().__rtruediv__(lhs)  # type: ignore[operator]

    @overload
    def __rfloordiv__(
        self: "HableOpsMixin[optype.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rfloordiv__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRFloordiv[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rfloordiv__(self, lhs: object) -> H[object]:
        return self.h().__rfloordiv__(lhs)  # type: ignore[operator]

    @overload
    def __rmod__(
        self: "HableOpsMixin[optype.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rmod__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRMod[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rmod__(self, lhs: object) -> H[object]:
        return self.h().__rmod__(lhs)  # type: ignore[operator]

    @overload
    def __rpow__(
        self: "HableOpsMixin[optype.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rpow__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRPow[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rpow__(self, lhs: object) -> H[object]:
        return self.h().__rpow__(lhs)  # type: ignore[operator]

    @overload
    def __rlshift__(
        self: "HableOpsMixin[optype.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rlshift__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRLshift[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rlshift__(self, lhs: object) -> H[object]:
        return self.h().__rlshift__(lhs)  # type: ignore[operator]

    @overload
    def __rrshift__(
        self: "HableOpsMixin[optype.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rrshift__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRRshift[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rrshift__(self, lhs: object) -> H[object]:
        return self.h().__rrshift__(lhs)  # type: ignore[operator]

    @overload
    def __rand__(
        self: "HableOpsMixin[optype.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rand__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRAnd[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rand__(self, lhs: object) -> H[object]:
        return self.h().__rand__(lhs)  # type: ignore[operator]

    @overload
    def __ror__(
        self: "HableOpsMixin[optype.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __ror__(
        self: "HableOpsMixin[_T]", lhs: optype.CanROr[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __ror__(self, lhs: object) -> H[object]:
        return self.h().__ror__(lhs)  # type: ignore[operator]

    @overload
    def __rxor__(
        self: "HableOpsMixin[optype.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> H[_ResultT]: ...
    @overload
    def __rxor__(
        self: "HableOpsMixin[_T]", lhs: optype.CanRXor[_T, _ResultT]
    ) -> H[_ResultT]: ...
    def __rxor__(self, lhs: object) -> H[object]:
        return self.h().__rxor__(lhs)  # type: ignore[operator]

    # ---- Unary operators -------------------------------------------------------------

    def __neg__(self: "HableOpsMixin[optype.CanNeg[_ResultT]]") -> H[_ResultT]:
        return self.h().__neg__()

    def __pos__(self: "HableOpsMixin[optype.CanPos[_ResultT]]") -> H[_ResultT]:
        return self.h().__pos__()

    def __abs__(self: "HableOpsMixin[optype.CanAbs[_ResultT]]") -> H[_ResultT]:
        return self.h().__abs__()

    def __invert__(self: "HableOpsMixin[optype.CanInvert[_ResultT]]") -> H[_ResultT]:
        return self.h().__invert__()

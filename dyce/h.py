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

import math
import os
import warnings
from abc import abstractmethod
from collections import Counter
from collections.abc import (
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Mapping,
    Sequence,
    ValuesView,
)
from fractions import Fraction
from itertools import groupby
from itertools import product as iproduct
from types import NotImplementedType
from typing import (
    Any,
    Literal,
    Never,
    Protocol,
    Self,
    SupportsFloat,
    SupportsInt,
    TypeVar,
    cast,
    overload,
    runtime_checkable,
)

import optype as ot

from . import rng
from .lifecycle import deprecated, experimental
from .types import (
    Sentinel,
    SentinelT,
    lossless_int,
    lossless_int_or_not_implemented,
    natural_key,
    nobeartype,
)

__all__ = ("H", "HableT")

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_OtherT = TypeVar("_OtherT")
_ResultT = TypeVar("_ResultT")
_ConvolvableT = TypeVar("_ConvolvableT", bound=ot.CanAddSame)

try:
    _ROW_WIDTH = int(os.environ["COLUMNS"])
except (KeyError, ValueError):
    _ROW_WIDTH = 65


class H(Mapping[_T_co, int], Iterable[_T_co]):  # type: ignore[type-var]
    r"""
    <!-- BEGIN MONKEY PATCH --
    For typing.

        >>> import sympy.abc  # type: ignore[import-untyped]

      -- END MONKEY PATCH -->

    An immutable mapping for use as a histogram which supports arithmetic operations.
    This is useful for modeling discrete outcomes, like individual dice.
    `#!python H` objects encode finite discrete probability distributions as integer counts without any denominator.

    !!! info

        The lack of an explicit denominator is intentional and has two benefits.
        First, a denominator is redundant.
        Without it, one never has to worry about probabilities summing to one (e.g., via miscalculation, floating point error, etc.).
        Second (and perhaps more importantly), sometimes one wants to have an insight into non-reduced counts, not just probabilities.
        If needed, probabilities can always be derived, as shown below.
        While a rational abstraction (e.g., `#!python fractions.Fraction`) could have been used, `#!python int`s typically perform better under most circumstances.

    The [initializer][dyce.H.__init__] takes a single argument, *init_val*.
    In its most explicit form, *init_val* maps outcome values to counts.

    Modeling a single six-sided die (`1d6`) can be expressed as:

        >>> from dyce import H
        >>> d6 = H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    Two shorthands are provided.
    If *init_val* is an operable of numbers, counts of 1 are assumed and outcomes are sorted.

        >>> H(range(6, 0, -1))
        H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1})

    Repeated items are accumulated, as one would expect.

        >>> lo_var_d6 = H((5, 4, 4, 3, 3, 2))
        >>> lo_var_d6
        H({2: 1, 3: 2, 4: 2, 5: 1})

    If *init_val* is an `#!python int` (and ***only*** an `#!python int`),it is shorthand for creating a sequential range `#!math \left[ {1} .. {init\_val} \right]` (or `#!math \left[ {init\_val} .. {-1} \right]` if *init_val* is negative).

        >>> H(8)
        H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1})
        >>> H(0)
        H({})
        >>> H(-4.0)  # type: ignore[call-overload] # ty: ignore[no-matching-overload]
        Traceback (most recent call last):
          ...
        TypeError: scalar init_val must be int; use explicit Mapping or Iterable for 'float' outcomes

    !!! note "A work-around"

        You can usually find a way to coerce the shorthand into the correct type, if needed:

            >>> import sympy.abc
            >>> (H(-4) + 0.0) * sympy.abc.x
            H({-1.0*x: 1, -2.0*x: 1, -3.0*x: 1, -4.0*x: 1})

    Histograms are maps, so they can interact with other map types.

        >>> lo_var_d6 == {2: 1, 3: 2, 4: 2, 5: 1}
        True
        >>> lo_var_d6 != {}
        True
        >>> from collections import Counter
        >>> lo_var_d6 == Counter(lo_var_d6)
        True

    Simple indexes can be used to look up an outcome’s count.

        >>> lo_var_d6[3]
        2

    Most arithmetic operators are supported and do what one would expect.
    If the operand is a number, the operator applies to the outcomes.

        >>> d6 + 4
        H({5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1})

        >>> d6 * -1
        H({-6: 1, -5: 1, -4: 1, -3: 1, -2: 1, -1: 1})
        >>> d6 * -1 == -d6
        True
        >>> d6 * -1 == H(-6)
        True

    If the operand is another histogram, the operator applies to the Cartesian product of the outcomes in each histogram, and respective counts are multiplied.
    Modeling the sum of two six-sided dice (`2d6`) can be expressed as:

        >>> d6 + d6
        H({2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1})
        >>> print((d6 + d6).format(width=65))
        avg |    7.00
        std |    2.42
        var |    5.83
          2 |   2.78% |#
          3 |   5.56% |##
          4 |   8.33% |####
          5 |  11.11% |#####
          6 |  13.89% |######
          7 |  16.67% |########
          8 |  13.89% |######
          9 |  11.11% |#####
         10 |   8.33% |####
         11 |   5.56% |##
         12 |   2.78% |#

    To sum `#!math {n}` identical histograms, the matrix multiplication operator (`@`) provides a shorthand.

        >>> 3 @ d6 == d6 + d6 + d6
        True

    Unary operators are also supported:

        >>> ~d6
        H({-7: 1, -6: 1, -5: 1, -4: 1, -3: 1, -2: 1})
        >>> abs(-d6) == d6
        True

    The `#!python len` built-in function can be used to show the number of distinct outcomes.

        >>> len(2 @ d6)
        11

    The [`total` property][dyce.H.total] can be used to compute the total number of combinations and each outcome’s probability.

        >>> from fractions import Fraction
        >>> (2 @ d6).total
        36
        >>> [
        ...     (outcome, Fraction(count, (2 @ d6).total))
        ...     for outcome, count in (2 @ d6).items()
        ... ]
        [(2, Fraction(1, 36)), (3, Fraction(1, 18)), (4, Fraction(1, 12)), (5, Fraction(1, 9)), (6, Fraction(5, 36)), (7, Fraction(1, 6)), ..., (12, Fraction(1, 36))]

    Histograms provide common comparators (e.g., [`eq`][dyce.H.eq] [`ne`][dyce.H.ne], etc.).
    One way to count how often a first six-sided die shows a different face than a second is:

        >>> d6.ne(d6)
        H({False: 6, True: 30})
        >>> print(d6.ne(d6).format(width=65))
          avg |    0.83
          std |    0.37
          var |    0.14
        False |  16.67% |########
         True |  83.33% |########################################

    Or, how often a first six-sided die shows a face less than a second is:

        >>> d6.lt(d6)
        H({False: 21, True: 15})
        >>> print(d6.lt(d6).format(width=65))
          avg |    0.42
          std |    0.49
          var |    0.24
        False |  58.33% |############################
         True |  41.67% |####################

    Or how often at least one `#!python 2` will show when rolling four six-sided dice:

        >>> d6_eq2 = d6.eq(2)
        >>> d6_eq2  # how often a 2 shows on a single six-sided die
        H({False: 5, True: 1})
        >>> 4 @ d6_eq2  # number of 2s showing among 4d6
        H({0: 625, 1: 500, 2: 150, 3: 20, 4: 1})
        >>> (4 @ d6_eq2).ge(1)  # how often at least one 2 shows on 4d6
        H({False: 625, True: 671})
        >>> print((4 @ d6_eq2).ge(1).format(width=65))
          avg |    0.52
          std |    0.50
          var |    0.25
        False |  48.23% |#######################
         True |  51.77% |########################

    !!! bug "Mind your parentheses"

        Parentheses are often necessary to enforce the desired order of operations.
        This is most often an issue with the `#!python @` operator, because it behaves differently than the `d` operator in most dedicated grammars.
        More specifically, in Python, `#!python @` has a [lower precedence](https://docs.python.org/3/reference/expressions.html#operator-precedence) than `#!python .` and `#!python […]`.

            >>> 2 @ d6[7]  # type: ignore
            Traceback (most recent call last):
              ...
            KeyError: 7
            >>> 2 @ d6.le(7)  # probably not what was intended
            H({2: 36})
            >>> 2 @ d6.le(7) == 2 @ (d6.le(7))
            True

            >>> (2 @ d6)[7]
            6
            >>> (2 @ d6).le(7)
            H({False: 15, True: 21})
            >>> 2 @ d6.le(7) == (2 @ d6).le(7)
            False

    Counts are generally accumulated without reduction.
    To reduce, call the [`lowest_terms` method][dyce.H.lowest_terms].

        >>> d6.ge(4)
        H({False: 3, True: 3})
        >>> d6.ge(4).lowest_terms()
        H({False: 1, True: 1})

    Testing equivalence implicitly performs reductions of operands.

        >>> d6.ge(4) == d6.ge(4).lowest_terms()
        True
    """

    __slots__ = (
        "_h",
        "_hash",
        "_order_stat_funcs_by_n",
        "_total",
    )

    @overload
    def __init__(
        self: "H[Never]", init_val: Mapping[Never, SupportsInt], /
    ) -> None: ...
    @overload
    def __init__(self: "H[_T]", init_val: Mapping[_T, SupportsInt], /) -> None: ...
    @overload
    def __init__(self: "H[Never]", init_val: Iterable[Never], /) -> None: ...
    @overload
    def __init__(self: "H[_T]", init_val: Iterable[_T], /) -> None: ...
    @overload
    def __init__(self: "H[Never]", init_val: Literal[0, False], /) -> None: ...
    @overload
    def __init__(self: "H[int]", init_val: int, /) -> None: ...
    def __init__(self, init_val: Any, /) -> None:
        r"""Constructor."""
        self._h: dict[_T_co, int]
        self._hash: int | None = None
        self._order_stat_funcs_by_n: dict[int, Callable[[int], H[Any]]] = {}
        self._total: int | None = None

        def _sorted_items_iter(
            items: Sequence[tuple[Any, SupportsInt]],
        ) -> Iterator[tuple[Any, int]]:
            sorted_items = [(k, lossless_int(v)) for k, v in items]
            try:
                sorted_items.sort()
            except TypeError:
                sorted_items.sort(key=lambda item: natural_key(item[0]))
            for outcome, count in sorted_items:
                if count < 0:
                    raise ValueError(f"count for {outcome} cannot be negative")
                yield (outcome, count)

        if isinstance(init_val, Iterable):
            if isinstance(init_val, Mapping):
                self._h = dict(_sorted_items_iter(list(init_val.items())))  # ty: ignore[invalid-argument-type]
            else:
                c: Counter[_T_co] = Counter(init_val)
                self._h = dict(_sorted_items_iter(list(c.items())))
        elif isinstance(init_val, int):
            n = abs(init_val)
            if init_val > 0:
                self._h = dict(_sorted_items_iter([(i, 1) for i in range(1, n + 1)]))
            elif init_val < 0:
                self._h = dict(_sorted_items_iter([(i, 1) for i in range(-n, 0)]))
            else:
                self._h = {}
        else:
            raise TypeError(
                f"scalar init_val must be int; use explicit Mapping or Iterable "
                f"for {type(init_val).__qualname__!r} outcomes"
            )

    # ---- Class methods ---------------------------------------------------------------

    @classmethod
    def from_counts(
        cls,
        *sources: Mapping[_T, SupportsInt] | Iterable[tuple[_T, SupportsInt]],
    ) -> Self:
        r"""
        Construct a [`H`][dyce.H] by accumulating counts from one or more *sources*.

        Each source may be a mapping of outcomes to counts, or an iterable of
        `#!python (outcome, count)` pairs.
        Counts for the same outcome across all sources are summed.

            >>> H.from_counts([(1, 3), (2, 2), (1, 1)])
            H({1: 4, 2: 2})
            >>> H.from_counts({1: 2, 2: 3}, [(1, 1), (3, 4)])
            H({1: 3, 2: 3, 3: 4})

        With a single mapping source this is equivalent to [`H`][dyce.H] construction,
        but multiple sources are accumulated rather than raising on duplicate keys.

            >>> H.from_counts(H(6), H(6))  # pyrefly: ignore[no-matching-overload]
            H({1: 2, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2})

        """
        c: Counter[_T] = Counter()
        for source in sources:
            if isinstance(source, Mapping):
                # The cast is necessary because isinstance only narrows on Mapping, but
                # Iterable[tuple[_T, SupportsInt]] > Mapping[tuple[_T, SupportsInt],
                # Any], so type checkers rightly include that as the inferred return
                # type for source.items()
                source = cast("ItemsView[_T, SupportsInt]", source.items())  # noqa: PLW2901
            for outcome, count in source:
                c[outcome] += lossless_int(count)
        return cls(c)  # pyright: ignore[reportArgumentType,reportCallIssue]

    # ---- Overrides -------------------------------------------------------------------

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((type(self), *self.lowest_terms().items()))
        return self._hash

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._h!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, H):
            return bool(self.lowest_terms()._h == other.lowest_terms()._h)
        if isinstance(other, HableT):
            return self.__eq__(other.h())
        return super().__eq__(other)

    # ---- Mapping abstract methods ----------------------------------------------------

    def __bool__(self) -> bool:
        return bool(self.total)

    def __getitem__(self, key: object, /) -> int:
        return self._h[key]  # type: ignore[index] # ty: ignore[invalid-argument-type]

    def __iter__(self) -> Iterator[_T_co]:
        return iter(self._h)

    def __len__(self) -> int:
        return len(self._h)

    def counts(self) -> ValuesView[int]:
        r"""
        More descriptive synonym for the `#!python values` mapping method.
        """
        return self._h.values()

    def outcomes(self: "H[_T]") -> KeysView[_T]:
        r"""
        More descriptive synonym for the `#!python keys` mapping method.
        """
        return self._h.keys()

    # ---- Forward operators -----------------------------------------------------------

    @overload
    def __matmul__(self: "H[Never]", rhs: SupportsInt) -> "H[Never]": ...
    @overload
    def __matmul__(self: "H[Any]", rhs: Literal[0]) -> "H[Never]": ...
    @overload
    # See <https://github.com/jorenham/optype/discussions/574>
    def __matmul__(self: "H[ot.CanAdd[int, int]]", rhs: SupportsInt) -> "H[int]": ...
    @overload
    def __matmul__(
        self: "H[_ConvolvableT]", rhs: SupportsInt
    ) -> "H[_ConvolvableT]": ...
    @overload
    def __matmul__(self: "H[_T]", rhs: Literal[1]) -> "H[_T]": ...
    def __matmul__(self: "H", rhs: SupportsInt) -> "H":
        n = lossless_int_or_not_implemented(rhs)
        if n is NotImplemented:
            return NotImplemented
        if n < 0:
            return NotImplemented
        result = _convolve(self._h, n)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __add__(
        self: "H[ot.CanAdd[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __add__(
        self: "H[ot.CanAdd[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __add__(
        self: "H[ot.CanAdd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __add__(self: "H[_T]", rhs: "H[ot.CanAdd[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __add__(
        self: "H[_T]", rhs: "HableT[ot.CanAdd[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __add__(self: "H[_T]", rhs: ot.CanAdd[_T, _ResultT]) -> "H[_ResultT]": ...
    def __add__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__add__", "__radd__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__add__", "__radd__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __sub__(
        self: "H[ot.CanSub[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __sub__(
        self: "H[ot.CanSub[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __sub__(
        self: "H[ot.CanSub[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __sub__(self: "H[_T]", rhs: "H[ot.CanSub[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __sub__(
        self: "H[_T]", rhs: "HableT[ot.CanSub[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __sub__(self: "H[_T]", rhs: ot.CanSub[_T, _ResultT]) -> "H[_ResultT]": ...
    def __sub__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__sub__", "__rsub__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__sub__", "__rsub__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __mul__(
        self: "H[ot.CanMul[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mul__(
        self: "H[ot.CanMul[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mul__(
        self: "H[ot.CanMul[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __mul__(self: "H[_T]", rhs: "H[ot.CanMul[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __mul__(
        self: "H[_T]", rhs: "HableT[ot.CanMul[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mul__(self: "H[_T]", rhs: ot.CanMul[_T, _ResultT]) -> "H[_ResultT]": ...
    def __mul__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__mul__", "__rmul__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__mul__", "__rmul__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __truediv__(
        self: "H[ot.CanTruediv[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __truediv__(
        self: "H[ot.CanTruediv[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __truediv__(
        self: "H[ot.CanTruediv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __truediv__(
        self: "H[_T]", rhs: "H[ot.CanTruediv[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __truediv__(
        self: "H[_T]", rhs: "HableT[ot.CanTruediv[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __truediv__(
        self: "H[_T]", rhs: ot.CanTruediv[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __truediv__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__truediv__", "__rtruediv__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__truediv__", "__rtruediv__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __floordiv__(
        self: "H[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "H[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "H[ot.CanFloordiv[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "H[_T]", rhs: "H[ot.CanFloordiv[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "H[_T]", rhs: "HableT[ot.CanFloordiv[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __floordiv__(
        self: "H[_T]", rhs: ot.CanFloordiv[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __floordiv__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(
                    lhs, "__floordiv__", "__rfloordiv__", rhs
                ),
            )
        else:
            result = _map_opname_fwd(self._h, "__floordiv__", "__rfloordiv__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __mod__(
        self: "H[ot.CanMod[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mod__(
        self: "H[ot.CanMod[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mod__(
        self: "H[ot.CanMod[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __mod__(self: "H[_T]", rhs: "H[ot.CanMod[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __mod__(
        self: "H[_T]", rhs: "HableT[ot.CanMod[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __mod__(self: "H[_T]", rhs: ot.CanMod[_T, _ResultT]) -> "H[_ResultT]": ...
    def __mod__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__mod__", "__rmod__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__mod__", "__rmod__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __pow__(
        self: "H[ot.CanPow2[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __pow__(
        self: "H[ot.CanPow2[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __pow__(
        self: "H[ot.CanPow2[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __pow__(self: "H[_T]", rhs: "H[ot.CanPow2[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __pow__(
        self: "H[_T]", rhs: "HableT[ot.CanPow2[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __pow__(self: "H[_T]", rhs: ot.CanPow2[_T, _ResultT]) -> "H[_ResultT]": ...
    def __pow__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__pow__", "__rpow__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__pow__", "__rpow__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __lshift__(
        self: "H[ot.CanLshift[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __lshift__(
        self: "H[ot.CanLshift[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __lshift__(
        self: "H[ot.CanLshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __lshift__(
        self: "H[_T]", rhs: "H[ot.CanLshift[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __lshift__(
        self: "H[_T]", rhs: "HableT[ot.CanLshift[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __lshift__(self: "H[_T]", rhs: ot.CanLshift[_T, _ResultT]) -> "H[_ResultT]": ...
    def __lshift__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__lshift__", "__rlshift__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__lshift__", "__rlshift__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rshift__(
        self: "H[ot.CanRshift[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __rshift__(
        self: "H[ot.CanRshift[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __rshift__(
        self: "H[ot.CanRshift[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rshift__(
        self: "H[_T]", rhs: "H[ot.CanRshift[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __rshift__(
        self: "H[_T]", rhs: "HableT[ot.CanRshift[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __rshift__(self: "H[_T]", rhs: ot.CanRshift[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rshift__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__rshift__", "__rrshift__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__rshift__", "__rrshift__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __and__(
        self: "H[ot.CanAnd[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __and__(
        self: "H[ot.CanAnd[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __and__(
        self: "H[ot.CanAnd[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __and__(self: "H[_T]", rhs: "H[ot.CanAnd[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __and__(
        self: "H[_T]", rhs: "HableT[ot.CanAnd[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __and__(self: "H[_T]", rhs: ot.CanAnd[_T, _ResultT]) -> "H[_ResultT]": ...
    def __and__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__and__", "__rand__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__and__", "__rand__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __or__(
        self: "H[ot.CanOr[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __or__(
        self: "H[ot.CanOr[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __or__(
        self: "H[ot.CanOr[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __or__(self: "H[_T]", rhs: "H[ot.CanOr[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __or__(
        self: "H[_T]", rhs: "HableT[ot.CanOr[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __or__(self: "H[_T]", rhs: ot.CanOr[_T, _ResultT]) -> "H[_ResultT]": ...
    def __or__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__or__", "__ror__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__or__", "__ror__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __xor__(
        self: "H[ot.CanXor[_OtherT, _ResultT]]", rhs: "H[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __xor__(
        self: "H[ot.CanXor[_OtherT, _ResultT]]", rhs: "HableT[_OtherT]"
    ) -> "H[_ResultT]": ...
    @overload
    def __xor__(
        self: "H[ot.CanXor[_OtherT, _ResultT]]", rhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __xor__(self: "H[_T]", rhs: "H[ot.CanXor[_T, _ResultT]]") -> "H[_ResultT]": ...
    @overload
    def __xor__(
        self: "H[_T]", rhs: "HableT[ot.CanXor[_T, _ResultT]]"
    ) -> "H[_ResultT]": ...
    @overload
    def __xor__(self: "H[_T]", rhs: ot.CanXor[_T, _ResultT]) -> "H[_ResultT]": ...
    def __xor__(self, rhs: object) -> "H[object]":
        rhs = _flatten_to_h(rhs)
        if isinstance(rhs, H):
            result = _h_binary_callable(
                self._h,
                rhs._h,
                lambda lhs, rhs: _apply_opname(lhs, "__xor__", "__rxor__", rhs),
            )
        else:
            result = _map_opname_fwd(self._h, "__xor__", "__rxor__", rhs)
        return NotImplemented if result is NotImplemented else H(result)

    # ---- Reflected operators ---------------------------------------------------------

    @overload
    def __rmatmul__(self: "H[Never]", lhs: SupportsInt) -> "H[Never]": ...
    @overload
    def __rmatmul__(self: "H[Any]", lhs: Literal[0]) -> "H[Never]": ...
    @overload
    # See <https://github.com/jorenham/optype/discussions/574>
    def __rmatmul__(self: "H[ot.CanAdd[int, int]]", lhs: SupportsInt) -> "H[int]": ...
    @overload
    def __rmatmul__(
        self: "H[_ConvolvableT]", lhs: SupportsInt
    ) -> "H[_ConvolvableT]": ...
    @overload
    def __rmatmul__(self: "H[_T]", lhs: Literal[1]) -> "H[_T]": ...
    def __rmatmul__(self: "H", lhs: SupportsInt) -> "H":
        return self.__matmul__(lhs)

    @overload
    def __radd__(
        self: "H[ot.CanRAdd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __radd__(self: "H[_T]", lhs: ot.CanRAdd[_T, _ResultT]) -> "H[_ResultT]": ...
    def __radd__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__add__", "__radd__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rsub__(
        self: "H[ot.CanRSub[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rsub__(self: "H[_T]", lhs: ot.CanRSub[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rsub__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__sub__", "__rsub__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rmul__(
        self: "H[ot.CanRMul[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rmul__(self: "H[_T]", lhs: ot.CanRMul[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rmul__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__mul__", "__rmul__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rtruediv__(
        self: "H[ot.CanRTruediv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rtruediv__(
        self: "H[_T]", lhs: ot.CanRTruediv[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __rtruediv__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__truediv__", "__rtruediv__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rfloordiv__(
        self: "H[ot.CanRFloordiv[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rfloordiv__(
        self: "H[_T]", lhs: ot.CanRFloordiv[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __rfloordiv__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__floordiv__", "__rfloordiv__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rmod__(
        self: "H[ot.CanRMod[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rmod__(self: "H[_T]", lhs: ot.CanRMod[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rmod__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__mod__", "__rmod__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rpow__(
        self: "H[ot.CanRPow[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rpow__(self: "H[_T]", lhs: ot.CanRPow[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rpow__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__pow__", "__rpow__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rlshift__(
        self: "H[ot.CanRLshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rlshift__(
        self: "H[_T]", lhs: ot.CanRLshift[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __rlshift__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__lshift__", "__rlshift__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rrshift__(
        self: "H[ot.CanRRshift[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rrshift__(
        self: "H[_T]", lhs: ot.CanRRshift[_T, _ResultT]
    ) -> "H[_ResultT]": ...
    def __rrshift__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__rshift__", "__rrshift__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rand__(
        self: "H[ot.CanRAnd[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rand__(self: "H[_T]", lhs: ot.CanRAnd[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rand__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__and__", "__rand__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __ror__(
        self: "H[ot.CanROr[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __ror__(self: "H[_T]", lhs: ot.CanROr[_T, _ResultT]) -> "H[_ResultT]": ...
    def __ror__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__or__", "__ror__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def __rxor__(
        self: "H[ot.CanRXor[_OtherT, _ResultT]]", lhs: _OtherT
    ) -> "H[_ResultT]": ...
    @overload
    def __rxor__(self: "H[_T]", lhs: ot.CanRXor[_T, _ResultT]) -> "H[_ResultT]": ...
    def __rxor__(self, lhs: object) -> "H[object]":
        result = _map_opname_ref(self._h, "__xor__", "__rxor__", lhs)
        return NotImplemented if result is NotImplemented else H(result)

    @overload
    def lt(self: "H[ot.CanLt[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def lt(self: "H[ot.CanLt[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def lt(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_lt, rhs)`.

            >>> H(20).lt(10)
            H({False: 11, True: 9})
            >>> H(6).lt(H(10)).lowest_terms()
            H({False: 7, True: 13})
        """
        return self.apply(ot.do_lt, rhs)  # type: ignore[arg-type]

    @overload
    def le(self: "H[ot.CanLe[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def le(self: "H[ot.CanLe[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def le(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_le, rhs)`.

            >>> H(20).le(10)
            H({False: 10, True: 10})
            >>> H(6).le(H(10)).lowest_terms()
            H({False: 1, True: 3})
        """
        return self.apply(ot.do_le, rhs)  # type: ignore[arg-type]

    @overload
    def eq(self: "H[ot.CanEq[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def eq(self: "H[ot.CanEq[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def eq(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_eq, rhs)`.

            >>> H(20).eq(10)
            H({False: 19, True: 1})
            >>> H(6).eq(H(10)).lowest_terms()
            H({False: 9, True: 1})
        """
        return self.apply(ot.do_eq, rhs)

    @overload
    def ne(self: "H[ot.CanNe[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def ne(self: "H[ot.CanNe[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def ne(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_ne, rhs)`.

            >>> H(20).ne(10)
            H({False: 1, True: 19})
            >>> H(6).ne(H(10)).lowest_terms()
            H({False: 1, True: 9})
        """
        return self.apply(ot.do_ne, rhs)

    @overload
    def ge(self: "H[ot.CanGe[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def ge(self: "H[ot.CanGe[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def ge(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_ge, rhs)`.

            >>> H(20).ge(10)
            H({False: 9, True: 11})
            >>> H(6).ge(H(10)).lowest_terms()
            H({False: 13, True: 7})
        """
        return self.apply(ot.do_ge, rhs)  # type: ignore[arg-type]

    @overload
    def gt(self: "H[ot.CanGt[_OtherT, bool]]", rhs: "H[_OtherT]") -> "H[bool]": ...
    @overload
    def gt(self: "H[ot.CanGt[_OtherT, bool]]", rhs: _OtherT) -> "H[bool]": ...
    def gt(self, rhs: "H[object] | object") -> "H[bool]":
        r"""
        Shorthand for `#!python self.apply(optype.do_gt, rhs)`.

            >>> H(20).gt(10)
            H({False: 10, True: 10})
            >>> H(6).gt(H(10)).lowest_terms()
            H({False: 3, True: 1})
        """
        return self.apply(ot.do_gt, rhs)  # type: ignore[arg-type]

    # ---- Unary operators -------------------------------------------------------------

    def __neg__(self: "H[ot.CanNeg[_ResultT]]") -> "H[_ResultT]":
        result = _h_unary_opname(self._h, "__neg__")
        if result is NotImplemented:
            raise TypeError(
                f"bad operand type for unary -: {type(next(iter(self._h))).__qualname__!r}"
            )
        return H(result)

    def __pos__(self: "H[ot.CanPos[_ResultT]]") -> "H[_ResultT]":
        result = _h_unary_opname(self._h, "__pos__")
        if result is NotImplemented:
            raise TypeError(
                f"bad operand type for unary +: {type(next(iter(self._h))).__qualname__!r}"
            )
        return H(result)

    def __abs__(self: "H[ot.CanAbs[_ResultT]]") -> "H[_ResultT]":
        result = _h_unary_opname(self._h, "__abs__")
        if result is NotImplemented:
            raise TypeError(
                f"bad operand type for abs(): {type(next(iter(self._h))).__qualname__!r}"
            )
        return H(result)

    def __invert__(self: "H[ot.CanInvert[_ResultT]]") -> "H[_ResultT]":
        result = _h_unary_opname(self._h, "__invert__")
        if result is NotImplemented:
            raise TypeError(
                f"bad operand type for unary ~: {type(next(iter(self._h))).__qualname__!r}"
            )
        return H(result)

    # ---- Properties ------------------------------------------------------------------

    @property
    def total(self) -> int:
        r"""
        Equivalent to `#!python sum(self.counts())`.
        The result is cached to avoid redundant computation with multiple accesses.

            >>> H({4: 2, 5: 3, 6: 1}).total
            6
            >>> H({}).total
            0
        """
        if self._total is None:
            self._total = sum(self._h.values())
        return self._total

    # ---- Methods ---------------------------------------------------------------------

    def merge(
        self: "H[_T]", other: "H[_T] | Mapping[_T, SupportsInt] | Iterable[_T]"
    ) -> "H[_T]":
        r"""
        Merges counts.

            >>> H(4).merge(H(6))
            H({1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1})
        """
        result: dict[_T, int] = dict(self)
        other_h = other if isinstance(other, H) else H(other)
        for outcome, count in other_h.items():
            result[outcome] = result.get(outcome, 0) + count  # ty: ignore[invalid-assignment,no-matching-overload]
        return H(result)

    @overload
    def apply(
        self: "H[_T]",
        func: Callable[[_T], _ResultT],
    ) -> "H[_ResultT]": ...
    @overload
    def apply(
        self: "H[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: "H[_OtherT]",
    ) -> "H[_ResultT]": ...
    @overload
    def apply(
        self: "H[_T]",
        func: Callable[[_T, _OtherT], _ResultT],
        other: _OtherT,
    ) -> "H[_ResultT]": ...
    def apply(
        self: "H[_T]",
        func: Callable[[_T], _ResultT] | Callable[[_T, _OtherT], _ResultT],
        other: "H[_OtherT] | _OtherT | SentinelT" = Sentinel,
    ) -> "H[_ResultT]":
        r"""
        Return a new [`H`][dyce.H] by applying *func* to outcomes.
        If *operand* is provided, *func* should have two parameters, otherwise it should have one.

        If *operand* is an [`H`][dyce.H], take the Cartesian product of both histograms’ items: call `#!python func(h_outcome, other_outcome)` for each pair and accumulate `#!python h_count * other_count`.

        If *operand* is a scalar, call `#!python func(outcome, operand)` for each outcome, passing counts through unchanged.

        Resulting counts for duplicate outcomes are summed.

            >>> import operator
            >>> H({10: 1, 20: 1}).apply(operator.sub, 10)
            H({0: 1, 10: 1})
            >>> H({10: 1, 20: 1}).apply(operator.sub, H({1: 1, 2: 1}))
            H({8: 1, 9: 1, 18: 1, 19: 1})

            >>> # optype provides reflected operator functions as do_r*
            >>> import optype as ot

            >>> H({10: 1, 20: 1}).apply(ot.do_rsub, 10)
            H({-10: 1, 0: 1})

            >>> H({10: 1, 20: 1}).apply(ot.do_rsub, H({1: 1, 2: 1}))
            H({-19: 1, -18: 1, -9: 1, -8: 1})

        One way to compute how often a six-sided die “beats” an eight-sided die rolled together:

            >>> from enum import IntEnum

            >>> class Versus(IntEnum):
            ...     LOSS = -1
            ...     DRAW = 0
            ...     WIN = 1

            >>> d6 = H(6)
            >>> d8 = H(8)
            >>> vs = lambda h_outcome, other_outcome: (
            ...     Versus.LOSS
            ...     if h_outcome < other_outcome
            ...     else Versus.WIN
            ...     if h_outcome > other_outcome
            ...     else Versus.DRAW
            ... )
            >>> d6.apply(vs, d8)
            H({<Versus.LOSS: -1>: 27, <Versus.DRAW: 0>: 6, <Versus.WIN: 1>: 15})

        Omitting *operand* allows examination of just the histogram.
        One way to determine Apocalypse World outcomes with a modifier:

            >>> class PBTA(IntEnum):
            ...     MISS = 0
            ...     WEAK_HIT = 1
            ...     STRONG_HIT = 2

            >>> mod = +1
            >>> pbta_result = (2 @ H(6) + mod).apply(
            ...     lambda outcome: (
            ...         PBTA.MISS
            ...         if outcome <= 6
            ...         else PBTA.WEAK_HIT
            ...         if 7 <= outcome <= 9
            ...         else PBTA.STRONG_HIT
            ...     )
            ... )
            >>> pbta_result
            H({<PBTA.MISS: 0>: 10, <PBTA.WEAK_HIT: 1>: 16, <PBTA.STRONG_HIT: 2>: 10})

        One way to count how often summing outcomes comes out even on 2d3:

            >>> d3_2 = 2 @ H(3)
            >>> d3_2
            H({2: 1, 3: 2, 4: 3, 5: 2, 6: 1})
            >>> d3_2_is_even = d3_2.apply(lambda outcome: outcome % 2 == 0)
            >>> d3_2_is_even
            H({False: 4, True: 5})
            >>> (d3_2 % 2).eq(0) == d3_2_is_even
            True
            >>> ((d3_2 + 1) % 2) == d3_2_is_even
            True
        """
        if other is Sentinel:
            result: dict[_ResultT, int] = {}
            func = cast("Callable[[_T], _ResultT]", func)
            for outcome, count in self._h.items():
                new_outcome = func(outcome)
                result[new_outcome] = result.get(new_outcome, 0) + count
            return H(result)

        func = cast("Callable[[_T, _OtherT], _ResultT]", func)
        if isinstance(other, H):
            return H(
                cast("dict[_ResultT, int]", _h_binary_callable(self._h, other._h, func))  # noqa: SLF001
            )
        else:
            return H(
                cast(
                    "dict[_ResultT, int]", _h_binary_callable(self._h, {other: 1}, func)
                )
            )

    @experimental
    def exactly_k_times_in_n(
        self: "H[_T]",
        outcome: _T,
        n: SupportsInt,
        k: SupportsInt,
    ) -> int:
        r"""
        <!-- BEGIN MONKEY PATCH --
        >>> import warnings
        >>> from dyce.lifecycle import ExperimentalWarning
        >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

           -- END MONKEY PATCH -->

        Computes and returns (in constant time) the number of ways *outcome* appears exactly *k* times among *n* like histograms.
        Uses the binomial coefficient as a more efficient alternative to `#!python (n @ self.eq(outcome))[k]`.

            >>> H(6).exactly_k_times_in_n(outcome=5, n=4, k=2)
            150
            >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=2, n=3, k=3)
            1
            >>> H((2, 3, 3, 4, 4, 5)).exactly_k_times_in_n(outcome=4, n=3, k=3)
            8

        !!! note "Counts, not probabilities"

            This returns a *count* of ways, not a probability, and may not be in lowest terms.
            (See [`lowest_terms`][dyce.H.lowest_terms].)
            Divide by `#!python self.total ** n` to get a probability.
            (See [`total`][dyce.H.total].)

                >>> from fractions import Fraction
                >>> h = H((2, 3, 3, 4, 4, 5))
                >>> n, k = 3, 2
                >>> (n @ h).total == h.total**n
                True
                >>> Fraction(h.exactly_k_times_in_n(outcome=3, n=n, k=k), h.total**n)
                Fraction(2, 9)
                >>> h_not_lowest_terms = h.merge(h)
                >>> h == h_not_lowest_terms
                True
                >>> h_not_lowest_terms
                H({2: 2, 3: 4, 4: 4, 5: 2})
                >>> h_not_lowest_terms.exactly_k_times_in_n(outcome=3, n=n, k=k)
                384
                >>> Fraction(
                ...     h_not_lowest_terms.exactly_k_times_in_n(outcome=3, n=n, k=k),
                ...     h_not_lowest_terms.total**n,
                ... )
                Fraction(2, 9)

        <!-- BEGIN MONKEY PATCH --
        >>> warnings.resetwarnings()

           -- END MONKEY PATCH -->
        """
        n = lossless_int(n)
        k = lossless_int(k)

        if k > n:
            raise ValueError(f"k ({k!r}) must be less than or equal to n ({n!r})")

        c_outcome = self.get(outcome, 0)
        return math.comb(n, k) * c_outcome**k * (self.total - c_outcome) ** (n - k)

    def format(
        self,
        *,
        precision: int = 2,
        scaled: bool = False,
        tick: str = "#",
        width: int = _ROW_WIDTH,
    ) -> str:
        r"""
        Returns a formatted string representation of the histogram.
        *precision* is the number of decimal places to use and defaults to `#!python 2`.
        *tick* is used as the bar character and defaults to `#!python "#"`.
        *width* must be positive and is the maximum width of the horizontal bar ASCII graph.

            >>> print(
            ...     (2 @ H(6))
            ...     .zero_fill(range(1, 21))
            ...     .format(precision=4, tick="@", width=65)
            ... )
            avg |    7.0000
            std |    2.4152
            var |    5.8333
              1 |   0.0000% |
              2 |   2.7778% |@
              3 |   5.5556% |@@
              4 |   8.3333% |@@@@
              5 |  11.1111% |@@@@@
              6 |  13.8889% |@@@@@@
              7 |  16.6667% |@@@@@@@@
              8 |  13.8889% |@@@@@@
              9 |  11.1111% |@@@@@
             10 |   8.3333% |@@@@
             11 |   5.5556% |@@
             12 |   2.7778% |@
             13 |   0.0000% |
             14 |   0.0000% |
             15 |   0.0000% |
             16 |   0.0000% |
             17 |   0.0000% |
             18 |   0.0000% |
             19 |   0.0000% |
             20 |   0.0000% |

        If *scaled* is `#!python True`, horizontal bars are scaled to *width*.

            >>> h_ge = (2 @ H(6)).ge(7)
            >>> print(f"{' 65 chars wide -->|':->65}")
            ---------------------------------------------- 65 chars wide -->|
            >>> print(H(1).format(scaled=False, width=65))
            avg |    1.00
            std |    0.00
            var |    0.00
              1 | 100.00% |##################################################
            >>> print(h_ge.format(scaled=False, width=65))
              avg |    0.58
              std |    0.49
              var |    0.24
            False |  41.67% |####################
             True |  58.33% |############################
            >>> print(h_ge.format(scaled=True, width=65))
              avg |    0.58
              std |    0.49
              var |    0.24
            False |  41.67% |##################################
             True |  58.33% |################################################
        """
        # Get the length of the fixed-width column " | {<var>:7.2%} |" for computing the
        # available tick space
        prob_width = 5 + precision
        prob_len = len(f" | {0.0:{prob_width}.{precision}%} |")
        try:
            mu: float | None = self.mean()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
            std: float | None = self.stdev()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
            var: float | None = self.variance()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        except Exception as exc:  # noqa: BLE001
            # Broad catch is intentional: format() is a display method that should
            # always produce output. Any failure to compute statistics (including from
            # runtime type checkers like beartype) is treated as "stats not available"
            # rather than an error.
            warnings.warn(f"{exc!s}", stacklevel=2)
            mu = None
            std = None
            var = None

        def _lines() -> Iterator[str]:
            # First pass: collect (outcome_str, probability) pairs and find the widest
            # outcome representation. We need max_outcome_len before we can emit
            # anything, because the stats header must align with it.
            pairs: list[tuple[str, Fraction]] = []
            max_outcome_len = 3  # minimum column width
            for outcome, probability in self.probability_items():
                outcome_str = repr(outcome)
                max_outcome_len = max(max_outcome_len, len(outcome_str))
                pairs.append((outcome_str, probability))

            # Stats header (emitted before outcome rows)
            if mu is not None:
                yield f"{'avg': >{max_outcome_len}} | {mu:{prob_width}.{precision}f}"
            if std is not None:
                yield f"{'std': >{max_outcome_len}} | {std:{prob_width}.{precision}f}"
            if var is not None:
                yield f"{'var': >{max_outcome_len}} | {var:{prob_width}.{precision}f}"

            if pairs:
                tick_scale = max(self.counts()) / self.total if scaled else 1.0
                max_num_ticks = (width - max_outcome_len - prob_len) // len(tick)
                for outcome_str, probability in pairs:
                    ticks = tick * int(max_num_ticks * float(probability) / tick_scale)
                    yield f"{outcome_str: >{max_outcome_len}} | {float(probability):{prob_width}.{precision}%} |{ticks}"

        return os.linesep.join(_lines())

    def format_short(
        self,
        *,
        precision: int = 2,
    ) -> str:
        r"""
        Returns a short-form formatted string representation of the histogram.

            >>> print(H(6).format_short())
            {avg: 3.50, 1: 16.67%, 2: 16.67%, 3: 16.67%, 4: 16.67%, 5: 16.67%, 6: 16.67%}
            >>> print(H(6).format_short(precision=3))  # decimal places
            {avg: 3.500, 1: 16.667%, 2: 16.667%, 3: 16.667%, 4: 16.667%, 5: 16.667%, 6: 16.667%}
        """
        prob_width = 5 + precision
        try:
            mu: float | None = self.mean()  # type: ignore[misc] # ty: ignore[invalid-argument-type]
        except Exception as exc:  # noqa: BLE001
            # See format() for rationale
            warnings.warn(f"{exc!s}", stacklevel=2)
            mu = None

        def _parts() -> Iterator[str]:
            if mu is not None:
                yield f"avg: {mu:.2f}"
            yield from (
                f"{outcome}:{float(probability):{prob_width}.{precision}%}"
                for outcome, probability in self.probability_items()
            )

        return f"{{{', '.join(_parts())}}}"

    def lowest_terms(self: "H[_T]") -> "H[_T]":
        r"""
        Return a new [`H`][dyce.H] with zero-count outcomes removed and all counts divided by their GCD.

            >>> H({1: 2, 2: 4, 3: 6}).lowest_terms()
            H({1: 1, 2: 2, 3: 3})
            >>> H({1: 3, 2: 0, 3: 6}).lowest_terms()
            H({1: 1, 3: 2})
            >>> H({}).lowest_terms()
            H({})
        """
        counts = tuple(count for count in self._h.values() if count)
        if not counts:
            return cast("H[_T]", H({}))
        g = math.gcd(*counts)
        return H({outcome: count // g for outcome, count in self._h.items() if count})

    def mean(self: "H[SupportsFloat]") -> float:
        r"""
        Return the mean (expected value) of the weighted outcomes.
        Raises `#!python ValueError` if the histogram is empty.

            >>> H(6).mean()
            3.5
            >>> H({1: 1, 3: 1}).mean()
            2.0
        """
        if not self._h:
            raise ValueError("mean of empty histogram is undefined")
        return float(
            sum(outcome * count for outcome, count in self.items()) / self.total  # type: ignore[misc,operator]  # ty: ignore[unsupported-operator]
        )

    @experimental
    def order_stat_for_n_at_pos(
        self: "H[_T]",
        n: SupportsInt,
        pos: SupportsInt,
    ) -> "H[_T]":
        r"""
        <!-- BEGIN MONKEY PATCH --
        >>> import warnings
        >>> from dyce.lifecycle import ExperimentalWarning
        >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

           -- END MONKEY PATCH -->

        Computes the probability distribution for each outcome appearing at *pos* among *n* like histograms sorted least-to-greatest.
        *pos* is a zero-based index.

            >>> d6avg = H((2, 3, 3, 4, 4, 5))
            >>> d6avg.order_stat_for_n_at_pos(5, 3)
            H({2: 26, 3: 1432, 4: 4792, 5: 1526})

        The results show that, when rolling five averaging dice and sorting each roll, there are 26 ways where `#!python 2` appears at the fourth (index `#!python 3`) position, 1,432 ways where `#!python 3` appears at the fourth position, etc.

        Negative values for *pos* follow Python index semantics:

            >>> d6 = H(6)
            >>> d6.order_stat_for_n_at_pos(6, 0) == d6.order_stat_for_n_at_pos(6, -6)
            True
            >>> d6.order_stat_for_n_at_pos(6, 5) == d6.order_stat_for_n_at_pos(6, -1)
            True

        This method caches the beta values for *n* so they can be reused for varying values of *pos* in subsequent calls.

        <!-- BEGIN MONKEY PATCH --
        >>> warnings.resetwarnings()

           -- END MONKEY PATCH -->
        """
        n = lossless_int(n)
        pos = lossless_int(pos)
        if not (-n <= pos < n):
            raise ValueError(f"pos ({pos!r}) must be in range [{-n}, {n})")

        if n not in self._order_stat_funcs_by_n:
            self._order_stat_funcs_by_n[n] = self._order_stat_func_for_n(n)
        if pos < 0:
            pos = n + pos
        return self._order_stat_funcs_by_n[n](pos)

    @overload
    def probability_items(
        self: "H[_T]", rational_t: None = None
    ) -> Iterator[tuple[_T, Fraction]]: ...
    @overload
    def probability_items(
        self: "H[_T]", rational_t: Callable[[int, int], _OtherT]
    ) -> Iterator[tuple[_T, _OtherT]]: ...
    def probability_items(
        self: "H[_T]", rational_t: Callable[[int, int], _OtherT] | None = None
    ) -> Iterator[tuple[_T, _OtherT]]:
        r"""
        Yield `#!python (outcome, probability)` pairs where each probability is computed as `#!python rational_t(count, total)`.

        *rational_t* defaults to `#!python fractions.Fraction`, giving exact rational probabilities.
        Pass any two-argument callable to get a different representation (e.g. `#!python float` division via `#!python lambda n, d: n / d`).

        Yields nothing if the histogram is empty (total is zero).

            >>> list(H({1: 1, 2: 2, 3: 1}).probability_items())
            [(1, Fraction(1, 4)), (2, Fraction(1, 2)), (3, Fraction(1, 4))]
            >>> from operator import truediv
            >>> list(H({1: 1, 2: 2, 3: 1}).probability_items(truediv))
            [(1, 0.25), (2, 0.5), (3, 0.25)]
            >>> list(H({}).probability_items())
            []
        """
        if rational_t is None:
            rational_t = cast("Callable[[int, int], _OtherT]", Fraction)
        t = self.total
        if not t:
            return
        for outcome, count in self._h.items():
            yield outcome, rational_t(count, t)

    @experimental
    def replace(self: "H[_T]", existing_outcome: _T, repl: "H[_T] | _T") -> "H[_T]":
        r"""
        <!-- BEGIN MONKEY PATCH --
        >>> import warnings
        >>> from dyce.lifecycle import ExperimentalWarning
        >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

           -- END MONKEY PATCH -->

        Returns a new histogram with a possibly substituted outcome.
        If *repl* is a single outcome, it will replace *existing_outcome* directly (if *existing_outcome* exists in the original histogram).
        If *repl* is a histogram, its outcomes will be “folded in”, together making up the same proportion of the total as the replaced outcome.

            >>> d6 = H(6)
            >>> d6.replace(6, 1_000)
            H({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 1000: 1})
            >>> d6.replace(7, "never used") == d6  # type: ignore[arg-type]
            True

            >>> H({1: 1, 2: 2, 3: 3}).replace(2, H({3: 1, 4: 2, 5: 3}))
            H({1: 6, 3: 20, 4: 4, 5: 6})

            >>> once_exploded_d6 = d6.replace(6, d6 + 6)
            >>> once_exploded_d6
            H({1: 6, 2: 6, 3: 6, 4: 6, 5: 6, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1})

        One way to “explode” a die `#!math n` times:

            >>> def explode_n_by_replacement(h: H[int], n: int) -> H[int]:
            ...     max_h = max(h)
            ...     exploded_h = h
            ...     for _ in range(n):
            ...         exploded_h = h.replace(max_h, exploded_h + max_h)
            ...     return exploded_h  # ty: ignore[invalid-return-type]

            >>> explode_n_by_replacement(d6, 0) == d6
            True
            >>> explode_n_by_replacement(d6, 1) == once_exploded_d6
            True
            >>> explode_n_by_replacement(d6, 2)
            H({1: 36, 2: 36, 3: 36, 4: 36, 5: 36, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1})
            >>> explode_n_by_replacement(d6, 15)
            H({1: 470184984576, 2: 470184984576, 3: 470184984576, ..., 94: 1, 95: 1, 96: 1})

        <!-- BEGIN MONKEY PATCH --
        >>> warnings.resetwarnings()

           -- END MONKEY PATCH -->
        """
        if existing_outcome not in self:
            return self
        existing_outcome_count = self[existing_outcome]
        d: dict[_T, int]
        if isinstance(repl, H):
            repl_total = repl.total
            d = {
                outcome: count * repl_total
                for outcome, count in self.items()
                if outcome != existing_outcome
            }
            for repl_outcome, repl_count in repl.items():
                d[repl_outcome] = (  # ty: ignore[invalid-assignment]
                    d.get(repl_outcome, 0)  # ty: ignore[no-matching-overload]
                    + repl_count * existing_outcome_count
                )
        else:
            d = {
                outcome: count
                for outcome, count in self.items()
                if outcome != existing_outcome
            }
            d[repl] = d.get(repl, 0) + existing_outcome_count
        return H(d)

    def roll(self: "H[_T]") -> _T:
        r"""
        Returns a (weighted) random outcome.

        <!-- BEGIN MONKEY PATCH --
        For deterministic outcomes.

        >>> import random
        >>> from dyce import rng
        >>> rng.RNG = random.Random(1774583876)

          -- END MONKEY PATCH -->

            >>> d6 = H(6)
            >>> [d6.roll() for _ in range(10)]
            [2, 6, 1, 2, 4, 5, 1, 4, 2, 5]
        """
        if not self:
            raise ValueError("no outcomes from which to select in empty histogram")
        return rng.RNG.choices(
            population=tuple(self.outcomes()),
            weights=tuple(self.counts()),
            k=1,
        )[0]

    def stdev(self: "H[SupportsFloat]") -> float:
        r"""
        Return the standard deviation of the weighted outcomes as a `#!python float`.
        Raises `#!python ValueError` if the histogram is empty.

            >>> H(6).stdev()
            1.707825...
            >>> H({1: 1, 3: 1}).stdev()
            1.0
        """
        return math.sqrt(self.variance())

    def variance(self: "H[SupportsFloat]") -> float:
        r"""
        Return the variance of the weighted outcomes as a `#!python float`.
        Raises `#!python ValueError` if the histogram is empty.

            >>> H(6).variance()
            2.916666...
            >>> H({1: 1, 3: 1}).variance()
            1.0
        """
        return (
            sum(
                count / self.total * float(outcome) ** 2
                for outcome, count in self._h.items()
            )
            - self.mean() ** 2
        )

    def zero_fill(self: "H[_T]", outcomes: Iterable[_T]) -> "H[_T]":
        r"""
        Shorthand for `#!python self.merge(dict.fromkeys(outcomes, 0))`.

            >>> H(4).zero_fill(H(8).outcomes())
            H({1: 1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0})
        """
        return self.merge(dict.fromkeys(outcomes, 0))

    def _order_stat_func_for_n(self: "H[_T]", n: int) -> "Callable[[int], H[_T]]":
        cumulative = 0
        betas: list[tuple[_T, int, int]] = []
        for outcome, count in self.items():
            c_lt = cumulative
            c_le = cumulative + count
            betas.append((outcome, c_lt, c_le))
            cumulative = c_le

        def _order_stat_at_pos(pos: int) -> "H[_T]":
            return H(
                {
                    outcome: (
                        sum(
                            math.comb(n, k) * c_le**k * (self.total - c_le) ** (n - k)
                            for k in range(pos + 1, n + 1)
                        )
                        - sum(
                            math.comb(n, k) * c_lt**k * (self.total - c_lt) ** (n - k)
                            for k in range(pos + 1, n + 1)
                        )
                    )
                    for outcome, c_lt, c_le in betas
                }
            )

        return _order_stat_at_pos


@nobeartype  # not decoratable by beartype (avoids warning)
@runtime_checkable
class HableT(Protocol[_T_co]):
    r"""
    A protocol whose implementer can be expressed as (or reduced to) an [`H` object][dyce.H] by calling its [`h` method][dyce.HableT.h].
    Currently, no class implements this protocol, but this affords an integration point for.

    !!! info

        The intended pronunciation of `Hable` is *AYCH-uh-BUL*[^1] (i.e., [`H`][dyce.H]-able).
        Yes, that is a clumsy attempt at [verbing](https://www.gocomics.com/calvinandhobbes/1993/01/25).
        (You could *totally* [`H`][dyce.H] that, dude!)
        However, if you prefer something else (e.g. *HAY-bul* or *AYCH-AY-bul*), no one is going to judge you.
        (Well, they *might*, but they *shouldn’t*.)
        We all know what you mean.

    [^1]:

        World Book Online (WBO) style [pronunciation respelling](https://en.wikipedia.org/wiki/Pronunciation_respelling_for_English#Traditional_respelling_systems).
    """

    __slots__ = ()

    @abstractmethod
    def h(self: "HableT[_T]") -> H[_T]:
        r"""Express its implementer as an [`H` object][dyce.H]."""


# ---- Helpers -------------------------------------------------------------------------


@overload
def aggregate_weighted(
    weighted_sources: Iterable[tuple[H[_T] | _T, int]], /
) -> H[_T]: ...
@overload
def aggregate_weighted(weighted_sources: Iterable[tuple[Any, int]], /) -> H[Any]: ...
def aggregate_weighted(
    weighted_sources: Iterable[tuple[Any, int]],
) -> H[Any]:
    r"""
    <!-- BEGIN MONKEY PATCH --
    >>> import warnings
    >>> from dyce.lifecycle import ExperimentalWarning
    >>> warnings.filterwarnings("ignore", category=ExperimentalWarning)

       -- END MONKEY PATCH -->

    Aggregate *weighted_sources* into an [`H`][dyce.H] object.

    Each element of *weighted_sources* is a two-tuple of either an `#!python (outcome, count)` pair or an `#!python (H, count)` pair.
    When a source is an [`H`][dyce.H], its total takes on the weight of *count*.
    When a source is the empty histogram (`#!python H({})`), it and its count are omitted without scaling.

    This function is the accumulation engine used by [`expand`][dyce.expand].

        >>> from dyce import H
        >>> from dyce.evaluation import aggregate_weighted
        >>> aggregate_weighted(
        ...     (
        ...         (H({1: 1}), 1),
        ...         (H({1: 1, 2: 2}), 2),
        ...     )
        ... )
        H({1: 5, 2: 4})
        >>> aggregate_weighted(((H(2), 1), (H({}), 20)))
        H({1: 1, 2: 1})

    <!-- BEGIN MONKEY PATCH --
    >>> warnings.resetwarnings()

       -- END MONKEY PATCH -->
    """
    aggregate_scalar = 1
    outcome_counts: list[tuple[Any, int]] = []

    for outcome_or_h, count in weighted_sources:
        if isinstance(outcome_or_h, H):
            if outcome_or_h:
                h_scalar = outcome_or_h.total
                for i, (prior_outcome, prior_count) in enumerate(outcome_counts):
                    outcome_counts[i] = (prior_outcome, prior_count * h_scalar)
                for new_outcome, new_count in outcome_or_h.items():
                    outcome_counts.append(
                        (new_outcome, count * aggregate_scalar * new_count)
                    )
                aggregate_scalar *= h_scalar
        else:
            outcome_counts.append((outcome_or_h, count * aggregate_scalar))

    return H.from_counts(outcome_counts)


def sum_h(hs: Iterable[H[_T]]) -> H[_T]:
    r"""
    Sums zero or more histograms, returning `#!python H({})` for an empty iterable.
    This ensures callers never have to special-case the empty collection.

    Consecutive equal histograms are batched via `#!python @` (which uses `#!math O\left( \log n \right)` exponentiation by squaring), so homogeneous pools like those produced by `#!python P.h()` are convolved efficiently.
    """
    result: H[_T] | None = None
    for h, group in groupby(hs):
        n = sum(1 for _ in group)
        batch = h @ n if n > 1 else h  # pyright: ignore[reportOperatorIssue] # pyrefly: ignore[unsupported-operation] # ty: ignore[unsupported-operator]
        result = batch if result is None else result + batch  # type: ignore[operator]
    return cast("H[_T]", H({})) if result is None else result


@deprecated("may be removed in future versions")
def sum_h_old(hs: Iterable[H[_T]]) -> H[_T]:  # pragma: no cover
    r"""
    Original `#!math O\left( n \right)` implementation of `sum_h`, preserved for performance comparison.
    Sums zero or more histograms, returning `#!python H({})` for an empty iterable.
    """
    result: H[_T] | None = None
    for h in hs:
        result = h if result is None else result + h  # type: ignore[operator]
    return cast("H[_T]", H({})) if result is None else result


class _ConvolveFallbackWarning(UserWarning):
    r"""
    Issued when [`_convolve_fast`][dyce.h._convolve_fast] falls back to the `#!math O \left( n \right)` linear approach.
    """


def _apply_opname(
    l_val: object,
    op_name: str,
    rop_name: str,
    r_val: object,
) -> object:
    r"""
    Try `#!python l_val.op_name(r_val)`; if `#!python NotImplemented`, try `#!python r_val.rop_name(l_val)`.
    """
    op = getattr(l_val, op_name, None)
    result = op(r_val) if op is not None else NotImplemented
    if result is NotImplemented:
        r_op = getattr(r_val, rop_name, None)
        result = r_op(l_val) if r_op is not None else NotImplemented
    return result


def _convolve(
    mapping: Mapping[_ConvolvableT, int],
    n: int,
) -> dict[_ConvolvableT, int] | NotImplementedType:
    r"""
    Sum *n* independent copies of *mapping* (*n*-fold additive convolution).

    Tries `#!math O\left( \log n \right)` exponentiation by squaring first, falling back to the `#!math O\left( n \right)` linear approach if squaring fails.
    (Some outcome types may only support addition with the original outcome type, not with evolved sums.)
    """
    if n == 0:
        return {}
    result = _convolve_fast(mapping, n)
    if result is not NotImplemented:
        return result

    outcome_type = type(next(iter(mapping))).__qualname__
    warnings.warn(
        f"Falling back to O(n) linear convolution for outcome type {outcome_type!r}; fast path requires addition to be closed over evolved sums",
        _ConvolveFallbackWarning,
        stacklevel=3,  # [0] this function -> [1] _convolve -> [2] __matmul__ -> [3] user call site
    )
    return _convolve_linear(mapping, n)


def _convolve_fast(
    mapping: Mapping[_ConvolvableT, int],
    n: int,
) -> dict[_ConvolvableT, int] | NotImplementedType:
    #     mapping: Mapping[Any, int],
    #     n: int,
    # ) -> dict[Any, int] | NotImplementedType:
    r"""
    Compute n-fold additive convolution in `#!math O\left( \log n \right)` steps.

    This is the classic "exponentiation by squaring" algorithm, generalized from multiplication to any associative binary operation.
    Additive convolution of histograms is associative, so it qualifies.

    The key identity is:

        n copies = (n//2 copies) convolved with (n//2 copies)   [+ 1 extra if n is odd]

    So instead of accumulating one copy at a time (`#!math O\left( n \right)` steps), we repeatedly double `#!python base`—convolving it with itself—and accumulate it into `#!python acc` only for the bits of `#!python n` that are set.
    Each bit of `#!python n` corresponds to a power-of-two number of copies (1, 2, 4, 8, …), and the set bits tell us which powers to combine, exactly as binary addition works.

    Example: n=6 (binary 110)
        - bit 1 (value 2): accumulate base<sup>2</sup> into acc; acc = 2 copies
        - bit 2 (value 4): accumulate base<sup>4</sup> into acc; acc = 6 copies
        Total: 2 squares, 1 accumulation versus 5 steps linearly.

    Returns `!#python NotImplemented` if any convolution step does, so the caller can fall back to the linear approach.
    """
    acc: dict[Any, int] | None = None
    base: dict[Any, int] = dict(mapping)
    while n:
        if n & 1:
            if acc is None:
                acc = dict(base)
            else:
                new_acc = _h_binary_callable(
                    acc,
                    base,
                    lambda lhs, rhs: _apply_opname(lhs, "__add__", "__radd__", rhs),
                )
                if new_acc is NotImplemented:
                    return NotImplemented  # pragma: no cover
                acc = new_acc
        n >>= 1
        if n:
            new_base = _h_binary_callable(
                base,
                base,
                lambda lhs, rhs: _apply_opname(lhs, "__add__", "__radd__", rhs),
            )
            if new_base is NotImplemented:
                return NotImplemented
            base = new_base
    return acc if acc is not None else {}


def _convolve_linear(
    mapping: Mapping[_ConvolvableT, int],
    n: int,
) -> dict[_ConvolvableT, int] | NotImplementedType:
    #     mapping: Mapping[Any, int],
    #     n: int,
    # ) -> dict[Any, int] | NotImplementedType:
    r"""
    Linear fallback: `#!math O \left( n \right)` steps, always adding the original mapping.
    """
    result: dict[Any, int] = dict(mapping)
    for _ in range(1, n):
        new_result = _h_binary_callable(
            result,
            mapping,
            lambda lhs, rhs: _apply_opname(lhs, "__add__", "__radd__", rhs),
        )
        if new_result is NotImplemented:
            return NotImplemented
        result = new_result
    return result


def _flatten_to_h(rhs: object) -> object:
    r"""
    If *rhs* is an `#!python HableT` but not already an `#!python H`, coerce it to `#!python H` via `#!python .h()`.
    Otherwise return *rhs* unchanged.

    Used in forward binary operators so that `#!python H(…) + P(…)` is treated as `#!python H(…) + P(…).h()` rather than using `#!python P` as a scalar outcome.
    Also imported by [`dyce.hable`][dyce.hable] for use in [`HableOpsMixin`][dyce.HableOpsMixin] forward operators.
    """
    if isinstance(rhs, H):
        return rhs
    if isinstance(rhs, HableT):
        return rhs.h()
    return rhs


def _h_binary_callable(
    lhs_mapping: Mapping[Any, int],
    rhs_mapping: Mapping[Any, int],
    func: Callable[[Any, Any], Any],
) -> "dict[Any, int] | NotImplementedType":
    r"""
    Cartesian product: for each `#!python (lhs_outcome, lhs_count)` &times; `#!python (rhs_outcome, rhs_count)`, compute `#!python func(lhs_outcome, rhs_outcome)` and accumulate `#!python lhs_count * rhs_count`.
    Returns `#!python NotImplemented` immediately if *func* does.
    """
    result: dict[Any, int] = {}
    for (lhs_outcome, lhs_count), (rhs_outcome, rhs_count) in iproduct(
        lhs_mapping.items(), rhs_mapping.items()
    ):
        new_outcome = func(lhs_outcome, rhs_outcome)
        if new_outcome is NotImplemented:
            return NotImplemented
        result[new_outcome] = result.get(new_outcome, 0) + lhs_count * rhs_count
    return result


def _h_unary_opname(
    mapping: Mapping[Any, int],
    op_name: str,
) -> dict[Any, int] | NotImplementedType:
    r"""Apply a unary op to each outcome key, preserving counts."""
    result: dict[Any, int] = {}
    for outcome, count in mapping.items():
        op_fn = getattr(outcome, op_name, None)
        new_outcome = op_fn() if op_fn is not None else NotImplemented
        if new_outcome is NotImplemented:
            return NotImplemented
        result[new_outcome] = result.get(new_outcome, 0) + count
    return result


def _map_opname_fwd(
    mapping: Mapping[Any, int], op_name: str, rop_name: str, scalar: object
) -> dict[Any, int] | NotImplementedType:
    r"""
    Forward op with scalar rhs: apply [`_apply_opname`][dyce.h._apply_opname] across all outcome keys.
    """
    result: dict[Any, int] = {}
    for outcome, count in mapping.items():
        new_outcome = _apply_opname(outcome, op_name, rop_name, scalar)
        if new_outcome is NotImplemented:
            return NotImplemented
        result[new_outcome] = result.get(new_outcome, 0) + count
    return result


def _map_opname_ref(
    mapping: Mapping[Any, int],
    op_name: str,
    rop_name: str,
    scalar: object,
) -> dict[Any, int] | NotImplementedType:
    r"""
    Reflected op with scalar lhs: apply [`_apply_opname`][dyce.h._apply_opname] across all outcome keys.
    """
    result: dict[Any, int] = {}
    for outcome, count in mapping.items():
        new_outcome = _apply_opname(scalar, op_name, rop_name, outcome)
        if new_outcome is NotImplemented:
            return NotImplemented
        result[new_outcome] = result.get(new_outcome, 0) + count
    return result

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
import weakref
from abc import abstractmethod
from collections import defaultdict, deque
from copy import copy
from itertools import chain
from operator import (
    __abs__,
    __add__,
    __and__,
    __eq__,
    __floordiv__,
    __ge__,
    __gt__,
    __index__,
    __invert__,
    __le__,
    __lt__,
    __mod__,
    __mul__,
    __ne__,
    __neg__,
    __or__,
    __pos__,
    __pow__,
    __sub__,
    __truediv__,
    __xor__,
    attrgetter,
)
from textwrap import indent
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
    overload,
)

from .bt import beartype
from .h import H, _BinaryOperatorT, _UnaryOperatorT
from .lifecycle import experimental
from .p import P
from .types import (
    CachingProtocolMeta,
    IndexT,
    IntT,
    OutcomeT,
    Protocol,
    _GetItemT,
    _IntCs,
    _OutcomeCs,
    as_int,
    getitems,
    runtime_checkable,
)

__all__ = ("R",)


# ---- Types ---------------------------------------------------------------------------


_ROperandT = Union[OutcomeT, "R"]
_ValueT = Union[OutcomeT, H, P]
_UnaryRollerOperatorT = Callable[
    ["RollOutcome"], Union["RollOutcome", Iterable["RollOutcome"]]
]
_BinaryRollerOperatorT = Callable[
    ["RollOutcome", "RollOutcome"], Union["RollOutcome", Iterable["RollOutcome"]]
]
_RollOutcomeOperandT = Union[OutcomeT, "RollOutcome"]


@runtime_checkable
class RollOutcomeOperatorT(
    Protocol,
    metaclass=CachingProtocolMeta,
):
    # TODO(posita): See <https://github.com/python/mypy/issues/11013>
    # __slots__: Tuple[str, ...] = ()

    def __call__(
        self,
        *roll_outcomes: RollOutcome,
    ) -> Union[RollOutcome, Iterable[RollOutcome]]:
        ...


# ---- Classes -------------------------------------------------------------------------


class R:
    r"""
    !!! warning "Experimental"

        This class (and its descendants) should be considered experimental and may
        change or disappear in future versions.

    Where [``H`` objects][dyce.h.H] and [``P`` objects][dyce.p.P] are used primarily for
    enumerating all weighted outcomes, ``R`` objects represent rollers. More
    specifically, they are immutable nodes assembled in tree-like structures to
    represent calculations. They generate rolls that conform to outcomes weighted
    according to those calculations without engaging in computationally expensive
    enumeration (unlike [``H``][dyce.h.H] and [``P``][dyce.p.P] objects). Roller trees
    are typically composed from various ``R`` class methods and operators as well as
    arithmetic operations.

    ``` python
    >>> from dyce import H, P, R
    >>> d6 = H(6)
    >>> r_d6 = R.from_value(d6) ; r_d6
    ValueRoller(value=H(6), annotation='')
    >>> ((4 * r_d6 + 3) ** 2 % 5).gt(2)
    BinaryOperationRoller(
      op=<function R.gt...>,
      left_source=BinaryOperationRoller(
          op=<built-in function mod>,
          left_source=BinaryOperationRoller(
              op=<built-in function pow>,
              left_source=BinaryOperationRoller(
                  op=<built-in function add>,
                  left_source=BinaryOperationRoller(
                      op=<built-in function mul>,
                      left_source=ValueRoller(value=4, annotation=''),
                      right_source=ValueRoller(value=H(6), annotation=''),
                      annotation='',
                    ),
                  right_source=ValueRoller(value=3, annotation=''),
                  annotation='',
                ),
              right_source=ValueRoller(value=2, annotation=''),
              annotation='',
            ),
          right_source=ValueRoller(value=5, annotation=''),
          annotation='',
        ),
      right_source=ValueRoller(value=2, annotation=''),
      annotation='',
    )

    ```

    !!! info

        No optimizations are made when initializing roller trees. They retain their
        exact structure, even where such structures could be trivially reduced.

        ``` python
        >>> r_6 = R.from_value(6)
        >>> r_6_abs_3 = 3 @ abs(r_6)
        >>> r_6_abs_6_abs_6_abs = R.from_rs(abs(r_6), abs(r_6), abs(r_6))
        >>> tuple(r_6_abs_3.roll().outcomes()), tuple(r_6_abs_6_abs_6_abs.roll().outcomes())  # they generate the same rolls
        ((6, 6, 6), (6, 6, 6))
        >>> r_6_abs_3 == r_6_abs_6_abs_6_abs  # and yet, they're different animals
        False

        ```

        This is because the structure itself contains information that might be required
        by certain contexts. If such information loss is permissible and
        reduction is desirable, consider using [histograms][dyce.h.H] instead.

    Roller trees can can be queried via the [``roll`` method][dyce.r.R.roll], which
    produces [``Roll`` objects][dyce.r.Roll].

    ``` python
    >>> roll = r_d6.roll()
    >>> tuple(roll.outcomes())  # doctest: +SKIP
    (4,)
    >>> roll.total()  # doctest: +SKIP
    4

    ```

    ``` python
    >>> d6 + 3
    H({4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1})
    >>> (r_d6 + 3).roll().total() in (d6 + 3)
    True

    ```

    [``Roll`` objects][dyce.r.Roll] are much richer than mere outcomes. They are also
    tree-like structures that mirror the roller trees used to produce them, capturing
    references to rollers and the outcomes generated at each one.

    ``` python
    >>> roll = (r_d6 + 3).roll()
    >>> roll.total()  # doctest: +SKIP
    8
    >>> roll  # doctest: +SKIP
    Roll(
      r=,
      roll_outcomes=(
        RollOutcome(
          value=8,
          sources=(
            RollOutcome(
              value=3,
              sources=(),
            ),
            RollOutcome(
              value=5,
              sources=(),
            ),
          ),
        ),
      ),
      sources=(
        Roll(
          roll_outcomes=(
            RollOutcome(
              value=3,
              sources=(),
            ),
          ),
          sources=(),
        ),
        Roll(
          roll_outcomes=(
            RollOutcome(
              value=5,
              sources=(),
            ),
          ),
          sources=(),
        ),
      ),
    )

    ```

    Rollers provide optional arbitrary annotations as a convenience to callers. They are
    taken into account when comparing roller trees, but otherwise ignored internally.
    One use is to capture references to corresponding rollers in an abstract syntax tree
    generated from parsing a proprietary grammar. Any provided *annotation* can be
    retrieved using the [``annotation`` property][dyce.r.R.annotation]. The
    [``annotate`` method][dyce.r.R.annotate] can be used to apply an annotation to
    existing roller.

    The ``R`` class itself acts as a base from which several computation-specific
    implementations derive (such as expressing operands like outcomes or histograms,
    unary operations, binary operations, pools, etc.). In most cases, details of those
    implementations can be safely ignored.
    """
    __slots__: Tuple[str, ...] = ("_annotation", "_sources")

    # ---- Initializer -----------------------------------------------------------------

    @experimental
    @beartype
    def __init__(
        self,
        sources: Iterable["R"] = (),
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__()
        self._sources = tuple(sources)
        self._annotation = annotation

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  sources=({_seq_repr(self.sources)}),
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        if isinstance(other, R):
            return (
                (isinstance(self, type(other)) or isinstance(other, type(self)))
                and __eq__(self.sources, other.sources)
                and __eq__(self.annotation, other.annotation)
            )
        else:
            return super().__eq__(other)

    @beartype
    def __ne__(self, other) -> bool:
        if isinstance(other, R):
            return not __eq__(self, other)
        else:
            return super().__ne__(other)

    @beartype
    def __add__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __sub__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rsub__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mul__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmul__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __matmul__(self, other: IntT) -> R:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return RepeatRoller(other, self)

    @beartype
    def __rmatmul__(self, other: IntT) -> R:
        return self.__matmul__(other)

    @beartype
    def __truediv__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rtruediv__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __floordiv__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rfloordiv__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mod__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmod__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __pow__(self, other: _ROperandT) -> BinaryOperationRoller:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rpow__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __and__(self, other: Union["R", IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__and__, other)
            else:
                return self.map(__and__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rand__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __and__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __xor__(self, other: Union["R", IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__xor__, other)
            else:
                return self.map(__xor__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rxor__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __xor__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __or__(self, other: Union["R", IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__or__, other)
            else:
                return self.map(__or__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __ror__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __or__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __neg__(self) -> UnaryOperationRoller:
        return self.umap(__neg__)

    @beartype
    def __pos__(self) -> UnaryOperationRoller:
        return self.umap(__pos__)

    @beartype
    def __abs__(self) -> UnaryOperationRoller:
        return self.umap(__abs__)

    @beartype
    def __invert__(self) -> UnaryOperationRoller:
        return self.umap(__invert__)

    @abstractmethod
    def roll(self) -> Roll:
        r"""
        Sub-classes should implement this to return a new [``Roll`` object][dyce.r.Roll]
        appropriate for a particular roller (taking into account any sources).
        """
        ...

    # ---- Properties ------------------------------------------------------------------

    @property
    def annotation(self) -> Any:
        r"""
        Any provided annotation.
        """
        return self._annotation

    @property
    def sources(self) -> Tuple[R, ...]:
        r"""
        The roller’s direct sources (if any).
        """
        return self._sources

    # ---- Methods ---------------------------------------------------------------------

    @classmethod
    @beartype
    def from_rs(
        cls,
        *sources: R,
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Shorthand for ``#!python cls.from_rs_iterable(rs, annotation=annotation)``.

        See the [``from_rs_iterable`` method][dyce.r.R.from_rs_iterable].
        """
        return cls.from_rs_iterable(sources, annotation=annotation)

    @classmethod
    @beartype
    def from_rs_iterable(
        cls,
        sources: Iterable["R"],
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Creates and returns a roller for “pooling” zero or more *sources*. The returned
        roller will generate rolls whose items will contain one value for each source.

        ``` python
        >>> r_pool = R.from_rs_iterable(R.from_value(h) for h in (H((1, 2)), H((3, 4)), H((5, 6))))
        >>> roll = r_pool.roll()
        >>> tuple(roll.outcomes())  # doctest: +SKIP
        (2, 4, 6)
        >>> roll  # doctest: +SKIP
        Roll(
          r=,
          roll_outcomes=(
            RollOutcome(
              value=2,
              sources=(
                RollOutcome(
                  value=2,
                  sources=(),
                ),
              ),
            ),
            RollOutcome(
              value=4,
              sources=(
                RollOutcome(
                  value=4,
                  sources=(),
                ),
              ),
            ),
            RollOutcome(
              value=6,
              sources=(
                RollOutcome(
                  value=6,
                  sources=(),
                ),
              ),
            ),
          ),
          sources=...,
        )

        ```
        """
        return PoolRoller(sources, annotation=annotation)

    @classmethod
    @beartype
    def from_value(
        cls,
        value: _ValueT,
        annotation: Any = "",
    ) -> ValueRoller:
        r"""
        Creates and returns a roller without any sources for representing a single *value*
        (i.e., scalar or histogram).

        ``` python
        >>> R.from_value(6)
        ValueRoller(value=6, annotation='')

        ```

        ``` python
        >>> R.from_value(H(6))
        ValueRoller(value=H(6), annotation='')

        ```

        ``` python
        >>> R.from_value(P(6, 6))
        ValueRoller(value=P(6, 6), annotation='')

        ```
        """
        return ValueRoller(value, annotation=annotation)

    @classmethod
    @beartype
    def from_values(
        cls,
        *values: _ValueT,
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Shorthand for ``#!python cls.from_values_iterable(values, annotation=annotation)``.

        See the [``from_values_iterable`` method][dyce.r.R.from_values_iterable].
        """
        return cls.from_values_iterable(values, annotation=annotation)

    @classmethod
    @beartype
    def from_values_iterable(
        cls,
        values: Iterable[_ValueT],
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Shorthand for
        ``#!python cls.from_rs_iterable((cls.from_value(value) for value in values), annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``from_rs_iterable``][dyce.r.R.from_rs_iterable] methods.
        """
        return cls.from_rs_iterable(
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @classmethod
    @beartype
    def select_from_rs(
        cls,
        which: Iterable[_GetItemT],
        *sources: R,
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Shorthand for ``#!python R.select_from_rs_iterable(which, sources,
        annotation=annotation)``.

        See the [``select_from_rs_iterable`` method][dyce.r.R.select_from_rs_iterable].
        """
        return cls.select_from_rs_iterable(which, sources, annotation=annotation)

    @classmethod
    @beartype
    def select_from_rs_iterable(
        cls,
        which: Iterable[_GetItemT],
        sources: Iterable["R"],
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Creates and returns a roller for applying an *n*-ary selection *which* to sorted
        outcomes from this roller as its source.

        ``` python
        >>> r_select = R.select_from_values(
        ...   (0, -1, slice(3, 6), slice(6, 3, -1), -1, 0),
        ...   5, 4, 6, 3, 7, 2, 8, 1, 9, 0,
        ... ) ; r_select
        SelectionRoller(
          which=(0, -1, slice(3, 6, None), slice(6, 3, -1), -1, 0),
          sources=(
            ValueRoller(value=5, annotation=''),
            ValueRoller(value=4, annotation=''),
            ...,
            ValueRoller(value=9, annotation=''),
            ValueRoller(value=0, annotation=''),
          ),
          annotation='',
        )
        >>> tuple(r_select.roll().outcomes())
        (0, 9, 3, 4, 5, 6, 5, 4, 9, 0)

        ```
        """
        return SelectionRoller(which, sources, annotation=annotation)

    @classmethod
    @beartype
    def select_from_values(
        cls,
        which: Iterable[_GetItemT],
        *values: _ValueT,
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Shorthand for ``#!python R.select_from_values_iterable(which, sources,
        annotation=annotation)``.

        See the
        [``select_from_values_iterable`` method][dyce.r.R.select_from_values_iterable].
        """
        return cls.select_from_values_iterable(which, values, annotation=annotation)

    @classmethod
    @beartype
    def select_from_values_iterable(
        cls,
        which: Iterable[_GetItemT],
        values: Iterable[_ValueT],
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Shorthand for ``#!python cls.select_from_rs_iterable((cls.from_value(value) for
        value in values), annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``select_from_rs_iterable``][dyce.r.R.select_from_rs_iterable] methods.
        """
        return cls.select_from_rs_iterable(
            which,
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @beartype
    def select(
        self,
        *which: _GetItemT,
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Shorthand for ``#!python self.select_iterable(which, annotation=annotation)``.

        See the [``select_iterable`` method][dyce.r.R.select_iterable].
        """
        return self.select_iterable(which, annotation=annotation)

    @beartype
    def select_iterable(
        self,
        which: Iterable[_GetItemT],
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Creates and returns a roller for applying an *n*-ary selection *which* to sorted
        outcomes from this roller as its source.

        ``` python
        >>> r_values = R.from_values(5, 4, 6, 3, 7, 2, 8, 1, 9, 0)
        >>> r_select = r_values.select(0, -1, slice(3, 6), slice(6, 3, -1), -1, 0) ; r_select
        SelectionRoller(
          which=(0, -1, slice(3, 6, None), slice(6, 3, -1), -1, 0),
          sources=(
            PoolRoller(
              sources=(
                ValueRoller(value=5, annotation=''),
                ValueRoller(value=4, annotation=''),
                ...,
                ValueRoller(value=9, annotation=''),
                ValueRoller(value=0, annotation=''),
              ),
              annotation='',
            ),
          ),
          annotation='',
        )
        >>> tuple(r_select.roll().outcomes())
        (0, 9, 3, 4, 5, 6, 5, 4, 9, 0)

        ```
        """
        return SelectionRoller(which, (self,), annotation=annotation)

    @beartype
    def annotate(self, annotation: Any = "") -> R:
        r"""
        Generates a copy of the roller with the desired annotation.

        ``` python
        >>> r_just_the_n_of_us = R.from_value(5, annotation="But I'm 42!") ; r_just_the_n_of_us
        ValueRoller(value=5, annotation="But I'm 42!")
        >>> r_just_the_n_of_us.annotate("I'm a 42-year-old investment banker!")
        ValueRoller(value=5, annotation="I'm a 42-year-old investment banker!")

        ```
        """
        r = copy(self)
        r._annotation = annotation

        return r

    @beartype
    def map(
        self,
        op: _BinaryRollerOperatorT,
        right_operand: _ROperandT,
        annotation: Any = "",
    ) -> BinaryOperationRoller:
        r"""
        Creates and returns a roller for applying binary operator *op* to this roller and
        *right_operand* as its sources. Shorthands exist for many arithmetic operators
        and comparators.

        ``` python
        >>> import operator
        >>> r_binop = R.from_value(H(6)).map(operator.__pow__, 2) ; r_binop
        BinaryOperationRoller(
          op=<built-in function pow>,
          left_source=ValueRoller(value=H(6), annotation=''),
          right_source=ValueRoller(value=2, annotation=''),
          annotation='',
        )
        >>> r_binop == R.from_value(H(6)) ** 2
        True

        ```
        """
        if isinstance(right_operand, _OutcomeCs):
            right_operand = ValueRoller(right_operand)

        if isinstance(right_operand, R):
            return BinaryOperationRoller(op, self, right_operand, annotation=annotation)
        else:
            raise NotImplementedError

    @beartype
    def rmap(
        self,
        left_operand: OutcomeT,
        op: _BinaryRollerOperatorT,
        annotation: Any = "",
    ) -> BinaryOperationRoller:
        r"""
        Analogous to the [``map`` method][dyce.r.R.map], but where the caller supplies
        *left_operand*.

        ``` python
        >>> import operator
        >>> r_binop = R.from_value(H(6)).rmap(2, operator.__pow__) ; r_binop
        BinaryOperationRoller(
          op=<built-in function pow>,
          left_source=ValueRoller(value=2, annotation=''),
          right_source=ValueRoller(value=H(6), annotation=''),
          annotation='',
        )
        >>> r_binop == 2 ** R.from_value(H(6))
        True

        ```
        """
        if isinstance(left_operand, _OutcomeCs):
            return BinaryOperationRoller(
                op,
                ValueRoller(left_operand),
                self,
                annotation=annotation,
            )
        else:
            raise NotImplementedError

    @beartype
    def umap(
        self,
        op: _UnaryRollerOperatorT,
        annotation: Any = "",
    ) -> UnaryOperationRoller:
        r"""
        Creates and returns a roller for applying unary operator *op* to this roller as its
        source.

        ``` python
        >>> import operator
        >>> r_unop = R.from_value(H(6)).umap(operator.__neg__) ; r_unop
        UnaryOperationRoller(
          op=<built-in function neg>,
          source=ValueRoller(value=H(6), annotation=''),
          annotation='',
        )
        >>> r_unop == -R.from_value(H(6))
        True

        ```
        """
        return UnaryOperationRoller(op, self, annotation=annotation)

    @beartype
    def lt(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.lt(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _lt(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.lt(right_operand)

        return self.map(_lt, other)

    @beartype
    def le(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.le(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _le(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.le(right_operand)

        return self.map(_le, other)

    @beartype
    def eq(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.eq(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _eq(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.eq(right_operand)

        return self.map(_eq, other)

    @beartype
    def ne(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.ne(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _ne(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.ne(right_operand)

        return self.map(_ne, other)

    @beartype
    def gt(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.gt(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _gt(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.gt(right_operand)

        return self.map(_gt, other)

    @beartype
    def ge(self, other: _ROperandT) -> BinaryOperationRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.ge(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _ge(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.ge(right_operand)

        return self.map(_ge, other)

    @beartype
    def is_even(self) -> UnaryOperationRoller:
        r"""
        Shorthand for: ``#!python self.umap(lambda operand: (operand % 2).eq(0))``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_even(operand: RollOutcome) -> RollOutcome:
            return __mod__(operand, 2).eq(0)

        return self.umap(_is_even)

    @beartype
    def is_odd(self) -> UnaryOperationRoller:
        r"""
        Shorthand for: ``#!python self.umap(lambda operand: (operand % 2).ne(0))``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_odd(operand: RollOutcome) -> RollOutcome:
            return __mod__(operand, 2).ne(0)

        return self.umap(_is_odd)


class ValueRoller(R):
    r"""
    A [roller][dyce.r.R] without any sources for representing a single *value* (i.e., a
    single outcome or a histogram).
    """
    __slots__: Tuple[str, ...] = ("_value",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        value: _ValueT,
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__((), annotation)

        if isinstance(value, P) and not value.is_homogeneous:
            warnings.warn(
                f"using a heterogeneous pool ({value}) is not recommended where traceability is important",
                stacklevel=2,
            )

        self._value = value

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"{type(self).__name__}(value={self.value!r}, annotation={self.annotation!r})"

    @beartype
    def roll(self) -> Roll:
        r""""""
        if isinstance(self.value, P):
            return Roll(
                self,
                roll_outcomes=(RollOutcome(outcome) for outcome in self.value.roll()),
            )
        elif isinstance(self.value, H):
            return Roll(self, roll_outcomes=(RollOutcome(self.value.roll()),))
        elif isinstance(self.value, _OutcomeCs):
            return Roll(self, roll_outcomes=(RollOutcome(self.value),))

    # ---- Properties ------------------------------------------------------------------

    @property
    def value(self) -> _ValueT:
        r"""
        The single value for this leaf node roller.
        """
        return self._value


class OperationRollerBase(R):
    r"""
    An abstract [roller][dyce.r.R] for applying *op* to some variation of outcomes from
    *sources*. (The specific variation is left up to the
    [``R.roll`` method][dyce.r.R.roll] implementation of any subclass.)
    """
    __slots__: Tuple[str, ...] = ("_op",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        op: RollOutcomeOperatorT,
        sources: Iterable[R] = (),
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__(sources, annotation)
        self._op = op

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  op={self.op!r},
  sources=({_seq_repr(self.sources)}),
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.op == other.op

    # ---- Properties ------------------------------------------------------------------

    @property
    def op(self) -> RollOutcomeOperatorT:
        r"""
        The operator this roller applies to its sources.
        """
        return self._op


class ChainRoller(OperationRollerBase):
    r"""
    A roller deriving from [``OperationRollerBase``][dyce.r.OperationRollerBase] for
    applying *op* to the chained outcomes from each of *sources*.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = tuple(source.roll() for source in self.sources)
        roll_outcomes = tuple(
            roll_outcome
            for roll_outcome in chain.from_iterable(source_rolls)
            if roll_outcome.value is not None
        )
        res = self.op(*roll_outcomes)

        if isinstance(res, RollOutcome):
            res = (res,)

        return Roll(
            self,
            roll_outcomes=res,
            sources=source_rolls,
        )


class SumRoller(OperationRollerBase):
    r"""
    A roller deriving from [``OperationRollerBase``][dyce.r.OperationRollerBase] for
    applying *op* to the sum of outcomes grouped by each of *sources*.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = tuple(source.roll() for source in self.sources)

        def _roll_outcomes() -> Iterator[RollOutcome]:
            for source_roll in source_rolls:
                if len(source_roll) == 1:
                    yield from source_roll
                elif len(source_roll) > 1:
                    yield RollOutcome(
                        sum(roll_outcome.value for roll_outcome in source_roll),
                        sources=source_roll,
                    )

        res = self.op(*_roll_outcomes())

        if isinstance(res, RollOutcome):
            res = (res,)

        return Roll(
            self,
            roll_outcomes=res,
            sources=source_rolls,
        )


class BinaryOperationRoller(SumRoller):
    r"""
    A [``SumRoller``][dyce.r.SumRoller] for applying a binary operator *op* to the sum
    of all outcomes from its *left_source* and the sum of all outcomes from its
    *right_source*.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        op: _BinaryRollerOperatorT,
        left_source: R,
        right_source: R,
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__(
            cast(RollOutcomeOperatorT, op), (left_source, right_source), annotation
        )

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        def _source_repr(source: R) -> str:
            return indent(repr(source), "    ").strip()

        left_source, right_source = self.sources

        return f"""{type(self).__name__}(
  op={self.op!r},
  left_source={_source_repr(left_source)},
  right_source={_source_repr(right_source)},
  annotation={self.annotation!r},
)"""


class UnaryOperationRoller(SumRoller):
    r"""
    A [``SumRoller``][dyce.r.SumRoller] for applying a unary operator *op* to the sum of
    all outcomes from its sole *source*.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        op: _UnaryRollerOperatorT,
        source: R,
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__(cast(RollOutcomeOperatorT, op), (source,), annotation)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        (source,) = self.sources

        return f"""{type(self).__name__}(
  op={self.op!r},
  source={indent(repr(source), "  ").strip()},
  annotation={self.annotation!r},
)"""


class PoolRoller(ChainRoller):
    r"""
    A [``ChainRoller``][dyce.r.ChainRoller] for “pooling” zero or more roller *sources*.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        sources: Iterable[R] = (),
        annotation: Any = "",
    ):
        r"Initializer."

        def _pool(*source_outcomes: RollOutcome) -> Iterable[RollOutcome]:
            for source_outcome in source_outcomes:
                yield RollOutcome(
                    source_outcome.value,
                    sources=(source_outcome,),
                )

        super().__init__(_pool, sources, annotation)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  sources=({_seq_repr(self.sources)}),
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super(OperationRollerBase, self).__eq__(other)


class SelectionRoller(ChainRoller):
    r"""
    A [``ChainRoller``][dyce.r.ChainRoller] for sorting outcomes from its roller
    *sources* and applying a selector *which*.

    Roll outcomes in created rolls are ordered according to the selections *which*.
    However, those selections reference values in a *sorted* view of the source’s roll
    outcomes.

    <!--
    ``` python
    >>> from typing import Tuple, Union
    >>> which: Tuple[Union[int, slice], ...]

    ```

    -->

    ``` python
    >>> r_values = R.from_values(10000, 1, 1000, 10, 100)
    >>> outcomes = tuple(r_values.roll().outcomes()) ; outcomes
    (10000, 1, 1000, 10, 100)
    >>> sorted_outcomes = tuple(sorted(outcomes)) ; sorted_outcomes
    (1, 10, 100, 1000, 10000)
    >>> which = (3, 1, 3, 2)
    >>> tuple(sorted_outcomes[i] for i in which)
    (1000, 10, 1000, 100)
    >>> r_select = r_values.select_iterable(which) ; r_select
    SelectionRoller(
      which=(3, 1, 3, 2),
      sources=(
        PoolRoller(
          sources=(
            ValueRoller(value=10000, annotation=''),
            ValueRoller(value=1, annotation=''),
            ValueRoller(value=1000, annotation=''),
            ValueRoller(value=10, annotation=''),
            ValueRoller(value=100, annotation=''),
          ),
          annotation='',
        ),
      ),
      annotation='',
    )
    >>> roll = r_select.roll()
    >>> tuple(roll.outcomes())
    (1000, 10, 1000, 100)
    >>> roll
    Roll(
      r=...,
      roll_outcomes=(
        RollOutcome(
          value=1000,
          sources=(
            RollOutcome(
              value=1000, ...,
            ),
          ),
        ),
        RollOutcome(
          value=10,
          sources=(
            RollOutcome(
              value=10, ...,
            ),
          ),
        ),
        RollOutcome(
          value=1000,
          sources=(
            RollOutcome(
              value=1000, ...,
              ),
            ),
          ),
        ),
        RollOutcome(
          value=100,
          sources=(
            RollOutcome(
              value=100, ...,
            ),
          ),
        ),
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=1, ...,
              ),
            ),
          ),
        ),
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=10000, ...,
            ),
          ),
        ),
      ),
    )

    ```
    """
    __slots__: Tuple[str, ...] = ("_which",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        which: Iterable[_GetItemT],
        sources: Iterable[R] = (),
        annotation: Any = "",
    ):
        r"Initializer."

        def _select_which(*source_outcomes: RollOutcome) -> Iterable[RollOutcome]:
            all_indexes = tuple(range(len(source_outcomes)))
            selected_indexes = tuple(getitems(all_indexes, self.which))
            unique_selected_indexes = set(selected_indexes)
            source_outcomes_sorted = sorted(source_outcomes, key=attrgetter("value"))
            roll_outcomes_by_index = {
                index: RollOutcome(
                    value=source_outcomes_sorted[index].value
                    if index in unique_selected_indexes
                    else None,
                    sources=(source_outcomes_sorted[index],),
                )
                for index in all_indexes
            }

            for selected_index in selected_indexes:
                yield roll_outcomes_by_index[selected_index]

            for excluded_index in set(all_indexes) - unique_selected_indexes:
                yield roll_outcomes_by_index[excluded_index]

        super().__init__(_select_which, sources, annotation)
        self._which = tuple(which)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  which={self.which!r},
  sources=({_seq_repr(self.sources)}),
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return (
            super(OperationRollerBase, self).__eq__(other) and self.which == other.which
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def which(self) -> Tuple[_GetItemT, ...]:
        r"""
        The selector this roller applies to the sorted outcomes of its sole source.
        """
        return self._which


class RepeatRoller(R):
    r"""
    A [roller][dyce.r.R] to implement the ``#!python __matmul__`` operator. It is akin
    to a homogeneous [``PoolRoller``][dyce.r.PoolRoller] containing *n* copies of its
    sole *source*.

    ``` python
    >>> d20 = H(20)
    >>> r_d20 = R.from_value(d20)
    >>> r_d20_100 = 100@r_d20 ; r_d20_100
    RepeatRoller(
      n=100,
      source=ValueRoller(value=H(20), annotation=''),
      annotation='',
    )
    >>> all(outcome in d20 for outcome in r_d20_100.roll().outcomes())
    True

    ```
    """
    __slots__: Tuple[str, ...] = ("_n",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        n: IntT,
        source: R,
        annotation: Any = "",
    ):
        r"Initializer."
        super().__init__((source,), annotation)
        self._n = as_int(n)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        (source,) = self.sources

        return f"""{type(self).__name__}(
  n={self.n!r},
  source={indent(repr(source), "  ").strip()},
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.n == other.n

    @beartype
    def roll(self) -> Roll:
        r""""""
        (source,) = self.sources
        source_rolls = tuple(source.roll() for _ in range(self.n))

        def _roll_outcome_gen() -> Iterable[RollOutcome]:
            for source_roll in source_rolls:
                for source_outcome in source_roll:
                    if source_outcome.value is not None:
                        yield RollOutcome(
                            source_outcome.value,
                            sources=(source_outcome,),
                        )

        return Roll(self, roll_outcomes=_roll_outcome_gen(), sources=source_rolls)

    # ---- Properties ------------------------------------------------------------------

    @property
    def n(self) -> int:
        r"""
        The number of times to “repeat” the roller’s sole source.
        """
        return self._n


class RollOutcome:
    r"""
    !!! warning "Experimental"

        This class should be considered experimental and may change or disappear in
        future versions.

    A single, ([mostly][dyce.r.Roll.__init__]) immutable outcome generated by a roll.
    """
    __slots__: Tuple[str, ...] = ("_roll", "_sources", "_value")

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        value: Optional[OutcomeT],
        sources: Iterable["RollOutcome"] = (),
    ):
        r"Initializer."
        super().__init__()
        self._value = value
        self._sources = tuple(sources)
        # These are back-references to rolls used to aggregate roll outcomes. We use a
        # weakref here to avoid circular references that might frustrate or delay
        # garbage collection efforts
        self._roll: Optional[weakref.ref[Roll]] = None

        if self._value is None and not self._sources:
            raise ValueError("value can only be None if sources is non-empty")

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  value={repr(self.value)},
  sources=({_seq_repr(self.sources)}),
)"""

    @beartype
    # TODO(posita): See <https://github.com/python/mypy/issues/10943>
    def __lt__(self, other: _RollOutcomeOperandT) -> bool:  # type: ignore
        if isinstance(other, RollOutcome):
            return __lt__(self.value, other.value)
        else:
            return NotImplemented

    @beartype
    # TODO(posita): See <https://github.com/python/mypy/issues/10943>
    def __le__(self, other: _RollOutcomeOperandT) -> bool:  # type: ignore
        if isinstance(other, RollOutcome):
            return __le__(self.value, other.value)
        else:
            return NotImplemented

    @beartype
    def __eq__(self, other) -> bool:
        if isinstance(other, RollOutcome):
            return __eq__(self.value, other.value)
        else:
            return super().__eq__(other)

    @beartype
    def __ne__(self, other) -> bool:
        if isinstance(other, RollOutcome):
            return __ne__(self.value, other.value)
        else:
            return super().__ne__(other)

    @beartype
    def __gt__(self, other: _RollOutcomeOperandT) -> bool:
        if isinstance(other, RollOutcome):
            return __gt__(self.value, other.value)
        else:
            return NotImplemented

    @beartype
    def __ge__(self, other: _RollOutcomeOperandT) -> bool:
        if isinstance(other, RollOutcome):
            return __ge__(self.value, other.value)
        else:
            return NotImplemented

    @beartype
    def __add__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __sub__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rsub__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mul__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmul__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __truediv__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rtruediv__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __floordiv__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rfloordiv__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mod__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmod__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __pow__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rpow__(self, other: OutcomeT) -> RollOutcome:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __and__(self, other: Union["RollOutcome", IntT]) -> RollOutcome:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__and__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rand__(self, other: IntT) -> RollOutcome:
        try:
            return self.rmap(as_int(other), __and__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __xor__(self, other: Union["RollOutcome", IntT]) -> RollOutcome:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__xor__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rxor__(self, other: IntT) -> RollOutcome:
        try:
            return self.rmap(as_int(other), __xor__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __or__(self, other: Union["RollOutcome", IntT]) -> RollOutcome:
        try:
            if isinstance(other, _IntCs):
                other = as_int(other)

            return self.map(__or__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __ror__(self, other: IntT) -> RollOutcome:
        try:
            return self.rmap(as_int(other), __or__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __neg__(self) -> RollOutcome:
        return self.umap(__neg__)

    @beartype
    def __pos__(self) -> RollOutcome:
        return self.umap(__pos__)

    @beartype
    def __abs__(self) -> RollOutcome:
        return self.umap(__abs__)

    @beartype
    def __invert__(self) -> RollOutcome:
        return self.umap(__invert__)

    # ---- Properties ------------------------------------------------------------------

    @property
    def annotation(self) -> Any:
        r"""
        Shorthand for ``#!python self.roll.annotation``.

        See the [``roll``][dyce.r.RollOutcome.roll] and
        [``Roll.annotation``][dyce.r.Roll.annotation] properties.
        """
        return self.roll.annotation

    @property
    def r(self) -> R:
        r"""
        Shorthand for ``#!python self.roll.r``.

        See the [``roll``][dyce.r.RollOutcome.roll] and [``Roll.r``][dyce.r.Roll.r]
        properties.
        """
        return self.roll.r

    @property
    def roll(self) -> Roll:
        r"""
        Returns the roll if one has been associated with this roll outcome. Usually that is
        done via the [``Roll.__init__`` method][dyce.r.Roll.__init__]. Accessing this
        property before the roll outcome has been associated with a roll is considered
        a programming error.

        ``` python
        >>> from dyce.r import Roll, RollOutcome
        >>> ro = RollOutcome(4)
        >>> ro.roll
        Traceback (most recent call last):
          ...
        AssertionError: RollOutcome.roll accessed before associating the roll outcome with a roll (usually via Roll.__init__)
        assert None is not None
        >>> roll = Roll(R.from_value(4), roll_outcomes=(ro,))
        >>> ro.roll
        Roll(
          r=ValueRoller(value=4, annotation=''),
          roll_outcomes=(
            RollOutcome(
              value=4,
              sources=(),
            ),
          ),
          sources=(),
        )

        ```
        """
        assert (
            self._roll is not None
        ), "RollOutcome.roll accessed before associating the roll outcome with a roll (usually via Roll.__init__)"
        roll = self._roll()
        assert (
            roll is not None
        ), "RollOutcome.roll accessed after the roll associated the roll outcome was destroyed"

        return roll

    @property
    def sources(self) -> Tuple[RollOutcome, ...]:
        r"""
        The source roll outcomes from which this roll outcome was generated.
        """
        return self._sources

    @property
    def value(self) -> Optional[OutcomeT]:
        r"""
        The outcome value. A value of ``#!python None`` is used to signal that a source’s
        roll outcome was excluded by the roller.
        """
        return self._value

    # ---- Methods ---------------------------------------------------------------------

    @beartype
    def map(
        self,
        op: _BinaryOperatorT,
        right_operand: _RollOutcomeOperandT,
    ) -> RollOutcome:
        r"""
        Applies *op* to the value of this roll outcome as the left operand and
        *right_operand* as the right. Shorthands exist for many arithmetic operators and
        comparators.

        ``` python
        >>> import operator
        >>> from dyce.r import RollOutcome
        >>> two = RollOutcome(2)
        >>> two.map(operator.__pow__, 10)
        RollOutcome(
          value=1024,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        )
        >>> two.map(operator.__pow__, 10) == two ** 10
        True

        ```
        """
        if isinstance(right_operand, RollOutcome):
            sources: Tuple[RollOutcome, ...] = (self, right_operand)
            right_operand_value: Optional[OutcomeT] = right_operand.value
        else:
            sources = (self,)
            right_operand_value = right_operand

        if isinstance(right_operand_value, _OutcomeCs):
            return RollOutcome(op(self.value, right_operand_value), sources)
        else:
            raise NotImplementedError

    @beartype
    def rmap(
        self,
        left_operand: OutcomeT,
        op: _BinaryOperatorT,
    ) -> RollOutcome:
        r"""
        Analogous to the [``map`` method][dyce.r.RollOutcome.map], but where the caller
        supplies *left_operand*.

        ``` python
        >>> import operator
        >>> from dyce.r import RollOutcome
        >>> two = RollOutcome(2)
        >>> two.rmap(10, operator.__pow__)
        RollOutcome(
          value=100,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        )
        >>> two.rmap(10, operator.__pow__) == 10 ** two
        True

        ```
        """
        if isinstance(left_operand, _OutcomeCs):
            return RollOutcome(op(left_operand, self.value), sources=(self,))
        else:
            raise NotImplementedError

    @beartype
    def umap(
        self,
        op: _UnaryOperatorT,
    ) -> RollOutcome:
        r"""
        Applies *op* to the value of this roll outcome. Shorthands exist for many arithmetic
        operators and comparators.

        ``` python
        >>> import operator
        >>> from dyce.r import RollOutcome
        >>> two = RollOutcome(-2)
        >>> two.umap(operator.__neg__)
        RollOutcome(
          value=2,
          sources=(
            RollOutcome(
              value=-2,
              sources=(),
            ),
          ),
        )
        >>> two.umap(operator.__neg__) == -two
        True

        ```
        """
        return RollOutcome(op(self.value), sources=(self,))

    @beartype
    def lt(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__lt__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__lt__(self.value, other)), sources=(self,))

    @beartype
    def le(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__le__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__le__(self.value, other)), sources=(self,))

    @beartype
    def eq(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__eq__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__eq__(self.value, other)), sources=(self,))

    @beartype
    def ne(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__ne__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__ne__(self.value, other)), sources=(self,))

    @beartype
    def gt(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__gt__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__gt__(self.value, other)), sources=(self,))

    @beartype
    def ge(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return RollOutcome(
                bool(__ge__(self.value, other.value)), sources=(self, other)
            )
        else:
            return RollOutcome(bool(__ge__(self.value, other)), sources=(self,))


class Roll(Sequence[RollOutcome]):
    r"""
    !!! warning "Experimental"

        This class should be considered experimental and may change or disappear in
        future versions.

    An immutable roll result (or “roll” for short). More specifically, the result of
    calling the [``R.roll`` method][dyce.r.R.roll]. Rolls are sequences of
    [``RollOutcome`` objects][dyce.r.RollOutcome] with additional convenience methods.
    """
    __slots__: Tuple[str, ...] = ("__weakref__", "_r", "_roll_outcomes", "_sources")

    # ---- Initializer -----------------------------------------------------------------

    @experimental
    @beartype
    def __init__(
        self,
        r: R,
        roll_outcomes: Iterable[RollOutcome],
        sources: Iterable["Roll"] = (),
    ):
        r"""
        Initializer.

        If the [``R.annotation`` property][dyce.r.R.annotation] of the *r* argument is
        ``#!python None``, all history will be removed from any *roll_outcomes* and
        *sources* during initialization.

        !!! note

            Technically, this violates the immutability of roll outcomes.

            ``` python
            >>> from dyce.r import PoolRoller, Roll, RollOutcome
            >>> origin = RollOutcome(value=1)
            >>> descendant = RollOutcome(value=2, sources=(origin,)) ; descendant
            RollOutcome(
              value=2,
              sources=(
                RollOutcome(
                  value=1,
                  sources=(),
                ),
              ),
            )
            >>> roll = Roll(PoolRoller(annotation=None), roll_outcomes=(descendant,))
            >>> descendant  # sources are wiped out
            RollOutcome(
              value=2,
              sources=(),
            )

            ```

            ``dyce`` does not generally contemplate creation of rolls or roll outcomes
            outside the womb of [``R.roll``][dyce.r.R.roll] implementations.
            [``Roll``][dyce.r.Roll] and [``RollOutcome``][dyce.r.RollOutcome] objects
            generally mate for life, being created exclusively for (and in close
            proximity to) one another. A roll manipulating a roll outcome’s internal
            state post initialization may seem unseemly, but that intimacy is a
            fundamental part of their primordial ritual.

            More practically, it frees each roller from having to do its own cleaving.

            That being said, you’re an adult. Do what you want. Just know that if you’re
            going to create your own roll outcomes and pimp them out to different rolls
            all over town, they might come back with some parts missing.

            (See also the [``RollOutcome.roll`` property][dyce.r.RollOutcome.roll].)
        """
        super().__init__()
        self._r = r

        def _strip_roll_outcome_sources() -> Iterator[RollOutcome]:
            for roll_outcome in roll_outcomes:
                if roll_outcome.value is not None:
                    roll_outcome._sources = ()
                    yield roll_outcome

        if r.annotation is None:
            self._roll_outcomes: Tuple[RollOutcome, ...] = tuple(
                _strip_roll_outcome_sources()
            )
            self._sources: Tuple[Roll, ...] = ()
        else:
            self._roll_outcomes = tuple(roll_outcomes)
            self._sources = tuple(sources)

        for roll_outcome in self._roll_outcomes:
            roll_outcome._roll = weakref.ref(self)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  r={indent(repr(self.r), "  ").strip()},
  roll_outcomes=({_seq_repr(self)}),
  sources=({_seq_repr(self.sources)}),
)"""

    @beartype
    def __len__(self) -> int:
        return len(self._roll_outcomes)

    @overload
    def __getitem__(self, key: IndexT) -> RollOutcome:
        ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[RollOutcome, ...]:
        ...

    @beartype
    # TODO(posita): See <https://github.com/python/mypy/issues/8393>
    # TODO(posita): See <https://github.com/beartype/beartype/issues/39#issuecomment-871914114> et seq.
    def __getitem__(  # type: ignore
        self,
        key: _GetItemT,
    ) -> Union[RollOutcome, Tuple[RollOutcome, ...]]:
        if isinstance(key, slice):
            return self._roll_outcomes[key]
        else:
            return self._roll_outcomes[__index__(key)]

    @beartype
    def __iter__(self) -> Iterator[RollOutcome]:
        return iter(self._roll_outcomes)

    # ---- Properties ------------------------------------------------------------------

    @property
    def annotation(self) -> Any:
        r"""
        Shorthand for ``#!python self.r.annotation``.

        See the [``R.annotation`` property][dyce.r.R.annotation].
        """
        return self.r.annotation

    @property
    def r(self) -> R:
        r"""
        The roller that generated the roll.
        """
        return self._r

    @property
    def sources(self) -> Tuple[Roll, ...]:
        r"""
        The source roll from which this roll was generated.
        """
        return self._sources

    # ---- Methods ---------------------------------------------------------------------

    @beartype
    def outcomes(self) -> Iterator[OutcomeT]:
        r"""
        Shorthand for
        ``#!python (roll_outcome.value for roll_outcome in self if roll_outcome.value is not None)``.

        !!! info

            Unlike [``H.roll``][dyce.h.H.roll] and [``P.roll``][dyce.p.P.roll], these
            outcomes are *not* sorted. Instead, they retain the ordering from whence
            they came in the roller tree.

            ``` python
            >>> r_3d6 = 3@R.from_value(H(6))
            >>> r_3d6_neg = 3@-R.from_value(H(6))
            >>> roll = R.from_rs(r_3d6, r_3d6_neg).roll()
            >>> tuple(roll.outcomes())  # doctest: +SKIP
            (1, 4, 1, -5, -2, -3)
            >>> len(roll)
            6

            ```
        """
        return (
            roll_outcome.value
            for roll_outcome in self
            if roll_outcome.value is not None
        )

    @beartype
    def total(self) -> OutcomeT:
        r"""
        Shorthand for ``#!python sum(self.outcomes())``.
        """
        return sum(self.outcomes())


class RollWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``Roll`` object][dyce.r.Roll] found.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Overrides -------------------------------------------------------------------

    @abstractmethod
    def on_roll(self, roll: Roll, parents: Iterator[Roll]) -> None:
        ...


class RollOutcomeWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``RollOutcome`` object][dyce.r.RollOutcome] found.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Overrides -------------------------------------------------------------------

    @abstractmethod
    def on_roll_outcome(
        self, roll_outcome: RollOutcome, parents: Iterator[RollOutcome]
    ) -> None:
        ...


class RollerWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``R`` object][dyce.r.R] found.
    """
    __slots__: Tuple[str, ...] = ()

    # ---- Overrides -------------------------------------------------------------------

    @abstractmethod
    def on_roller(self, r: R, parents: Iterator[R]) -> None:
        ...


@experimental
@beartype
def walk(
    root: Union[Roll, R, RollOutcome],
    visitor: Union[RollWalkerVisitor, RollerWalkerVisitor, RollOutcomeWalkerVisitor],
) -> None:
    r"""
    !!! warning "Experimental"

        This function should be considered experimental and may change or disappear in
        future versions.

    Walks through *root*, calling *visitor* for each matching object. No ordering
    guarantees are made.

    !!! info "On the current implementation"

        ``walk`` performs a breadth-first traversal of *root*, assembling a secondary
        index of referencing objects (parents). Visitors are called back grouped first
        by type, then by order encountered.
    """
    rolls: Dict[int, Roll] = {}
    rollers: Dict[int, R] = {}
    roll_outcomes: Dict[int, RollOutcome] = {}
    roll_parent_ids: DefaultDict[int, Set[int]] = defaultdict(set)
    roller_parent_ids: DefaultDict[int, Set[int]] = defaultdict(set)
    roll_outcome_parent_ids: DefaultDict[int, Set[int]] = defaultdict(set)
    queue = deque((root,))
    roll: Roll
    r: R
    roll_outcome: RollOutcome

    while queue:
        obj = queue.popleft()

        if isinstance(obj, Roll):
            roll = obj

            if id(roll) not in rolls:
                rolls[id(roll)] = roll

                queue.append(roll.r)

                for i, roll_outcome in enumerate(roll):
                    queue.append(roll_outcome)

                for source_roll in roll.sources:
                    roll_parent_ids[id(source_roll)].add(id(roll))
                    queue.append(source_roll)
        elif isinstance(obj, R):
            r = obj

            if id(r) not in rollers:
                rollers[id(r)] = r

                for source_r in r.sources:
                    roller_parent_ids[id(source_r)].add(id(r))
                    queue.append(source_r)
        elif isinstance(obj, RollOutcome):
            roll_outcome = obj

            if id(roll_outcome) not in roll_outcomes:
                roll_outcomes[id(roll_outcome)] = roll_outcome

                for source_roll_outcome in roll_outcome.sources:
                    roll_outcome_parent_ids[id(source_roll_outcome)].add(
                        id(roll_outcome)
                    )
                    queue.append(source_roll_outcome)

    if rolls and isinstance(visitor, RollWalkerVisitor):
        for roll_id, roll in rolls.items():
            visitor.on_roll(roll, (rolls[i] for i in roll_parent_ids[roll_id]))

    if rollers and isinstance(visitor, RollerWalkerVisitor):
        for r_id, r in rollers.items():
            visitor.on_roller(r, (rollers[i] for i in roller_parent_ids[r_id]))

    if roll_outcomes and isinstance(visitor, RollOutcomeWalkerVisitor):
        for roll_outcome_id, roll_outcome in roll_outcomes.items():
            visitor.on_roll_outcome(
                roll_outcome,
                (roll_outcomes[i] for i in roll_outcome_parent_ids[roll_outcome_id]),
            )


# ---- Functions -----------------------------------------------------------------------


@beartype
def _seq_repr(s: Sequence) -> str:
    seq_repr = indent(",\n".join(repr(i) for i in s), "    ")

    return "\n" + seq_repr + ",\n  " if seq_repr else seq_repr

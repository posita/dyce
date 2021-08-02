# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from abc import abstractmethod
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
)
from textwrap import indent
from typing import Any, Iterable, Iterator, List, Sequence, Tuple, Union, overload

from .h import H, _BinaryOperatorT, _UnaryOperatorT
from .lifecycle import experimental
from .p import P
from .symmetries import sum_w_start
from .types import IndexT, IntT, OutcomeT, _GetItemT, _OutcomeCs, as_int

__all__ = (
    "R",
    "Roll",
)


# ---- Types ---------------------------------------------------------------------------


_OperandT = Union[OutcomeT, "R"]
_ValueT = Union[OutcomeT, H, P]
_RollItemT = Tuple[Tuple[OutcomeT, ...], Tuple["Roll", ...]]


# ---- Classes -------------------------------------------------------------------------


class R(Sequence["R"]):
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
    arithmetic operations:

    ```python
    >>> from dyce import H, P, R
    >>> d6 = H(6)
    >>> r_d6 = R.from_value(d6) ; r_d6
    ValueRoller(value=H(6), annotation=None)
    >>> ((4 * r_d6 + 3) ** 2 % 5).gt(2)
    BinaryOperationRoller(
      op=<function R.gt...>,
      left_child=BinaryOperationRoller(
          op=<built-in function mod>,
          left_child=BinaryOperationRoller(
              op=<built-in function pow>,
              left_child=BinaryOperationRoller(
                  op=<built-in function add>,
                  left_child=BinaryOperationRoller(
                      op=<built-in function mul>,
                      left_child=ValueRoller(value=4, annotation=None),
                      right_child=ValueRoller(value=H(6), annotation=None),
                      annotation=None,
                    ),
                  right_child=ValueRoller(value=3, annotation=None),
                  annotation=None,
                ),
              right_child=ValueRoller(value=2, annotation=None),
              annotation=None,
            ),
          right_child=ValueRoller(value=5, annotation=None),
          annotation=None,
        ),
      right_child=ValueRoller(value=2, annotation=None),
      annotation=None,
    )
    >>> (((4 * r_d6 + 3) ** 2 % 5).gt(2)).h() == ((4 * d6 + 3) ** 2 % 5).gt(2)
    True

    ```

    !!! tip

        No optimizations are made when constructing roller trees. They retain their
        exact structure, even where such structures could be trivially reduced:

        ```python
        >>> r_6 = R.from_value(6)
        >>> r_6_abs_3 = 3 @ abs(r_6)
        >>> r_6_3_abs = abs(3 @ r_6)
        >>> r_6_abs_3.h() == r_6_3_abs.h()  # their histograms are the same
        True
        >>> tuple(r_6_abs_3.roll().outcomes()), tuple(r_6_3_abs.roll().outcomes())  # they generate the same rolls
        ((6, 6, 6), (6, 6, 6))
        >>> r_6_abs_3 == r_6_3_abs  # and yet, they're different animals
        False

        ```

        This is because the structure itself contains information that might be required
        by certain contexts. If such information loss is permissible and
        reduction is desirable, consider using [histograms][dyce.h.H] instead.

    Roller trees can can be queried via the [``roll`` method][dyce.r.R.roll], which
    produce [``Roll`` objects][dyce.r.Roll]:

    ```python
    >>> roll = r_d6.roll()
    >>> roll.total  # doctest: +SKIP
    4
    >>> roll  # doctest: +SKIP
    Roll(
      r=ValueRoller(value=H(6), annotation=None),
      items=(
        ((4,), ()),
      ),
    )
    >>> (r_d6 + 3).roll().total in (d6 + 3)
    True

    ```

    [``Roll`` objects][dyce.r.Roll] are much richer than mere outcomes. They mirror the
    roller trees used to produce them, capturing references to nodes and the outcomes
    generated at each one:

    ```python
    >>> roll = (r_d6 + 3).roll()
    >>> roll.total  # doctest: +SKIP
    8
    >>> roll  # doctest: +SKIP
    Roll(
      r=BinaryOperationRoller(
        op=<built-in function add>,
        left_child=ValueRoller(value=H(6), annotation=None),
        right_child=ValueRoller(value=3, annotation=None),
        annotation=None,
      ),
      items=(
        ((8,), (
          Roll(
            r=ValueRoller(value=H(6), annotation=None),
            items=(
              ((5,), ()),
            ),
          ),
          Roll(
            r=ValueRoller(value=3, annotation=None),
            items=(
              ((3,), ()),
            ),
          ),
        )),
      ),
    )

    ```

    Rollers provide optional arbitrary annotations as a convenience to callers. They are
    considered during roller tree comparison, but otherwise ignored internally. One use
    is to capture references to corresponding nodes in an abstract syntax tree generated
    from parsing a proprietary grammar. Any provided *annotation* can be retrieved using
    the [``annotation`` property][dyce.r.R.annotation]. The
    [``annotate`` method][dyce.r.R.annotate] can be used to modify an annotation for
    existing roller.

    The ``R`` class itself acts as a base from which several computation-specific
    implementations derive (such as expressing operands like outcomes or histograms,
    unary operations, binary operations, pools, etc.). In most cases, details of those
    implementations can be safely ignored.
    """

    # ---- Constructor -----------------------------------------------------------------

    @experimental
    def __init__(
        self,
        children: Iterable[R] = (),
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__()
        self._children = tuple(children)
        self._annotation = annotation
        # It is probably an abuse of lists to use them as pointers, but this allows
        # copies (e.g., made from R.annotate) to benefit from siblings' efforts
        self._cached_h: List[H] = []

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _children_repr() -> Iterator[str]:
            for child in self.children:
                yield indent(repr(child), "    ")

        children_repr = ",\n".join(_children_repr()).strip()
        children_repr = (
            "\n    " + children_repr + ",\n  " if children_repr else children_repr
        )

        return f"""{type(self).__name__}(
  children=({children_repr}),
  annotation={self.annotation!r},
)"""

    def __eq__(self, other) -> bool:
        if isinstance(other, R):
            return (
                (isinstance(self, type(other)) or isinstance(other, type(self)))
                and __eq__(self.children, other.children)
                and __eq__(self.annotation, other.annotation)
            )
        else:
            return super().__eq__(other)

    def __ne__(self, other) -> bool:
        if isinstance(other, R):
            return not __eq__(self, other)
        else:
            return super().__ne__(other)

    def __len__(self) -> int:
        return len(self.children)

    @overload
    def __getitem__(self, key: IndexT) -> R:
        ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[R, ...]:
        ...

    def __getitem__(self, key: _GetItemT) -> Union[R, Tuple[R, ...]]:
        if isinstance(key, slice):
            return self.children[key]
        else:
            return self.children[__index__(key)]

    def __add__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    def __radd__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    def __sub__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    def __rsub__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    def __mul__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    def __rmul__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    def __matmul__(self, other: IntT) -> R:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return RepeatRoller(other, self)

    def __rmatmul__(self, other: IntT) -> R:
        return self.__matmul__(other)

    def __truediv__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    def __rtruediv__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    def __floordiv__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    def __rfloordiv__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    def __mod__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    def __rmod__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    def __pow__(self, other: _OperandT) -> BinaryOperationRoller:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    def __rpow__(self, other: OutcomeT) -> BinaryOperationRoller:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    def __and__(self, other: Union[R, IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__and__, other)
            else:
                return self.map(__and__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    def __rand__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __and__)
        except NotImplementedError:
            return NotImplemented

    def __xor__(self, other: Union[R, IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__xor__, other)
            else:
                return self.map(__xor__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    def __rxor__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __xor__)
        except NotImplementedError:
            return NotImplemented

    def __or__(self, other: Union[R, IntT]) -> BinaryOperationRoller:
        try:
            if isinstance(other, R):
                return self.map(__or__, other)
            else:
                return self.map(__or__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    def __ror__(self, other: IntT) -> BinaryOperationRoller:
        try:
            return self.rmap(as_int(other), __or__)
        except NotImplementedError:
            return NotImplemented

    def __neg__(self) -> UnaryOperationRoller:
        return self.umap(__neg__)

    def __pos__(self) -> UnaryOperationRoller:
        return self.umap(__pos__)

    def __abs__(self) -> UnaryOperationRoller:
        return self.umap(__abs__)

    def __invert__(self) -> UnaryOperationRoller:
        return self.umap(__invert__)

    def h(self) -> H:
        r"""
        Implements the [``HAbleT`` protocol][dyce.h.HAbleT]. This method calls the abstract
        ``_h`` method and caches (memoizes) the result to avoid potentially intensive,
        redundant computation. Derived classes wishing to preserve this behavior should
        override the ``_h`` method instead of this one.

        Internally, this method should only ever be called from ``_h`` method
        implementations.
        """
        if not self._cached_h:
            self._cached_h.append(self._h())

        return self._cached_h[0]

    @abstractmethod
    def roll(self) -> Roll:
        r"""
        Sub-classes should implement this to return a new [``Roll`` object][dyce.r.Roll]
        appropriate for a particular node (taking into account any children).
        """
        raise NotImplementedError

    def _h(self) -> H:
        r"""
        Sub-clases should implement this to return an [``H`` object][dyce.h.H] reflective of
        a particular node (taking into account any children). This method should only
        ever be called from the [``h`` method][dyce.r.R.h].

        The default implementation for this method is to raise a
        ``NotImplementedError``. This is by design. Not all rollers can efficiently
        compute their own histograms, even if their children can. If you want to
        implement rollers and don’t need this functionality, you can safely ignore it.
        """
        raise NotImplementedError

    # ---- Properties ------------------------------------------------------------------

    @property
    def annotation(self) -> Any:
        r"""
        Any provided annotation.
        """
        return self._annotation

    @property
    def children(self) -> Tuple[R, ...]:
        r"""
        The roller’s direct child nodes (if any).
        """
        return self._children

    # ---- Methods ---------------------------------------------------------------------

    @classmethod
    def from_value(
        cls,
        value: _ValueT,
        annotation: Any = None,
    ) -> ValueRoller:
        r"""
        Creates and returns a roller without any children for representing a single *value*
        (i.e., scalar or histogram).

        ```python
        >>> R.from_value(6)
        ValueRoller(value=6, annotation=None)
        >>> R.from_value(H(6))
        ValueRoller(value=H(6), annotation=None)

        ```
        """
        return ValueRoller(value, annotation=annotation)

    @classmethod
    def from_values(
        cls,
        *values: _ValueT,
        annotation: Any = None,
    ) -> PoolRoller:
        r"""
        Shorthand for ``cls.from_values_iterable(values, annotation=annotation)``.

        See the [``from_values_iterable`` method][dyce.r.R.from_values_iterable].
        """
        return cls.from_values_iterable(values, annotation=annotation)

    @classmethod
    def from_values_iterable(
        cls,
        values: Iterable[_ValueT],
        annotation: Any = None,
    ) -> PoolRoller:
        r"""
        Shorthand for ``cls.from_rs_iterable((cls.from_value(value) for value in values),
        annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``from_rs_iterable``][dyce.r.R.from_rs_iterable] methods.
        """
        return cls.from_rs_iterable(
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @classmethod
    def from_rs(
        cls,
        *children: R,
        annotation: Any = None,
    ) -> PoolRoller:
        r"""
        Shorthand for ``cls.from_rs_iterable(rs, annotation=annotation)``.

        See the [``from_rs_iterable`` method][dyce.r.R.from_rs_iterable].
        """
        return cls.from_rs_iterable(children, annotation=annotation)

    @classmethod
    def from_rs_iterable(
        cls,
        children: Iterable[R],
        annotation: Any = None,
    ) -> PoolRoller:
        r"""
        Creates and returns a roller for “pooling” zero or more *children*. The returned
        roller will generate rolls whose items will contain one value for each child:

        ```python
        >>> r_pool = R.from_rs_iterable(R.from_value(h) for h in (H((1, 2)), H((3, 4)), H((5, 6))))
        >>> r_pool.roll()  # doctest: +SKIP
        Roll(
          r=PoolRoller(
            children=(
              ValueRoller(value=H({1: 1, 2: 1}), annotation=None),
              ValueRoller(value=H({3: 1, 4: 1}), annotation=None),
              ValueRoller(value=H({5: 1, 6: 1}), annotation=None),
            ),
            annotation=None,
          ),
          items=(
            ((2,), (
              Roll(
                r=ValueRoller(value=H({1: 1, 2: 1}), annotation=None),
                items=(
                  ((2,), ()),
                ),
              ),
            )),
            ((4,), (
              Roll(
                r=ValueRoller(value=H({3: 1, 4: 1}), annotation=None),
                items=(
                  ((4,), ()),
                ),
              ),
            )),
            ((6,), (
              Roll(
                r=ValueRoller(value=H({5: 1, 6: 1}), annotation=None),
                items=(
                  ((6,), ()),
                ),
              ),
            )),
          ),
        )

        ```
        """
        return PoolRoller(children, annotation=annotation)

    def map(
        self,
        op: _BinaryOperatorT,
        right_operand: _OperandT,
        annotation: Any = None,
    ) -> BinaryOperationRoller:
        r"""
        Creates and returns a parent roller for applying binary operator *op* to this roller
        and *right_operand*.

        ```python
        >>> import operator
        >>> r_binop = R.from_value(H(6)).map(operator.__pow__, 2) ; r_binop
        BinaryOperationRoller(
          op=<built-in function pow>,
          left_child=ValueRoller(value=H(6), annotation=None),
          right_child=ValueRoller(value=2, annotation=None),
          annotation=None,
        )
        >>> r_binop.h()
        H({1: 1, 4: 1, 9: 1, 16: 1, 25: 1, 36: 1})

        ```
        """
        if isinstance(right_operand, _OutcomeCs):
            right_operand = ValueRoller(right_operand)

        if isinstance(right_operand, R):
            return BinaryOperationRoller(op, self, right_operand, annotation=annotation)
        else:
            raise NotImplementedError

    def rmap(
        self,
        left_operand: OutcomeT,
        op: _BinaryOperatorT,
        annotation: Any = None,
    ) -> BinaryOperationRoller:
        r"""
        Analogous to the [``map`` method][dyce.r.R.map], but where the caller supplies
        *left_operand*:

        ```python
        >>> import operator
        >>> r_binop = R.from_value(H(6)).rmap(2, operator.__pow__) ; r_binop
        BinaryOperationRoller(
          op=<built-in function pow>,
          left_child=ValueRoller(value=2, annotation=None),
          right_child=ValueRoller(value=H(6), annotation=None),
          annotation=None,
        )
        >>> r_binop.h()
        H({2: 1, 4: 1, 8: 1, 16: 1, 32: 1, 64: 1})

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

    def umap(
        self,
        op: _UnaryOperatorT,
        annotation: Any = None,
    ) -> UnaryOperationRoller:
        r"""
        Creates and returns a parent roller for applying unary operator *op* to this roller.

        ```python
        >>> import operator
        >>> r_unop = R.from_value(H(6)).umap(operator.__neg__) ; r_unop
        UnaryOperationRoller(
          op=<built-in function neg>,
          child=ValueRoller(value=H(6), annotation=None),
          annotation=None,
        )
        >>> r_unop.h()
        H(-6)

        ```
        """
        return UnaryOperationRoller(op, self, annotation=annotation)

    def lt(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.lt(right) if isinstance(left, H)
        else right.ge(left) if isisntance(right, H) else bool(__lt__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_lt(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.lt(right)
            elif isinstance(right, H):
                return right.gt(left)
            else:
                return bool(__lt__(left, right))

        return self.map(_is_lt, other)

    def le(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.le(right) if isinstance(left, H)
        else right.gt(left) if isisntance(right, H) else bool(__le__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_le(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.le(right)
            elif isinstance(right, H):
                return right.gt(left)
            else:
                return bool(__le__(left, right))

        return self.map(_is_le, other)

    def eq(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.eq(right) if isinstance(left, H)
        else right.eq(left) if isisntance(right, H) else bool(__eq__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_eq(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.eq(right)
            elif isinstance(right, H):
                return right.eq(left)
            else:
                return bool(__eq__(left, right))

        return self.map(_is_eq, other)

    def ne(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.ne(right) if isinstance(left, H)
        else right.ne(left) if isisntance(right, H) else bool(__ne__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_ne(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.ne(right)
            elif isinstance(right, H):
                return right.ne(left)
            else:
                return bool(__ne__(left, right))

        return self.map(_is_ne, other)

    def gt(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.gt(right) if isinstance(left, H)
        else right.le(left) if isisntance(right, H) else bool(__gt__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_gt(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.gt(right)
            elif isinstance(right, H):
                return right.le(left)
            else:
                return bool(__gt__(left, right))

        return self.map(_is_gt, other)

    def ge(
        self,
        other: _OperandT,
    ) -> BinaryOperationRoller:
        r"""
        Shorthand for ``self.map(lambda left, right: left.ge(right) if isinstance(left, H)
        else right.lt(left) if isisntance(right, H) else bool(__ge__(left, right)),
        other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _is_ge(
            left: Union[OutcomeT, H], right: Union[OutcomeT, H]
        ) -> Union[bool, H]:
            if isinstance(left, H):
                return left.ge(right)
            elif isinstance(right, H):
                return right.lt(left)
            else:
                return bool(__ge__(left, right))

        return self.map(_is_ge, other)

    def is_even(self) -> UnaryOperationRoller:
        r"""
        Shorthand for: ``self.umap(lambda x: x.is_even() if isinstance(x, H) else as_int(x)
        % 2 == 0)``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_even(operand: Union[IntT, H]) -> Union[bool, H]:
            if isinstance(operand, H):
                return operand.is_even()
            else:
                return __mod__(as_int(operand), 2) == 0

        return self.umap(_is_even)

    def is_odd(self) -> UnaryOperationRoller:
        r"""
        Shorthand for: ``self.umap(lambda x: x.is_odd() if isinstance(x, H) else as_int(x) %
        2 != 0)``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_odd(operand: Union[IntT, H]) -> Union[bool, H]:
            if isinstance(operand, H):
                return operand.is_odd()
            else:
                return __mod__(as_int(operand), 2) != 0

        return self.umap(_is_odd)

    def annotate(self, annotation: Any = None) -> R:
        r"""
        Generates a copy of the roller with the desired annotation.

        ```python
        >>> r_just_the_n_of_us = R.from_value(5, annotation="But I'm 42!") ; r_just_the_n_of_us
        ValueRoller(value=5, annotation="But I'm 42!")
        >>> r_just_the_n_of_us.annotate("I'm a 42-year-old investment banker!")
        ValueRoller(value=5, annotation="I'm a 42-year-old investment banker!")

        ```
        """
        r = copy(self)
        r._annotation = annotation

        return r


class ValueRoller(R):
    r"""
    A roller without any children for representing a single *value* (i.e., a single
    outcome or a histogram).
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(
        self,
        value: _ValueT,
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__((), annotation)
        self._value = value

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"""{type(self).__name__}(value={self.value!r}, annotation={self.annotation!r})"""

    def roll(self) -> Roll:
        if isinstance(self.value, P):
            return Roll(self, items=((self.value.roll(), ()),))
        elif isinstance(self.value, H):
            return Roll(self, items=(((self.value.roll(),), ()),))
        elif isinstance(self.value, _OutcomeCs):
            return Roll(self, items=(((self.value,), ()),))

    def _h(self) -> H:
        if isinstance(self.value, P):
            return self.value.h()
        elif isinstance(self.value, H):
            return self.value
        elif isinstance(self.value, _OutcomeCs):
            return H({self.value: 1})

    # ---- Properties ------------------------------------------------------------------

    @property
    def value(self) -> _ValueT:
        r"""
        The single value for this leaf node roller.
        """
        return self._value


class BinaryOperationRoller(R):
    r"""
    A roller for applying a binary operator *op* to the Cartesian product of all
    outcomes from its *left_child* and all outcomes from its *right_child*.
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(
        self,
        op: _BinaryOperatorT,
        left_child: R,
        right_child: R,
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__((left_child, right_child), annotation)
        self._operator = op

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _child_repr(child: R) -> str:
            return indent(repr(child), "    ").strip()

        left_child, right_child = self.children

        return f"""{type(self).__name__}(
  op={self.operator!r},
  left_child={_child_repr(left_child)},
  right_child={_child_repr(right_child)},
  annotation={self.annotation!r},
)"""

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.operator == other.operator

    def roll(self) -> Roll:
        left_child, right_child = self.children
        left_roll = left_child.roll()
        right_roll = right_child.roll()

        return Roll(
            self,
            items=(
                (
                    tuple(
                        self.operator(left_outcome, right_outcome)
                        for left_outcome in left_roll.outcomes()
                        for right_outcome in right_roll.outcomes()
                    ),
                    (left_roll, right_roll),
                ),
            ),
        )

    def _h(self) -> H:
        left_child, right_child = self.children

        return self.operator(left_child.h(), right_child.h())

    # ---- Properties ------------------------------------------------------------------

    @property
    def operator(self) -> _BinaryOperatorT:
        r"""
        The binary operator this roller applies to its children.
        """
        return self._operator


class UnaryOperationRoller(R):
    r"""
    A roller for applying a unary operator *op* to each outcome from its sole *child*.
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(
        self,
        op: _UnaryOperatorT,
        child: R,
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__((child,), annotation)
        self._operator = op

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _child_repr(child: R) -> str:
            return indent(repr(child), "  ").strip()

        (child,) = self.children

        return f"""{type(self).__name__}(
  op={self.operator!r},
  child={_child_repr(child)},
  annotation={self.annotation!r},
)"""

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.operator == other.operator

    def roll(self) -> Roll:
        (child,) = self.children
        child_roll = child.roll()

        return Roll(
            self,
            items=(
                (
                    tuple(self.operator(outcome) for outcome in child_roll.outcomes()),
                    (child_roll,),
                ),
            ),
        )

    def _h(self) -> H:
        (child,) = self.children

        return self.operator(child.h())

    # ---- Properties ------------------------------------------------------------------

    @property
    def operator(self) -> _UnaryOperatorT:
        r"""
        The unary operator this roller applies to each outcome of its sole child.
        """
        return self._operator


class RepeatRoller(R):
    r"""
    Roller to implement the ``__matmul__`` operator. It is akin to a homogeneous
    ``PoolRoller`` containing *n* copies of its sole *child*.

    ```python
    >>> r_d6 = R.from_value(H(6))
    >>> 1000 @ r_d6
    RepeatRoller(
      n=1000,
      child=ValueRoller(value=H(6), annotation=None),
      annotation=None,
    )

    ```
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(
        self,
        n: IntT,
        child: R,
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__((child,), annotation)
        self._n = as_int(n)

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _child_repr(child: R) -> str:
            return indent(repr(child), "  ").strip()

        (child,) = self.children

        return f"""{type(self).__name__}(
  n={self.n!r},
  child={_child_repr(child)},
  annotation={self.annotation!r},
)"""

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.n == other.n

    def roll(self) -> Roll:
        def _items() -> Iterator[_RollItemT]:
            (child,) = self.children

            for _ in range(self.n):
                child_roll = child.roll()
                yield (tuple(child_roll.outcomes()), (child_roll,))

        return Roll(self, items=_items())

    def _h(self) -> H:
        (child,) = self.children

        return self.n @ child.h()

    # ---- Properties ------------------------------------------------------------------

    @property
    def n(self) -> int:
        r"""
        The number of times to “repeat” the roller’s sole child.
        """
        return self._n


class PoolRoller(R):
    r"""
    A roller for “pooling” zero or more *children* rollers.
    """

    # ---- Constructor -----------------------------------------------------------------

    def __init__(
        self,
        children: Iterable[R] = (),
        annotation: Any = None,
    ):
        r"Initializer."
        super().__init__(children, annotation)

    # ---- Overrides -------------------------------------------------------------------

    def roll(self) -> Roll:
        def _items() -> Iterator[_RollItemT]:
            for child in self._children:
                child_roll = child.roll()
                yield (tuple(child_roll.outcomes()), (child_roll,))

        return Roll(self, items=_items())

    def _h(self) -> H:
        return sum_w_start((child.h() for child in self.children), start=H({}))


class Roll(Sequence[_RollItemT]):
    r"""
    !!! warning "Experimental"

        This class should be considered experimental and may change or disappear in
        future versions.

    An immutable roll result (or “roll” for short). More specifically, the result of
    calling the [``R.roll`` method][dyce.r.R.roll]. Rolls have their own tree-like
    structures that mirror the roller trees that generated them.
    """

    # ---- Constructor -----------------------------------------------------------------

    @experimental
    def __init__(
        self,
        r: R,
        items: Iterable[_RollItemT],
    ):
        r"Initializer."
        super().__init__()
        self._r = r
        self._items = tuple(items)
        self._total = sum(self.outcomes())

    # ---- Overrides -------------------------------------------------------------------

    def __repr__(self) -> str:
        def _r_repr(r: R) -> str:
            return indent(repr(r), "  ").strip()

        def _rolls_repr(rolls: Iterable[Roll]) -> Iterator[str]:
            for roll in rolls:
                yield indent(repr(roll), "  ")

        def _items_repr(items: Iterable[_RollItemT]) -> Iterator[str]:
            for outcome, rolls in self:
                rolls_repr = ",\n".join(_rolls_repr(rolls)).strip()
                rolls_repr = "\n  " + rolls_repr + ",\n" if rolls_repr else rolls_repr
                yield indent(f"({outcome!r}, ({rolls_repr}))", "    ")

        items_repr = ",\n".join(_items_repr(self)).strip()
        items_repr = "\n    " + items_repr + ",\n  " if items_repr else items_repr

        return f"""{type(self).__name__}(
  r={_r_repr(self.r)},
  items=({items_repr}),
)"""

    def __len__(self) -> int:
        return len(self._items)

    @overload
    def __getitem__(self, key: IndexT) -> _RollItemT:
        ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[_RollItemT, ...]:
        ...

    def __getitem__(self, key: _GetItemT) -> Union[_RollItemT, Tuple[_RollItemT, ...]]:
        if isinstance(key, slice):
            return self._items[key]
        else:
            return self._items[__index__(key)]

    def __iter__(self) -> Iterator[_RollItemT]:
        return iter(self._items)

    # ---- Methods ---------------------------------------------------------------------

    def outcomes(self) -> Iterator[OutcomeT]:
        r"""
        Shorthand for ``chain.from_iterable(outcomes for (outcomes, _) in self)``.

        !!! tip

            Unlike [``H.roll``][dyce.h.H.roll] and [``P.roll``][dyce.p.P.roll], these
            outcomes are *not* sorted. Instead, they retain the ordering from whence
            they came in the roller tree:

            ```python
            >>> r_3d6 = 3 @ R.from_value(H(6))
            >>> r_3d6_neg = 3 @ -R.from_value(H(6))
            >>> roll = R.from_rs(r_3d6, r_3d6_neg).roll()
            >>> tuple(roll.outcomes())  # doctest: +SKIP
            (1, 4, 1, -5, -2, -3)
            >>> len(roll)
            2
            >>> [outcomes for outcomes, _ in roll]  # doctest: +SKIP
            [(1, 4, 1), (-5, -2, -3)]
            >>> [roll.r for roll in roll.rolls()] == [r_3d6, r_3d6_neg]
            True

            ```
        """
        return chain.from_iterable(outcomes for (outcomes, _) in self)

    def rolls(self) -> Iterator[Roll]:
        r"""
        Shorthand for ``chain.from_iterable(rolls for (_, rolls) in self)``.

        TODO
        """
        return chain.from_iterable(rolls for (_, rolls) in self)

    # ---- Properties ------------------------------------------------------------------

    @property
    def r(self) -> R:
        r"""
        The roller from whence the roll was generated.
        """
        return self._r

    @property
    def total(self) -> OutcomeT:
        r"""
        Equivalent to ``sum(self.outcomes())``, but calculated once in
        [``Roll.__init__``][dyce.r.Roll.__init__].
        """
        return self._total

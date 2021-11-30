# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import enum
import warnings
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
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    overload,
)

from numerary import RealLike
from numerary.bt import beartype
from numerary.types import SupportsIndex, SupportsInt

from .h import H
from .lifecycle import experimental
from .p import P
from .types import (
    _BinaryOperatorT,
    _GetItemT,
    _UnaryOperatorT,
    as_int,
    getitems,
    is_even,
    is_odd,
)

__all__ = ("R",)


# ---- Types ---------------------------------------------------------------------------


_ValueT = Union[RealLike, H, P]
_SourceT = Union["R"]
_ROperandT = Union[RealLike, _SourceT]
_RollOutcomeOperandT = Union[RealLike, "RollOutcome"]
_RollOutcomesReturnT = Union["RollOutcome", Iterable["RollOutcome"]]
_RollOutcomeUnaryOperatorT = Callable[["RollOutcome"], _RollOutcomesReturnT]
_RollOutcomeBinaryOperatorT = Callable[
    ["RollOutcome", "RollOutcome"], _RollOutcomesReturnT
]
BasicOperatorT = Callable[["R", Iterable["RollOutcome"]], _RollOutcomesReturnT]
_ExpansionOperatorT = Callable[["RollOutcome"], Union["RollOutcome", "Roll"]]
_PredicateT = Callable[["RollOutcome"], bool]


class CoalesceMode(enum.Enum):
    REPLACE = enum.auto()
    APPEND = enum.auto()


# ---- Classes -------------------------------------------------------------------------


class R:
    r"""
    !!! warning "Experimental"

        This class (and its descendants) should be considered experimental and may
        change or disappear in future versions.

    Where [``H`` objects][dyce.h.H] and [``P`` objects][dyce.p.P] are used primarily for
    enumerating weighted outcomes, ``#!python R`` objects represent rollers. More
    specifically, they are immutable nodes assembled in tree-like structures to
    represent calculations. Unlike [``H``][dyce.h.H] or [``P``][dyce.p.P] objects,
    rollers generate rolls that conform to weighted outcomes without engaging in
    computationally expensive enumeration. Roller trees are typically composed from
    various ``#!python R`` class methods and operators as well as arithmetic operations.

    ``` python
    >>> from dyce import H, P, R
    >>> d6 = H(6)
    >>> r_d6 = R.from_value(d6) ; r_d6
    ValueRoller(value=H(6), annotation='')
    >>> ((4 * r_d6 + 3) ** 2 % 5).gt(2)
    BinarySumOpRoller(
      bin_op=<function R.gt.<locals>._gt at ...>,
      left_source=BinarySumOpRoller(
          bin_op=<built-in function mod>,
          left_source=BinarySumOpRoller(
              bin_op=<built-in function pow>,
              left_source=BinarySumOpRoller(
                  bin_op=<built-in function add>,
                  left_source=BinarySumOpRoller(
                      bin_op=<built-in function mul>,
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
        >>> r_6_abs_3 = 3@abs(r_6)
        >>> r_6_abs_6_abs_6_abs = R.from_sources(abs(r_6), abs(r_6), abs(r_6))
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

    <!-- BEGIN MONKEY PATCH --
    For deterministic outcomes.

    >>> import random
    >>> from dyce import rng
    >>> rng.RNG = random.Random(1633056380)

      -- END MONKEY PATCH -->

    ``` python
    >>> roll = r_d6.roll()
    >>> tuple(roll.outcomes())
    (4,)
    >>> roll.total()
    4

    ```

    ``` python
    >>> d6 + 3
    H({4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1})
    >>> (r_d6 + 3).roll().total() in (d6 + 3)
    True

    ```

    [``Roll`` objects][dyce.r.Roll] are much richer than mere sequences of outcomes.
    They are also tree-like structures that mirror the roller trees used to produce
    them, capturing references to rollers and the outcomes generated at each node.

    ``` python
    >>> roll = (r_d6 + 3).roll()
    >>> roll.total()
    8
    >>> roll
    Roll(
      r=...,
      roll_outcomes=(
        RollOutcome(
          value=8,
          sources=(
            RollOutcome(
              value=5,
              sources=(),
            ),
            RollOutcome(
              value=3,
              sources=(),
            ),
          ),
        ),
      ),
      source_rolls=(
        Roll(
          r=ValueRoller(value=H(6), annotation=''),
          roll_outcomes=(
            RollOutcome(
              value=5,
              sources=(),
            ),
          ),
          source_rolls=(),
        ),
        Roll(
          r=ValueRoller(value=3, annotation=''),
          roll_outcomes=(
            RollOutcome(
              value=3,
              sources=(),
            ),
          ),
          source_rolls=(),
        ),
      ),
    )

    ```

    Rollers afford optional annotations as a convenience to callers. They are taken into
    account when comparing roller trees, but otherwise ignored, internally. One use is
    to capture references to nodes in an abstract syntax tree generated from parsing a
    proprietary grammar. Any provided *annotation* can be retrieved using the
    [``annotation`` property][dyce.r.R.annotation]. The
    [``annotate`` method][dyce.r.R.annotate] can be used to apply an annotation to
    existing roller.

    The ``#!python R`` class itself acts as a base from which several
    computation-specific implementations derive (such as expressing operands like
    outcomes or histograms, unary operations, binary operations, pools, etc.).

    <!-- BEGIN MONKEY PATCH --
    For type-checking docstrings

    >>> from typing import Tuple, Union
    >>> from dyce.r import PoolRoller, Roll, RollOutcome, ValueRoller
    >>> which: Tuple[Union[int, slice], ...]

      -- END MONKEY PATCH -->
    """
    __slots__: Union[str, Iterable[str]] = ("_annotation", "_sources")

    # ---- Initializer -----------------------------------------------------------------

    @experimental
    @beartype
    def __init__(
        self,
        sources: Iterable[_SourceT] = (),
        annotation: Any = "",
        **kw,
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
                and __eq__(self.sources, other.sources)  # order matters
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
    def __add__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __add__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __sub__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__sub__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rsub__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __sub__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mul__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__mul__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmul__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __mul__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __matmul__(self, other: SupportsInt) -> R:
        try:
            other = as_int(other)
        except TypeError:
            return NotImplemented

        if other < 0:
            raise ValueError("argument cannot be negative")
        else:
            return RepeatRoller(other, self)

    @beartype
    def __rmatmul__(self, other: SupportsInt) -> R:
        return self.__matmul__(other)

    @beartype
    def __truediv__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__truediv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rtruediv__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __truediv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __floordiv__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__floordiv__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rfloordiv__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __floordiv__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __mod__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__mod__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rmod__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __mod__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __pow__(self, other: _ROperandT) -> BinarySumOpRoller:
        try:
            return self.map(__pow__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rpow__(self, other: RealLike) -> BinarySumOpRoller:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __and__(self, other: Union[_SourceT, SupportsInt]) -> BinarySumOpRoller:
        try:
            if isinstance(other, R):
                return self.map(__and__, other)
            else:
                return self.map(__and__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rand__(self, other: SupportsInt) -> BinarySumOpRoller:
        try:
            return self.rmap(as_int(other), __and__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __xor__(self, other: Union[_SourceT, SupportsInt]) -> BinarySumOpRoller:
        try:
            if isinstance(other, R):
                return self.map(__xor__, other)
            else:
                return self.map(__xor__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __rxor__(self, other: SupportsInt) -> BinarySumOpRoller:
        try:
            return self.rmap(as_int(other), __xor__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __or__(self, other: Union[_SourceT, SupportsInt]) -> BinarySumOpRoller:
        try:
            if isinstance(other, R):
                return self.map(__or__, other)
            else:
                return self.map(__or__, as_int(other))
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __ror__(self, other: SupportsInt) -> BinarySumOpRoller:
        try:
            return self.rmap(as_int(other), __or__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __neg__(self) -> UnarySumOpRoller:
        return self.umap(__neg__)

    @beartype
    def __pos__(self) -> UnarySumOpRoller:
        return self.umap(__pos__)

    @beartype
    def __abs__(self) -> UnarySumOpRoller:
        return self.umap(__abs__)

    @beartype
    def __invert__(self) -> UnarySumOpRoller:
        return self.umap(__invert__)

    @abstractmethod
    def roll(self) -> Roll:
        r"""
        Sub-classes should implement this method to return a new
        [``Roll`` object][dyce.r.Roll] taking into account any
        [sources][dyce.r.R.sources].

        !!! note

            Implementors guarantee that all [``RollOutcome``][dyce.r.RollOutcome]s in
            the returned [``Roll``][dyce.r.Roll] *must* be associated with a roll,
            *including all roll outcomes’ [``sources``][dyce.r.RollOutcome.sources]*.

        <!-- BEGIN MONKEY PATCH --
        For deterministic outcomes.

        >>> import random
        >>> from dyce import rng
        >>> rng.RNG = random.Random(1633403927)

          -- END MONKEY PATCH -->

        !!! tip

            Show that roll outcomes from source rolls are excluded by creating a new
            roll outcome with a value of ``#!python None`` with the excluded roll
            outcome as its source. The
            [``RollOutcome.euthanize``][dyce.r.RollOutcome.euthanize] convenience method
            is provided for this purpose.

            See the section on “[Dropping dice from prior rolls
            …](rollin.md#dropping-dice-from-prior-rolls-keeping-the-best-three-of-3d6-and-1d8)”
            as well as the note in [``Roll.__init__``][dyce.r.Roll.__init__] for
            additional color.

            ``` python
            >>> from itertools import chain
            >>> class AntonChigurhRoller(R):
            ...   h_coin_toss = H((0, 1))
            ...   def roll(self) -> Roll:
            ...     source_rolls = list(self.source_rolls())
            ...     def _roll_outcomes_gen():
            ...       for roll_outcome in chain.from_iterable(source_rolls):
            ...         if roll_outcome.value is None:
            ...           # Omit those already deceased
            ...           continue
            ...         elif self.h_coin_toss.roll():
            ...           # This one lives. Wrap the old outcome in a new one with the same value.
            ...           yield roll_outcome
            ...         else:
            ...           # This one dies here. Wrap the old outcome in a new one with a value of None.
            ...           yield roll_outcome.euthanize()
            ...     return Roll(self, roll_outcomes=_roll_outcomes_gen(), source_rolls=source_rolls)
            >>> ac_r = AntonChigurhRoller(sources=(R.from_value(1), R.from_value(2), R.from_value(3)))
            >>> ac_r.roll()
            Roll(
              r=AntonChigurhRoller(
                sources=(
                  ValueRoller(value=1, annotation=''),
                  ValueRoller(value=2, annotation=''),
                  ValueRoller(value=3, annotation=''),
                ),
                annotation='',
              ),
              roll_outcomes=(
                RollOutcome(
                  value=None,
                  sources=(
                    RollOutcome(
                      value=1,
                      sources=(),
                    ),
                  ),
                ),
                RollOutcome(
                  value=2,
                  sources=(),
                ),
                RollOutcome(
                  value=3,
                  sources=(),
                ),
              ),
              source_rolls=(
                Roll(
                  r=ValueRoller(value=1, annotation=''),
                  roll_outcomes=(
                    RollOutcome(
                      value=1,
                      sources=(),
                    ),
                  ),
                  source_rolls=(),
                ),
                Roll(
                  r=ValueRoller(value=2, annotation=''),
                  roll_outcomes=(
                    RollOutcome(
                      value=2,
                      sources=(),
                    ),
                  ),
                  source_rolls=(),
                ),
                Roll(
                  r=ValueRoller(value=3, annotation=''),
                  roll_outcomes=(
                    RollOutcome(
                      value=3,
                      sources=(),
                    ),
                  ),
                  source_rolls=(),
                ),
              ),
            )

            ```
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
    def sources(self) -> Tuple[_SourceT, ...]:
        r"""
        The roller’s direct sources (if any).
        """
        return self._sources

    # ---- Methods ---------------------------------------------------------------------

    @classmethod
    @beartype
    def from_sources(
        cls,
        *sources: _SourceT,
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Shorthand for ``#!python cls.from_sources_iterable(rs, annotation=annotation)``.

        See the [``from_sources_iterable`` method][dyce.r.R.from_sources_iterable].
        """
        return cls.from_sources_iterable(sources, annotation=annotation)

    @classmethod
    @beartype
    def from_sources_iterable(
        cls,
        sources: Iterable[_SourceT],
        annotation: Any = "",
    ) -> PoolRoller:
        r"""
        Creates and returns a roller for “pooling” zero or more *sources*.

        <!-- BEGIN MONKEY PATCH --
        For deterministic outcomes.

        >>> import random
        >>> from dyce import rng
        >>> rng.RNG = random.Random(1633056341)

          -- END MONKEY PATCH -->

        ``` python
        >>> r_pool = R.from_sources_iterable(R.from_value(h) for h in (H((1, 2)), H((3, 4)), H((5, 6))))
        >>> roll = r_pool.roll()
        >>> tuple(roll.outcomes())
        (2, 4, 6)
        >>> roll
        Roll(
          r=...,
          roll_outcomes=(
            RollOutcome(
              value=2,
              sources=(),
            ),
            RollOutcome(
              value=4,
              sources=(),
            ),
            RollOutcome(
              value=6,
              sources=(),
            ),
          ),
          source_rolls=...,
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
        Creates and returns a [``ValueRoller``][dyce.r.ValueRoller] from *value*.

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
        Shorthand for ``#!python cls.from_sources_iterable((cls.from_value(value) for value
        in values), annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``from_sources_iterable``][dyce.r.R.from_sources_iterable] methods.
        """
        return cls.from_sources_iterable(
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @classmethod
    @beartype
    def filter_from_sources(
        cls,
        predicate: _PredicateT,
        *sources: _SourceT,
        annotation: Any = "",
    ) -> FilterRoller:
        r"""
        Shorthand for ``#!python cls.filter_from_sources_iterable(predicate, sources,
        annotation=annotation)``.

        See the [``filter_from_sources_iterable``
        method][dyce.r.R.filter_from_sources_iterable].
        """
        return cls.filter_from_sources_iterable(
            predicate, sources, annotation=annotation
        )

    @classmethod
    @beartype
    def filter_from_sources_iterable(
        cls,
        predicate: _PredicateT,
        sources: Iterable[_SourceT],
        annotation: Any = "",
    ) -> FilterRoller:
        r"""
        Creates and returns a [``FilterRoller``][dyce.r.FilterRoller] for applying filterion
        *predicate* to sorted outcomes from *sources*.

        ``` python
        >>> r_filter = R.filter_from_sources_iterable(
        ...   lambda outcome: bool(outcome.is_even().value),
        ...   (R.from_value(i) for i in (5, 4, 6, 3, 7, 2, 8, 1, 9, 0)),
        ... ) ; r_filter
        FilterRoller(
          predicate=<function <lambda> at ...>,
          sources=(
            ValueRoller(value=5, annotation=''),
            ValueRoller(value=4, annotation=''),
            ...,
            ValueRoller(value=9, annotation=''),
            ValueRoller(value=0, annotation=''),
          ),
          annotation='',
        )
        >>> tuple(r_filter.roll().outcomes())
        (4, 6, 2, 8, 0)

        ```
        """
        return FilterRoller(predicate, sources, annotation=annotation)

    @classmethod
    @beartype
    def filter_from_values(
        cls,
        predicate: _PredicateT,
        *values: _ValueT,
        annotation: Any = "",
    ) -> FilterRoller:
        r"""
        Shorthand for ``#!python cls.filter_from_values_iterable(predicate, values,
        annotation=annotation)``.

        See the
        [``filter_from_values_iterable`` method][dyce.r.R.filter_from_values_iterable].
        """
        return cls.filter_from_values_iterable(predicate, values, annotation=annotation)

    @classmethod
    @beartype
    def filter_from_values_iterable(
        cls,
        predicate: _PredicateT,
        values: Iterable[_ValueT],
        annotation: Any = "",
    ) -> FilterRoller:
        r"""
        Shorthand for ``#!python cls.filter_from_sources_iterable((cls.from_value(value) for
        value in values), annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``filter_from_sources_iterable``][dyce.r.R.filter_from_sources_iterable]
        methods.
        """
        return cls.filter_from_sources_iterable(
            predicate,
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @classmethod
    @beartype
    def select_from_sources(
        cls,
        which: Iterable[_GetItemT],
        *sources: _SourceT,
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Shorthand for ``#!python cls.select_from_sources_iterable(which, sources,
        annotation=annotation)``.

        See the [``select_from_sources_iterable``
        method][dyce.r.R.select_from_sources_iterable].
        """
        return cls.select_from_sources_iterable(which, sources, annotation=annotation)

    @classmethod
    @beartype
    def select_from_sources_iterable(
        cls,
        which: Iterable[_GetItemT],
        sources: Iterable[_SourceT],
        annotation: Any = "",
    ) -> SelectionRoller:
        r"""
        Creates and returns a [``SelectionRoller``][dyce.r.SelectionRoller] for applying
        selection *which* to sorted outcomes from *sources*.

        ``` python
        >>> r_select = R.select_from_sources_iterable(
        ...   (0, -1, slice(3, 6), slice(6, 3, -1), -1, 0),
        ...   (R.from_value(i) for i in (5, 4, 6, 3, 7, 2, 8, 1, 9, 0)),
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
        Shorthand for ``#!python cls.select_from_values_iterable(which, values,
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
        Shorthand for ``#!python cls.select_from_sources_iterable((cls.from_value(value) for
        value in values), annotation=annotation)``.

        See the [``from_value``][dyce.r.R.from_value] and
        [``select_from_sources_iterable``][dyce.r.R.select_from_sources_iterable]
        methods.
        """
        return cls.select_from_sources_iterable(
            which,
            (cls.from_value(value) for value in values),
            annotation=annotation,
        )

    @beartype
    def source_rolls(self) -> Iterator["Roll"]:
        r"""
        Generates new rolls from all [``sources``][dyce.r.R.sources].
        """
        for source in self.sources:
            yield source.roll()

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
        bin_op: _RollOutcomeBinaryOperatorT,
        right_operand: _ROperandT,
        annotation: Any = "",
    ) -> BinarySumOpRoller:
        r"""
        Creates and returns a [``BinarySumOpRoller``][dyce.r.BinarySumOpRoller] for applying
        *bin_op* to this roller and *right_operand* as its sources. Shorthands exist for
        many arithmetic operators and comparators.

        ``` python
        >>> import operator
        >>> r_bin_op = R.from_value(H(6)).map(operator.__pow__, 2) ; r_bin_op
        BinarySumOpRoller(
          bin_op=<built-in function pow>,
          left_source=ValueRoller(value=H(6), annotation=''),
          right_source=ValueRoller(value=2, annotation=''),
          annotation='',
        )
        >>> r_bin_op == R.from_value(H(6)) ** 2
        True

        ```
        """
        if isinstance(right_operand, RealLike):
            right_operand = ValueRoller(right_operand)

        if isinstance(right_operand, (R, RollOutcome)):
            return BinarySumOpRoller(bin_op, self, right_operand, annotation=annotation)
        else:
            raise NotImplementedError

    @beartype
    def rmap(
        self,
        left_operand: Union[RealLike, "RollOutcome"],
        bin_op: _RollOutcomeBinaryOperatorT,
        annotation: Any = "",
    ) -> BinarySumOpRoller:
        r"""
        Analogous to the [``map`` method][dyce.r.R.map], but where the caller supplies
        *left_operand*.

        ``` python
        >>> import operator
        >>> r_bin_op = R.from_value(H(6)).rmap(2, operator.__pow__) ; r_bin_op
        BinarySumOpRoller(
          bin_op=<built-in function pow>,
          left_source=ValueRoller(value=2, annotation=''),
          right_source=ValueRoller(value=H(6), annotation=''),
          annotation='',
        )
        >>> r_bin_op == 2 ** R.from_value(H(6))
        True

        ```

        !!! note

            The positions of *left_operand* and *bin_op* are different from
            [``map`` method][dyce.r.R.map]. This is intentional and serves as a reminder
            of operand ordering.
        """
        if isinstance(left_operand, RealLike):
            return BinarySumOpRoller(
                bin_op, ValueRoller(left_operand), self, annotation=annotation
            )
        elif isinstance(left_operand, RollOutcome):
            return BinarySumOpRoller(bin_op, left_operand, self, annotation=annotation)
        else:
            raise NotImplementedError

    @beartype
    def umap(
        self,
        un_op: _RollOutcomeUnaryOperatorT,
        annotation: Any = "",
    ) -> UnarySumOpRoller:
        r"""
        Creates and returns a [``UnarySumOpRoller``][dyce.r.UnarySumOpRoller] roller for
        applying *un_op* to this roller as its source.

        ``` python
        >>> import operator
        >>> r_un_op = R.from_value(H(6)).umap(operator.__neg__) ; r_un_op
        UnarySumOpRoller(
          un_op=<built-in function neg>,
          source=ValueRoller(value=H(6), annotation=''),
          annotation='',
        )
        >>> r_un_op == -R.from_value(H(6))
        True

        ```
        """
        return UnarySumOpRoller(un_op, self, annotation=annotation)

    @beartype
    def lt(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.lt(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _lt(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.lt(right_operand)

        return self.map(_lt, other)

    @beartype
    def le(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.le(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _le(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.le(right_operand)

        return self.map(_le, other)

    @beartype
    def eq(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.eq(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _eq(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.eq(right_operand)

        return self.map(_eq, other)

    @beartype
    def ne(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.ne(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _ne(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.ne(right_operand)

        return self.map(_ne, other)

    @beartype
    def gt(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.gt(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _gt(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.gt(right_operand)

        return self.map(_gt, other)

    @beartype
    def ge(self, other: _ROperandT) -> BinarySumOpRoller:
        r"""
        Shorthand for ``#!python self.map(lambda left, right: left.ge(right), other)``.

        See the [``map`` method][dyce.r.R.map].
        """

        def _ge(left_operand: RollOutcome, right_operand: RollOutcome) -> RollOutcome:
            return left_operand.ge(right_operand)

        return self.map(_ge, other)

    @beartype
    def is_even(self) -> UnarySumOpRoller:
        r"""
        Shorthand for: ``#!python self.umap(lambda operand: operand.is_even())``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_even(operand: RollOutcome) -> RollOutcome:
            return operand.is_even()

        return self.umap(_is_even)

    @beartype
    def is_odd(self) -> UnarySumOpRoller:
        r"""
        Shorthand for: ``#!python self.umap(lambda operand: operand.is_odd())``.

        See the [``umap`` method][dyce.r.R.umap].
        """

        def _is_odd(operand: RollOutcome) -> RollOutcome:
            return operand.is_odd()

        return self.umap(_is_odd)

    @beartype
    def filter(
        self,
        predicate: _PredicateT,
        annotation: Any = "",
    ) -> FilterRoller:
        r"""
        Shorthand for ``#!python type(self).filter_from_sources(predicate, self,
        annotation=annotation)``.

        See the [``filter_from_sources`` method][dyce.r.R.filter_from_sources].
        """
        return type(self).filter_from_sources(predicate, self, annotation=annotation)

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
        Shorthand for ``#!python type(self).select_from_sources(which, self,
        annotation=annotation)``.

        See the [``select_from_sources`` method][dyce.r.R.select_from_sources].
        """
        return type(self).select_from_sources(which, self, annotation=annotation)


class ValueRoller(R):
    r"""
    A [roller][dyce.r.R] whose roll outcomes are derived from scalars,
    [``H`` objects][dyce.h.H], [``P`` objects][dyce.p.P],
    [``RollOutcome`` objects][dyce.r.RollOutcome], or even
    [``Roll`` objects][dyce.r.Roll], instead of other source rollers.
    """
    __slots__: Union[str, Iterable[str]] = ("_value",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        value: _ValueT,
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=(), annotation=annotation, **kw)

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
        elif isinstance(self.value, RealLike):
            return Roll(self, roll_outcomes=(RollOutcome(self.value),))
        else:
            assert False, f"unrecognized value type {self.value!r}"

    # ---- Properties ------------------------------------------------------------------

    @property
    def value(self) -> _ValueT:
        r"""
        The value to be emitted by this roller via its
        [``ValueRoller.roll`` method][dyce.r.ValueRoller.roll].
        """
        return self._value


class PoolRoller(R):
    r"""
    A [roller][dyce.r.R] for rolling flattened “pools” from all *sources*.

    ``` python
    >>> PoolRoller((
    ...   PoolRoller((
    ...     ValueRoller(11),
    ...     ValueRoller(12),
    ...   )),
    ...   PoolRoller((
    ...     PoolRoller((
    ...       ValueRoller(211),
    ...       ValueRoller(212),
    ...     )),
    ...     PoolRoller((
    ...       ValueRoller(221),
    ...       ValueRoller(222),
    ...     )),
    ...   )),
    ...   ValueRoller(3),
    ... )).roll()
    Roll(
      r=...,
      roll_outcomes=(
        RollOutcome(
          value=11,
          sources=...,
        ),
        RollOutcome(
          value=12,
          sources=...,
        ),
        RollOutcome(
          value=211,
          sources=...,
        ),
        RollOutcome(
          value=212,
          sources=...,
        ),
        RollOutcome(
          value=221,
          sources=...,
        ),
        RollOutcome(
          value=222,
          sources=...,
        ),
        RollOutcome(
          value=3,
          sources=...,
        ),
      ),
      source_rolls=...,
    )

    ```
    """
    __slots__: Union[str, Iterable[str]] = ()

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = list(self.source_rolls())

        return Roll(
            self,
            roll_outcomes=(
                roll_outcome
                for roll_outcome in chain.from_iterable(source_rolls)
                if roll_outcome.value is not None
            ),
            source_rolls=source_rolls,
        )


class RepeatRoller(R):
    r"""
    A [roller][dyce.r.R] to implement the ``#!python __matmul__`` operator. It is akin
    to a homogeneous [``PoolRoller``][dyce.r.PoolRoller] containing *n* identical
    *source*s.

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
    __slots__: Union[str, Iterable[str]] = ("_n",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        n: SupportsInt,
        source: _SourceT,
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=(source,), annotation=annotation, **kw)
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
        source_rolls: List[Roll] = []

        for _ in range(self.n):
            source_rolls.extend(self.source_rolls())

        return Roll(
            self,
            roll_outcomes=(
                roll_outcome
                for roll_outcome in chain.from_iterable(source_rolls)
                if roll_outcome.value is not None
            ),
            source_rolls=source_rolls,
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def n(self) -> int:
        r"""
        The number of times to “repeat” the roller’s sole source.
        """
        return self._n


class BasicOpRoller(R):
    r"""
    A [roller][dyce.r.R] for applying *op* to some variation of outcomes from *sources*.
    Any [``RollOutcome``][dyce.r.RollOutcome]s returned by *op* are used directly in the
    creation of a new [``Roll``][dyce.r.Roll].
    """
    __slots__: Union[str, Iterable[str]] = ("_op",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        op: BasicOperatorT,
        sources: Iterable[_SourceT],
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=sources, annotation=annotation, **kw)
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
        return super().__eq__(other) and (_callable_cmp(self.op, other.op))

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = list(self.source_rolls())
        res = self.op(
            self,
            (
                roll_outcome
                for roll_outcome in chain.from_iterable(source_rolls)
                if roll_outcome.value is not None
            ),
        )

        if isinstance(res, RollOutcome):
            roll_outcomes = (res,)
        else:
            roll_outcomes = res  # type: ignore [assignment]  # TODO(posita): WTF?

        return Roll(
            self,
            roll_outcomes=roll_outcomes,
            source_rolls=source_rolls,
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def op(self) -> BasicOperatorT:
        r"""
        The operator this roller applies to its sources.
        """
        return self._op


class NarySumOpRoller(BasicOpRoller):
    r"""
    A [``BasicOpRoller``][dyce.r.BasicOpRoller] for applying *op* to the sum of outcomes
    grouped by each of *sources*.
    """
    __slots__: Union[str, Iterable[str]] = ()

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = list(self.source_rolls())

        def _sum_roll_outcomes_by_rolls() -> Iterator[RollOutcome]:
            for source_roll in source_rolls:
                if len(source_roll) == 1 and source_roll[0].value is not None:
                    yield from source_roll
                else:
                    yield RollOutcome(sum(source_roll.outcomes()), sources=source_roll)

        res = self.op(self, _sum_roll_outcomes_by_rolls())

        if isinstance(res, RollOutcome):
            roll_outcomes = (res,)
        else:
            roll_outcomes = res  # type: ignore [assignment]  # TODO(posita): WTF?

        return Roll(
            self,
            roll_outcomes=roll_outcomes,
            source_rolls=source_rolls,
        )


class BinarySumOpRoller(NarySumOpRoller):
    r"""
    An [``NarySumOpRoller``][dyce.r.NarySumOpRoller] for applying a binary operator
    *bin_op* to the sum of all outcomes from its *left_source* and the sum of all
    outcomes from its *right_source*.
    """
    __slots__: Union[str, Iterable[str]] = ("_bin_op",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        bin_op: _RollOutcomeBinaryOperatorT,
        left_source: _SourceT,
        right_source: _SourceT,
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."

        def _op(
            r: R,
            roll_outcomes: Iterable[RollOutcome],
        ) -> Union[RollOutcome, Iterable[RollOutcome]]:
            left_operand, right_operand = roll_outcomes

            return bin_op(left_operand, right_operand)

        super().__init__(
            op=_op, sources=(left_source, right_source), annotation=annotation, **kw
        )
        self._bin_op = bin_op

    # ---- Properties ------------------------------------------------------------------

    @property
    def bin_op(self) -> _RollOutcomeBinaryOperatorT:
        r"""
        The operator this roller applies to its sources.
        """
        return self._bin_op

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        def _source_repr(source: _SourceT) -> str:
            return indent(repr(source), "  ").strip()

        left_source, right_source = self.sources

        return f"""{type(self).__name__}(
  bin_op={self.bin_op!r},
  left_source={_source_repr(left_source)},
  right_source={_source_repr(right_source)},
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and (_callable_cmp(self.bin_op, other.bin_op))


class UnarySumOpRoller(NarySumOpRoller):
    r"""
    An [``NarySumOpRoller``][dyce.r.NarySumOpRoller] for applying a unary operator
    *un_op* to the sum of all outcomes from its sole *source*.
    """
    __slots__: Union[str, Iterable[str]] = ("_un_op",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        un_op: _RollOutcomeUnaryOperatorT,
        source: _SourceT,
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."

        def _op(
            r: R,
            roll_outcomes: Iterable[RollOutcome],
        ) -> Union[RollOutcome, Iterable[RollOutcome]]:
            (operand,) = roll_outcomes

            return un_op(operand)

        super().__init__(op=_op, sources=(source,), annotation=annotation, **kw)
        self._un_op = un_op

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        (source,) = self.sources

        return f"""{type(self).__name__}(
  un_op={self.un_op!r},
  source={indent(repr(source), "  ").strip()},
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and (_callable_cmp(self.un_op, other.un_op))

    # ---- Properties ------------------------------------------------------------------

    @property
    def un_op(self) -> _RollOutcomeUnaryOperatorT:
        r"""
        The operator this roller applies to its sources.
        """
        return self._un_op


class FilterRoller(R):
    r"""
    A [roller][dyce.r.R] for applying *predicate* to filter outcomes its *sources*.

    <!-- BEGIN MONKEY PATCH --
    For deterministic outcomes.

    >>> import random
    >>> from dyce import rng
    >>> rng.RNG = random.Random(1639580307)

      -- END MONKEY PATCH -->

    ``` python
    >>> r_d6 = R.from_value(H(6))
    >>> filter_r = (2@r_d6).filter(
    ...   lambda outcome: outcome.value is not None and outcome.value > 3,  # type: ignore [operator]
    ... )
    >>> (filter_r).roll()
    Roll(
      r=FilterRoller(
        predicate=<function <lambda> at ...>,
        sources=(
          RepeatRoller(
            n=2,
            source=ValueRoller(value=H(6), annotation=''),
            annotation='',
          ),
        ),
        annotation='',
      ),
      roll_outcomes=(
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        ),
        RollOutcome(
          value=5,
          sources=(),
        ),
      ),
      source_rolls=(
        Roll(
          r=RepeatRoller(
            n=2,
            source=ValueRoller(value=H(6), annotation=''),
            annotation='',
          ),
          roll_outcomes=(
            RollOutcome(
              value=2,
              sources=(),
            ),
            RollOutcome(
              value=5,
              sources=(),
            ),
          ),
          source_rolls=(
            Roll(
              r=ValueRoller(value=H(6), annotation=''),
              roll_outcomes=(
                RollOutcome(
                  value=2,
                  sources=(),
                ),
              ),
              source_rolls=(),
            ),
            Roll(
              r=ValueRoller(value=H(6), annotation=''),
              roll_outcomes=(
                RollOutcome(
                  value=5,
                  sources=(),
                ),
              ),
              source_rolls=(),
            ),
          ),
        ),
      ),
    )

    ```

    See the section on “[Filtering and
    substitution](rollin.md#filtering-and-substitution)” more examples.
    """
    __slots__: Tuple[str, ...] = ("_predicate",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        predicate: _PredicateT,
        sources: Iterable[R],
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=sources, annotation=annotation, **kw)
        self._predicate = predicate

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  predicate={self.predicate!r},
  sources=({_seq_repr(self.sources)}),
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return super().__eq__(other) and _callable_cmp(self.predicate, other.predicate)

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = list(self.source_rolls())

        def _filtered_roll_outcomes() -> Iterator[RollOutcome]:
            for roll_outcome in chain.from_iterable(source_rolls):
                if roll_outcome.value is not None:
                    if self.predicate(roll_outcome):
                        yield roll_outcome
                    else:
                        yield roll_outcome.euthanize()

        return Roll(
            self,
            roll_outcomes=_filtered_roll_outcomes(),
            source_rolls=source_rolls,
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def predicate(self) -> _PredicateT:
        r"""
        The predicate this roller applies to filter its sources.
        """
        return self._predicate


class SelectionRoller(R):
    r"""
    A [roller][dyce.r.R] for sorting outcomes from its *sources* and applying a selector
    *which*.

    Roll outcomes in created rolls are ordered according to the selections *which*.
    However, those selections are interpreted as indexes in a *sorted* view of the
    source’s roll outcomes.

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
          sources=(),
        ),
        RollOutcome(
          value=10,
          sources=(),
        ),
        RollOutcome(
          value=1000,
          sources=(),
        ),
        RollOutcome(
          value=100,
          sources=(),
        ),
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=1,
              sources=(),
            ),
          ),
        ),
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=10000,
              sources=(),
            ),
          ),
        ),
      ),
      source_rolls=...,
    )

    ```
    """
    __slots__: Union[str, Iterable[str]] = ("_which",)

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        which: Iterable[_GetItemT],
        sources: Iterable[_SourceT],
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=sources, annotation=annotation, **kw)
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
        return super().__eq__(other) and self.which == other.which

    @beartype
    def roll(self) -> Roll:
        r""""""
        source_rolls = list(self.source_rolls())
        roll_outcomes = list(
            roll_outcome
            for roll_outcome in chain.from_iterable(source_rolls)
            if roll_outcome.value is not None
        )
        roll_outcomes.sort(key=attrgetter("value"))
        all_indexes = tuple(range(len(roll_outcomes)))
        selected_indexes = tuple(getitems(all_indexes, self.which))

        def _selected_roll_outcomes():
            for selected_index in selected_indexes:
                selected_roll_outcome = roll_outcomes[selected_index]
                assert selected_roll_outcome.value is not None
                yield selected_roll_outcome

            for excluded_index in set(all_indexes) - set(selected_indexes):
                yield roll_outcomes[excluded_index].euthanize()

        return Roll(
            self,
            roll_outcomes=_selected_roll_outcomes(),
            source_rolls=source_rolls,
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def which(self) -> Tuple[_GetItemT, ...]:
        r"""
        The selector this roller applies to the sorted outcomes of its sole source.
        """
        return self._which


class SubstitutionRoller(R):
    r"""
    A [roller][dyce.r.R] for applying *expansion_op* to determine when to roll new
    values up to *max_depth* times for incorporation via *coalesce_mode*.

    <!-- BEGIN MONKEY PATCH --
    For deterministic outcomes.

    >>> import random
    >>> from dyce import rng
    >>> rng.RNG = random.Random(1639580307)

      -- END MONKEY PATCH -->

    ``` python
    >>> from dyce.r import SubstitutionRoller
    >>> r_d6 = R.from_value(H(6))
    >>> r_replace = SubstitutionRoller(
    ...   lambda outcome: RollOutcome(0) if outcome.value is not None and outcome.value <= 3 else outcome,
    ...   r_d6,
    ... )
    >>> (2@r_replace).roll()
    Roll(
      r=RepeatRoller(
        n=2,
        source=SubstitutionRoller(
          expansion_op=<function <lambda> at ...>,
          source=ValueRoller(value=H(6), annotation=''),
          coalesce_mode=<CoalesceMode.REPLACE: 1>,
          max_depth=1,
          annotation='',
        ),
        annotation='',
      ),
      roll_outcomes=(
        RollOutcome(
          value=0,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        ),
        RollOutcome(
          value=5,
          sources=(),
        ),
      ),
      source_rolls=(...),
    )

    ```

    See the section on “[Filtering and
    substitution](rollin.md#filtering-and-substitution)” more examples.
    """
    __slots__: Tuple[str, ...] = ("_coalesce_mode", "_expansion_op", "_max_depth")

    # ---- Initializer -----------------------------------------------------------------

    @beartype
    def __init__(
        self,
        expansion_op: _ExpansionOperatorT,
        source: _SourceT,
        coalesce_mode: CoalesceMode = CoalesceMode.REPLACE,
        max_depth: SupportsInt = 1,
        annotation: Any = "",
        **kw,
    ):
        r"Initializer."
        super().__init__(sources=(source,), annotation=annotation, **kw)
        self._expansion_op = expansion_op
        self._coalesce_mode = coalesce_mode
        self._max_depth = as_int(max_depth)

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        (source,) = self.sources

        return f"""{type(self).__name__}(
  expansion_op={self.expansion_op!r},
  source={indent(repr(source), "  ").strip()},
  coalesce_mode={self.coalesce_mode!r},
  max_depth={self.max_depth!r},
  annotation={self.annotation!r},
)"""

    @beartype
    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other)
            and _callable_cmp(self.expansion_op, other.expansion_op)
            and self.coalesce_mode == other.coalesce_mode
            and self.max_depth == other.max_depth
        )

    @beartype
    def roll(self) -> Roll:
        r""""""
        (source_roll,) = self.source_rolls()
        source_rolls: List[Roll] = []

        def _expanded_roll_outcomes(
            roll: Roll,
            depth: int = 0,
        ) -> Iterator[RollOutcome]:
            source_rolls.append(roll)
            roll_outcomes = (
                roll_outcome for roll_outcome in roll if roll_outcome.value is not None
            )

            if depth >= self.max_depth:
                yield from roll_outcomes

                return

            for roll_outcome in roll_outcomes:
                expanded = self.expansion_op(roll_outcome)

                if isinstance(expanded, RollOutcome):
                    if expanded is not roll_outcome:
                        expanded = expanded.adopt((roll_outcome,), CoalesceMode.APPEND)

                    yield expanded
                elif isinstance(expanded, Roll):
                    if self.coalesce_mode == CoalesceMode.REPLACE:
                        yield roll_outcome.euthanize()
                    elif self.coalesce_mode == CoalesceMode.APPEND:
                        yield roll_outcome
                    else:
                        assert (
                            False
                        ), f"unrecognized substitution mode {self.coalesce_mode!r}"

                    expanded_roll = expanded.adopt((roll_outcome,), CoalesceMode.APPEND)
                    yield from _expanded_roll_outcomes(expanded_roll, depth + 1)
                else:
                    assert False, f"unrecognized type for expanded value {expanded!r}"

        return Roll(
            self,
            roll_outcomes=_expanded_roll_outcomes(source_roll),
            source_rolls=source_rolls,
        )

    # ---- Properties ------------------------------------------------------------------

    @property
    def max_depth(self) -> int:
        r"""
        The max number of times this roller will attempt to substitute an outcome satisfying
        its [``expansion_op``][dyce.r.SubstitutionRoller.expansion_op].
        """
        return self._max_depth

    @property
    def expansion_op(self) -> _ExpansionOperatorT:
        r"""
        The expansion operator this roller applies to decide whether to substitute outcomes.
        """
        return self._expansion_op

    @property
    def coalesce_mode(self) -> CoalesceMode:
        r"""
        The coalesce mode this roller uses to incorporate substituted outcomes.
        """
        return self._coalesce_mode


class RollOutcome:
    r"""
    !!! warning "Experimental"

        This class should be considered experimental and may change or disappear in
        future versions.

    A single, ([mostly][dyce.r.Roll.__init__]) immutable outcome generated by a roll.
    """
    __slots__: Union[str, Iterable[str]] = ("_roll", "_sources", "_value")

    # ---- Initializer -----------------------------------------------------------------

    @experimental
    @beartype
    def __init__(
        self,
        value: Optional[RealLike],
        sources: Iterable["RollOutcome"] = (),
    ):
        r"Initializer."
        super().__init__()
        self._value = value
        self._sources = tuple(sources)
        self._roll: Optional[Roll] = None

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
    def __lt__(self, other: _RollOutcomeOperandT) -> bool:  # type: ignore [has-type]
        if isinstance(other, RollOutcome):
            return bool(__lt__(self.value, other.value))
        else:
            return NotImplemented

    @beartype
    # TODO(posita): See <https://github.com/python/mypy/issues/10943>
    def __le__(self, other: _RollOutcomeOperandT) -> bool:  # type: ignore [has-type]
        if isinstance(other, RollOutcome):
            return bool(__le__(self.value, other.value))
        else:
            return NotImplemented

    @beartype
    def __eq__(self, other) -> bool:
        if isinstance(other, RollOutcome):
            return bool(__eq__(self.value, other.value))
        else:
            return super().__eq__(other)

    @beartype
    def __ne__(self, other) -> bool:
        if isinstance(other, RollOutcome):
            return bool(__ne__(self.value, other.value))
        else:
            return super().__ne__(other)

    @beartype
    def __gt__(self, other: _RollOutcomeOperandT) -> bool:
        if isinstance(other, RollOutcome):
            return bool(__gt__(self.value, other.value))
        else:
            return NotImplemented

    @beartype
    def __ge__(self, other: _RollOutcomeOperandT) -> bool:
        if isinstance(other, RollOutcome):
            return bool(__ge__(self.value, other.value))
        else:
            return NotImplemented

    @beartype
    def __add__(self, other: _RollOutcomeOperandT) -> RollOutcome:
        try:
            return self.map(__add__, other)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __radd__(self, other: RealLike) -> RollOutcome:
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
    def __rsub__(self, other: RealLike) -> RollOutcome:
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
    def __rmul__(self, other: RealLike) -> RollOutcome:
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
    def __rtruediv__(self, other: RealLike) -> RollOutcome:
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
    def __rfloordiv__(self, other: RealLike) -> RollOutcome:
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
    def __rmod__(self, other: RealLike) -> RollOutcome:
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
    def __rpow__(self, other: RealLike) -> RollOutcome:
        try:
            return self.rmap(other, __pow__)
        except NotImplementedError:
            return NotImplemented

    @beartype
    def __and__(self, other: Union["RollOutcome", SupportsInt]) -> RollOutcome:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__and__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rand__(self, other: SupportsInt) -> RollOutcome:
        try:
            return self.rmap(as_int(other), __and__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __xor__(self, other: Union["RollOutcome", SupportsInt]) -> RollOutcome:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__xor__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __rxor__(self, other: SupportsInt) -> RollOutcome:
        try:
            return self.rmap(as_int(other), __xor__)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __or__(self, other: Union["RollOutcome", SupportsInt]) -> RollOutcome:
        try:
            if isinstance(other, SupportsInt):
                other = as_int(other)

            return self.map(__or__, other)
        except (NotImplementedError, TypeError):
            return NotImplemented

    @beartype
    def __ror__(self, other: SupportsInt) -> RollOutcome:
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
        Shorthand for ``#!python self.source_roll.annotation``.

        See the [``source_roll``][dyce.r.RollOutcome.source_roll] and
        [``Roll.annotation``][dyce.r.Roll.annotation] properties.
        """
        return self.source_roll.annotation

    @property
    def r(self) -> R:
        r"""
        Shorthand for ``#!python self.source_roll.r``.

        See the [``source_roll``][dyce.r.RollOutcome.source_roll] and
        [``Roll.r``][dyce.r.Roll.r] properties.
        """
        return self.source_roll.r

    @property
    def source_roll(self) -> Roll:
        r"""
        Returns the roll if one has been associated with this roll outcome. Usually that
        happens by submitting the roll outcome to the
        [``Roll.__init__`` method][dyce.r.Roll.__init__] inside a
        [``R.roll`` method][dyce.r.R.roll] implementation. Accessing this property
        before the roll outcome has been associated with a roll is considered a
        programming error.

        ``` python
        >>> ro = RollOutcome(4)
        >>> ro.source_roll
        Traceback (most recent call last):
          ...
        AssertionError: RollOutcome.source_roll accessed before associating the roll outcome with a roll (usually via Roll.__init__)
        assert None is not None
        >>> roll = Roll(R.from_value(4), roll_outcomes=(ro,))
        >>> ro.source_roll
        Roll(
          r=ValueRoller(value=4, annotation=''),
          roll_outcomes=(
            RollOutcome(
              value=4,
              sources=(),
            ),
          ),
          source_rolls=(),
        )

        ```
        """
        assert (
            self._roll is not None
        ), "RollOutcome.source_roll accessed before associating the roll outcome with a roll (usually via Roll.__init__)"

        return self._roll

    @property
    def sources(self) -> Tuple[RollOutcome, ...]:
        r"""
        The source roll outcomes from which this roll outcome was generated.
        """
        return self._sources

    @property
    def value(self) -> Optional[RealLike]:
        r"""
        The outcome value. A value of ``#!python None`` is used to signal that a source’s
        roll outcome was excluded by the roller.
        """
        return self._value

    # ---- Methods ---------------------------------------------------------------------

    @beartype
    def map(
        self,
        bin_op: _BinaryOperatorT,
        right_operand: _RollOutcomeOperandT,
    ) -> RollOutcome:
        r"""
        Applies *bin_op* to the value of this roll outcome as the left operand and
        *right_operand* as the right. Shorthands exist for many arithmetic operators and
        comparators.

        ``` python
        >>> import operator
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
            right_operand_value: Optional[RealLike] = right_operand.value
        else:
            sources = (self,)
            right_operand_value = right_operand

        if isinstance(right_operand_value, RealLike):
            return type(self)(bin_op(self.value, right_operand_value), sources)
        else:
            raise NotImplementedError

    @beartype
    def rmap(self, left_operand: RealLike, bin_op: _BinaryOperatorT) -> RollOutcome:
        r"""
        Analogous to the [``map`` method][dyce.r.RollOutcome.map], but where the caller
        supplies *left_operand*.

        ``` python
        >>> import operator
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

        !!! note

            The positions of *left_operand* and *bin_op* are different from
            [``map`` method][dyce.r.RollOutcome.map]. This is intentional and serves as
            a reminder of operand ordering.
        """
        if isinstance(left_operand, RealLike):
            return type(self)(bin_op(left_operand, self.value), sources=(self,))
        else:
            raise NotImplementedError

    @beartype
    def umap(
        self,
        un_op: _UnaryOperatorT,
    ) -> RollOutcome:
        r"""
        Applies *un_op* to the value of this roll outcome. Shorthands exist for many
        arithmetic operators and comparators.

        ``` python
        >>> import operator
        >>> two_neg = RollOutcome(-2)
        >>> two_neg.umap(operator.__neg__)
        RollOutcome(
          value=2,
          sources=(
            RollOutcome(
              value=-2,
              sources=(),
            ),
          ),
        )
        >>> two_neg.umap(operator.__neg__) == -two_neg
        True

        ```
        """
        return type(self)(un_op(self.value), sources=(self,))

    @beartype
    def lt(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__lt__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__lt__(self.value, other)), sources=(self,))

    @beartype
    def le(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__le__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__le__(self.value, other)), sources=(self,))

    @beartype
    def eq(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__eq__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__eq__(self.value, other)), sources=(self,))

    @beartype
    def ne(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__ne__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__ne__(self.value, other)), sources=(self,))

    @beartype
    def gt(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__gt__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__gt__(self.value, other)), sources=(self,))

    @beartype
    def ge(self, other: _RollOutcomeOperandT) -> RollOutcome:
        if isinstance(other, RollOutcome):
            return type(self)(
                bool(__ge__(self.value, other.value)), sources=(self, other)
            )
        else:
            return type(self)(bool(__ge__(self.value, other)), sources=(self,))

    @beartype
    def is_even(self) -> RollOutcome:
        r"""
        Shorthand for: ``#!python self.umap(dyce.types.is_even)``.

        See the [``umap`` method][dyce.r.RollOutcome.umap].
        """
        return self.umap(is_even)

    @beartype
    def is_odd(self) -> RollOutcome:
        r"""
        Shorthand for: ``#!python self.umap(dyce.types.is_even)``.

        See the [``umap`` method][dyce.r.RollOutcome.umap].
        """
        return self.umap(is_odd)

    @beartype
    def adopt(
        self,
        sources: Iterable["RollOutcome"] = (),
        coalesce_mode: CoalesceMode = CoalesceMode.REPLACE,
    ) -> RollOutcome:
        r"""
        Creates and returns a new roll outcome identical to this roll outcome, but with
        *sources* replacing or appended to this roll outcome’s sources in accordance
        with *coalesce_mode*.

        ``` python
        >>> from dyce.r import CoalesceMode
        >>> orig = RollOutcome(1, sources=(RollOutcome(2),)) ; orig
        RollOutcome(
          value=1,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        )
        >>> orig.adopt((RollOutcome(3),), coalesce_mode=CoalesceMode.REPLACE)
        RollOutcome(
          value=1,
          sources=(
            RollOutcome(
              value=3,
              sources=(),
            ),
          ),
        )
        >>> orig.adopt((RollOutcome(3),), coalesce_mode=CoalesceMode.APPEND)
        RollOutcome(
          value=1,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
            RollOutcome(
              value=3,
              sources=(),
            ),
          ),
        )

        ```
        """
        if coalesce_mode is CoalesceMode.REPLACE:
            adopted_sources = sources
        elif coalesce_mode is CoalesceMode.APPEND:
            adopted_sources = chain(self.sources, sources)
        else:
            assert False, f"unrecognized substitution mode {self.coalesce_mode!r}"

        adopted_roll_outcome = type(self)(self.value, adopted_sources)
        adopted_roll_outcome._roll = self._roll

        return adopted_roll_outcome

    @beartype
    def euthanize(self) -> RollOutcome:
        r"""
        Shorthand for ``#!python self.umap(lambda operand: None)``.

        ``` python
        >>> two = RollOutcome(2)
        >>> two.euthanize()
        RollOutcome(
          value=None,
          sources=(
            RollOutcome(
              value=2,
              sources=(),
            ),
          ),
        )

        ```

        See the [``umap`` method][dyce.r.RollOutcome.umap].
        """

        def _euthanize(operand: Optional[RealLike]) -> Optional[RealLike]:
            return None

        return self.umap(_euthanize)


class Roll(Sequence[RollOutcome]):
    r"""
    !!! warning "Experimental"

        This class should be considered experimental and may change or disappear in
        future versions.

    An immutable roll result (or “roll” for short). More specifically, the result of
    calling the [``R.roll`` method][dyce.r.R.roll]. Rolls are sequences of
    [``RollOutcome`` objects][dyce.r.RollOutcome] that can be assembled into trees.
    """
    __slots__: Union[str, Iterable[str]] = ("_r", "_roll_outcomes", "_source_rolls")

    # ---- Initializer -----------------------------------------------------------------

    @experimental
    @beartype
    def __init__(
        self,
        r: R,
        roll_outcomes: Iterable[RollOutcome],
        source_rolls: Iterable["Roll"] = (),
    ):
        r"""
        Initializer.

        This initializer will associate each of *roll_outcomes* with the newly
        constructed roll if they do not already have a
        [``source_roll``][dyce.r.RollOutcome.source_roll].

        ``` python
        >>> r_4 = ValueRoller(4)
        >>> roll = r_4.roll()
        >>> new_roll = Roll(r_4, roll) ; new_roll
        Roll(
          r=ValueRoller(value=4, annotation=''),
          roll_outcomes=(
            RollOutcome(
              value=4,
              sources=(),
            ),
          ),
          source_rolls=(),
        )
        >>> roll[0].source_roll == roll
        True
        >>> roll[0].r == r_4
        True

        ```

        !!! note

            Technically, this violates the immutability of roll outcomes.

            ``dyce`` does not generally contemplate creation of rolls or roll outcomes
            outside the womb of [``R.roll``][dyce.r.R.roll] implementations.
            [``Roll``][dyce.r.Roll] and [``RollOutcome``][dyce.r.RollOutcome] objects
            generally mate for life, being created exclusively for (and in close
            proximity to) one another. A roll manipulating a roll outcome’s internal
            state post initialization may seem unseemly, but that intimacy is a
            fundamental part of their primordial ritual.

            That being said, you’re an adult. Do what you want. Just know that if you’re
            going to create your own roll outcomes and pimp them out all over town, they
            might pick something up along the way.

            See also the
            [``RollOutcome.source_roll`` property][dyce.r.RollOutcome.source_roll].
        """
        super().__init__()
        self._r = r
        self._roll_outcomes = tuple(roll_outcomes)
        self._source_rolls = tuple(source_rolls)

        for roll_outcome in self._roll_outcomes:
            if roll_outcome._roll is None:
                roll_outcome._roll = self

    # ---- Overrides -------------------------------------------------------------------

    @beartype
    def __repr__(self) -> str:
        return f"""{type(self).__name__}(
  r={indent(repr(self.r), "  ").strip()},
  roll_outcomes=({_seq_repr(self)}),
  source_rolls=({_seq_repr(self.source_rolls)}),
)"""

    @beartype
    def __len__(self) -> int:
        return len(self._roll_outcomes)

    @overload
    def __getitem__(self, key: SupportsIndex) -> RollOutcome:
        ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[RollOutcome, ...]:
        ...

    @beartype
    # TODO(posita): See <https://github.com/python/mypy/issues/8393>
    # TODO(posita): See <https://github.com/beartype/beartype/issues/39#issuecomment-871914114> et seq.
    def __getitem__(  # type: ignore [override]
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
    def source_rolls(self) -> Tuple[Roll, ...]:
        r"""
        The source rolls from which this roll was generated.
        """
        return self._source_rolls

    # ---- Methods ---------------------------------------------------------------------

    @beartype
    def adopt(
        self,
        sources: Iterable["RollOutcome"] = (),
        coalesce_mode: CoalesceMode = CoalesceMode.REPLACE,
    ) -> Roll:
        r"""
        Shorthand for ``#!python Roll(self.r, (roll_outcome.adopt(sources,
        coalesce_mode) for roll_outcome in self), self.source_rolls)``.
        """
        return type(self)(
            self.r,
            (roll_outcome.adopt(sources, coalesce_mode) for roll_outcome in self),
            self.source_rolls,
        )

    @beartype
    def outcomes(self) -> Iterator[RealLike]:
        r"""
        Shorthand for ``#!python (roll_outcome.value for roll_outcome in self if
        roll_outcome.value is not None)``.

        <!-- BEGIN MONKEY PATCH --
        For deterministic outcomes.

        >>> import random
        >>> from dyce import rng
        >>> rng.RNG = random.Random(1633056410)

          -- END MONKEY PATCH -->

        !!! info

            Unlike [``H.roll``][dyce.h.H.roll] and [``P.roll``][dyce.p.P.roll], these
            outcomes are *not* sorted. Instead, they retain the ordering as passed to
            [``__init__``][dyce.r.Roll.__init__].

            ``` python
            >>> r_3d6 = 3@R.from_value(H(6))
            >>> r_3d6_neg = 3@-R.from_value(H(6))
            >>> roll = R.from_sources(r_3d6, r_3d6_neg).roll()
            >>> tuple(roll.outcomes())
            (1, 3, 1, -4, -6, -1)
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
    def total(self) -> RealLike:
        r"""
        Shorthand for ``#!python sum(self.outcomes())``.
        """
        return sum(self.outcomes())


class RollWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This class (and its descendants) should be considered experimental and may
        change or disappear in future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``Roll`` object][dyce.r.Roll] found.
    """
    __slots__: Union[str, Iterable[str]] = ()

    # ---- Overrides -------------------------------------------------------------------

    @abstractmethod
    def on_roll(self, roll: Roll, parents: Iterator[Roll]) -> None:
        ...


class RollOutcomeWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This class (and its descendants) should be considered experimental and may
        change or disappear in future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``RollOutcome`` object][dyce.r.RollOutcome] found.
    """
    __slots__: Union[str, Iterable[str]] = ()

    # ---- Overrides -------------------------------------------------------------------

    @abstractmethod
    def on_roll_outcome(
        self, roll_outcome: RollOutcome, parents: Iterator[RollOutcome]
    ) -> None:
        ...


class RollerWalkerVisitor:
    r"""
    !!! warning "Experimental"

        This class (and its descendants) should be considered experimental and may
        change or disappear in future versions.

    Abstract visitor interface for use with [``walk``][dyce.r.walk] called for each
    [``R`` object][dyce.r.R] found.
    """
    __slots__: Union[str, Iterable[str]] = ()

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

        ``#!python walk`` performs a breadth-first traversal of *root*, assembling a
        secondary index of referencing objects (parents). Visitors are called back
        grouped first by type, then by order encountered.
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

                for source_roll in roll.source_rolls:
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
def _callable_cmp(op1: Callable, op2: Callable) -> bool:
    return op1 == op2 or (
        hasattr(op1, "__code__")
        and hasattr(op2, "__code__")
        and op1.__code__ == op2.__code__
    )


@beartype
def _seq_repr(s: Sequence) -> str:
    seq_repr = indent(",\n".join(repr(i) for i in s), "    ")

    return "\n" + seq_repr + ",\n  " if seq_repr else seq_repr

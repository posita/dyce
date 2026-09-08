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

from functools import partial
from typing import Any, assert_type, cast

import pytest

from dyce import H, P
from dyce.roller import (
    HRoller,
    LiteralRoller,
    PoolRoller,
    PRoller,
    Roller,
    RollerPool,
    _MechanicPoolRoller,
    _MechanicRoller,
    mechanic,
)


class TestMechanicRoller:
    def test_callables(self) -> None:
        class RollerFactories:
            @mechanic()
            def factory(self, value: int) -> Roller[int]:
                return LiteralRoller(value)

            def __call__(self, value: int) -> Roller[int]:
                return LiteralRoller(value)

        some_rollers = RollerFactories()
        roller_factory = some_rollers.factory(3)
        assert_type(roller_factory, Roller[int])
        assert isinstance(roller_factory, _MechanicRoller)
        assert roller_factory.roll().outcome == 3

        callable_factory = mechanic(some_rollers)
        callable_roller = callable_factory(4)
        assert_type(callable_roller, Roller[int])
        assert isinstance(callable_roller, _MechanicRoller)
        assert callable_roller.name == "RollerFactories"
        assert callable_roller.roll().outcome == 4

        bound_factory = mechanic(partial(some_rollers, 5), name="bound")
        bound_roller = bound_factory()
        assert isinstance(bound_roller, _MechanicRoller)
        assert bound_roller.name == "bound"
        assert bound_roller.roll().outcome == 5

    def test_implicit_name(self) -> None:
        @mechanic
        def factory() -> Roller[int]:
            return LiteralRoller(3)

        assert factory().provenance()["name"] == factory.__name__

    def test_explicit_name(self) -> None:
        @mechanic(name="explicit_name")
        def factory() -> Roller[int]:
            return LiteralRoller(3)

        assert factory().provenance()["name"] == "explicit_name"

    def test_operands(self) -> None:
        literal_roller = LiteralRoller(3)

        @mechanic
        def factory() -> Roller[int]:
            return literal_roller

        assert factory().operands == (literal_roller,)

    def test_h(self) -> None:
        d6 = H(6)

        @mechanic
        def factory() -> Roller[int]:
            return HRoller(d6)

        assert factory().h() == d6

    def test_factory_returning_non_roller_raises(self) -> None:
        @mechanic
        def invalid_factory() -> Roller[int]:
            return cast("Any", "not_a_roller")

        with pytest.raises(TypeError, match="must return a Roller or PoolRoller"):
            invalid_factory()


class TestMechanicPoolRoller:
    def test_callables(self) -> None:
        class RollerFactories:
            @mechanic()
            def factory(self, n: int) -> PoolRoller[int]:
                return PRoller(n @ P(2))

            def __call__(self, first: int, second: int) -> PoolRoller[int]:
                return RollerPool(LiteralRoller(first), LiteralRoller(second))

        some_rollers = RollerFactories()
        roller_factory = some_rollers.factory(2)
        assert_type(roller_factory, PoolRoller[int])
        assert isinstance(roller_factory, _MechanicPoolRoller)
        assert len(roller_factory) == 2

        callable_factory = mechanic(some_rollers)
        callable_roller = callable_factory(3, 4)
        assert_type(callable_roller, PoolRoller[int])
        assert isinstance(callable_roller, _MechanicPoolRoller)
        assert callable_roller.name == "RollerFactories"
        assert callable_roller.roll().outcomes == (3, 4)

        bound_factory = mechanic(partial(some_rollers, 5, 6), name="bound")
        bound_roller = bound_factory()
        assert isinstance(bound_roller, _MechanicPoolRoller)
        assert bound_roller.name == "bound"
        assert bound_roller.roll().outcomes == (5, 6)

    def test_implicit_name(self) -> None:
        @mechanic
        def factory() -> PoolRoller[int]:
            return PRoller(P(2))

        assert factory().provenance()["name"] == factory.__name__

    def test_explicit_name(self) -> None:
        @mechanic(name="explicit_name")
        def factory() -> PoolRoller[int]:
            return PRoller(P(2))

        assert factory().provenance()["name"] == "explicit_name"

    def test_operands(self) -> None:
        p_roller = PRoller(P(2))

        @mechanic
        def factory() -> PoolRoller[int]:
            return p_roller

        assert factory().operands == (p_roller,)

    def test_h(self) -> None:
        p3d6 = 3 @ P(6)

        @mechanic
        def factory() -> PoolRoller[int]:
            return PRoller(p3d6)

        assert factory().h() == p3d6.h()

    def test_rolls_with_counts(self) -> None:
        p2d2 = 2 @ P(2)

        @mechanic
        def factory() -> PoolRoller[int]:
            return PRoller(p2d2)

        assert sorted(factory().rolls_with_counts()) == sorted(p2d2.rolls_with_counts())

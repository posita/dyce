# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import json
import random
from dataclasses import dataclass
from typing import ClassVar

import pytest

from dyce import H, HableT, P, rng
from dyce.roller import HRoller, Roll, Roller

__all__ = ()


@dataclass(frozen=True)
class _AdditionCountingOutcome:
    value: int
    times_added: ClassVar[int] = 0

    def __add__(self, other: "_AdditionCountingOutcome") -> "_AdditionCountingOutcome":
        type(self).times_added += 1
        return _AdditionCountingOutcome(self.value + other.value)


class _ConstantRoller(Roller[int]):
    def __init__(self, value: int) -> None:
        self._value = value

    def h(self) -> H[int]:
        return H({self._value: 1})

    def roll(self) -> Roll[int]:
        return Roll(self._value, self)

    def provenance(self) -> dict[str, object]:
        return {"kind": "constant", "value": self._value}


class _CountingHable(HableT[int]):
    def __init__(self, h: H[int]) -> None:
        self._h = h
        self.h_calls = 0

    def h(self) -> H[int]:
        self.h_calls += 1
        return self._h


class TestHRoller:
    def test_addition_preserves_distribution(self) -> None:
        d6 = HRoller(H(6), "d6")

        assert d6.name == "d6"
        assert (d6 + d6).h() == 2 @ H(6)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (d6 + 2).h() == H(6) + 2
        assert (2 + d6).h() == 2 + H(6)

    def test_distribution_is_computed_lazily(self) -> None:
        _AdditionCountingOutcome.times_added = 0
        source = HRoller(H({_AdditionCountingOutcome(1): 1}), "source")
        combined = source + source

        assert _AdditionCountingOutcome.times_added == 0
        assert combined.h() == H({_AdditionCountingOutcome(2): 1})
        assert _AdditionCountingOutcome.times_added == 1

    def test_adding_after_roll_matches_rolling_after_addition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), "d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() + 2
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 + 2).roll()

        assert realized_roll.outcome == deferred_roll.outcome
        assert realized_roll.to_dict() == deferred_roll.to_dict()

    def test_deferred_and_realized_addition_are_equivalent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d6 = HRoller(H(6), "d6")

        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        deferred_roll = (d6 + d6).roll()
        monkeypatch.setattr(rng, "RNG", random.Random(1774583876))
        realized_roll = d6.roll() + d6.roll()

        assert deferred_roll.outcome == realized_roll.outcome
        assert deferred_roll.to_dict() == realized_roll.to_dict()

    def test_literal_plus_roll_is_serializable(self) -> None:
        d6 = HRoller(H(6), "d6")
        roll = 2 + d6.roll()

        assert roll.outcome in 2 + H(6)
        assert json.loads(json.dumps(roll.to_dict())) == roll.to_dict()

    def test_roll_provenance_distinguishes_independent_and_shared_events(self) -> None:
        d6 = HRoller(H(6), "d6")
        independent = d6.roll() + d6.roll()
        shared_source = d6.roll()
        shared = shared_source + shared_source

        independent_provenance = independent.to_dict()
        shared_provenance = shared.to_dict()
        independent_events = independent_provenance["events"]
        shared_events = shared_provenance["events"]
        independent_definitions = independent_provenance["definitions"]
        shared_definitions = shared_provenance["definitions"]

        assert isinstance(independent_events, dict)
        assert isinstance(shared_events, dict)
        assert isinstance(independent_definitions, dict)
        assert isinstance(shared_definitions, dict)
        assert independent_events["e0"]["operands"] == ["e1", "e2"]
        assert shared_events["e0"]["operands"] == ["e1", "e1"]
        assert independent_definitions["d0"]["operands"] == ["d1", "d1"]
        assert shared_definitions["d0"]["operands"] == ["d1", "d1"]

    def test_raw_histograms_are_promoted_to_named_sources(self) -> None:
        d6 = HRoller(H(6), "d6")
        roll = (d6 + H(8)).roll()
        provenance = roll.to_dict()
        definitions = provenance["definitions"]

        assert isinstance(definitions, dict)
        assert definitions["d2"] == {"kind": "source", "name": str(H(8))}


class TestRoller:
    def test_hable_forward_addition_defers_to_roller(self) -> None:
        d6 = HRoller(H(6), "d6")

        assert H(6).__add__(d6) is NotImplemented
        assert P(6).__add__(d6) is NotImplemented

    def test_hable_addition_is_symmetric(self) -> None:
        d6 = HRoller(H(6), "d6")

        assert isinstance(d6 + H(6), Roller)
        assert isinstance(H(6) + d6, Roller)
        assert isinstance(d6 + P(6), Roller)
        assert isinstance(P(6) + d6, Roller)
        assert (d6 + H(6)).h() == 2 @ H(6)
        assert (H(6) + d6).h() == 2 @ H(6)
        assert (d6 + P(6)).h() == 2 @ H(6)
        assert (P(6) + d6).h() == 2 @ H(6)

    def test_hable_promotion_is_lazy(self) -> None:
        d6 = HRoller(H(6), "d6")
        hable = _CountingHable(H(6))

        combined = d6 + hable

        assert hable.h_calls == 0
        assert combined.h() == 2 @ H(6)
        assert hable.h_calls == 1

    def test_hable_promotion_supports_rolls_and_provenance(self) -> None:
        hable = _CountingHable(H(6))

        roll = (HRoller(H(6), "d6") + hable).roll()
        provenance = roll.to_dict()
        definitions = provenance["definitions"]

        assert roll.outcome in 2 @ H(6)
        assert hable.h_calls == 1
        assert isinstance(definitions, dict)
        assert definitions["d2"] == {"kind": "source", "name": str(hable)}

    def test_mixed_roller_addition(self) -> None:
        roll = (HRoller(H({1: 1}), "one") + _ConstantRoller(2)).roll()

        assert roll.outcome == 3
        assert json.loads(json.dumps(roll.to_dict())) == roll.to_dict()

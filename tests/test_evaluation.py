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

import sys
from collections import Counter, UserString
from contextlib import nullcontext
from enum import IntEnum, auto
from fractions import Fraction
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Never

import pytest

from dyce import H, HResult, PResult, TruncationWarning, expand, explode_n
from dyce.d import d0, d1, d2, d6, d8, d10, p2d8, pd6
from dyce.types import DYCE_IS_BEARIFIED, BeartypeCallHintViolation

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

__all__ = ()


class TestResult:
    def test_type_covariance(self) -> None:
        h_result_int: HResult[int] = HResult(d6, 1)
        p_result_int: PResult[int] = PResult(pd6, (1,))

        h_result_object: HResult[object] = h_result_int
        p_result_object: PResult[object] = p_result_int

        assert h_result_object is h_result_int
        assert p_result_object is p_result_int


class TestExpand:
    def test_h_and_p_sources(self) -> None:
        def _fn(
            d6_result: HResult[int],
            p_2d8_result: PResult[int],
            d10_result: HResult[int],
        ) -> int:
            assert d6_result.outcome in d6
            for d8_outcome in p_2d8_result.roll:
                assert d8_outcome in d8
            assert d10_result.outcome in d10
            return d6_result.outcome + sum(p_2d8_result.roll) + d10_result.outcome

        assert expand(_fn, d6, p2d8, d10) == d6 + p2d8 + d10

    @pytest.mark.skipif(DYCE_IS_BEARIFIED, reason="we are ***BEARIFIED***")
    def test_source_neither_h_nor_p_raises_type_error_without_beartype(self) -> None:
        class TotalStr(UserString):
            __slots__ = ()

            @property
            def total(self) -> int:
                return len(self)

        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # ruff: ignore[any-type]
            return d0

        with pytest.raises(TypeError, match=r"\bunrecognized source type\b"):
            expand(_fn, TotalStr("I'm an imposter!"))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    @pytest.mark.skipif(not DYCE_IS_BEARIFIED, reason="we are ***NOT*** bearified")
    def test_source_neither_h_nor_p_raises_hint_violation_with_beartype(self) -> None:
        class TotalStr(UserString):
            __slots__ = ()

            @property
            def total(self) -> int:
                return len(self)

        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # ruff: ignore[any-type]
            return d0

        with pytest.raises(BeartypeCallHintViolation, match=r"\bviolates type hint\b"):
            expand(_fn, TotalStr("I'm an imposter!"))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    def test_callback_returns_h_with_zero_count_outcomes(self) -> None:
        class Result(IntEnum):
            ONES = auto()
            FIVES_OR_SIXES = auto()

        def _fn(p_result: PResult[int]) -> H[Result]:
            c = Counter(p_result.roll)
            return H({Result.ONES: c[1], Result.FIVES_OR_SIXES: c[5] + c[6]})

        assert expand(_fn, 4 @ pd6) == H({Result.ONES: 1, Result.FIVES_OR_SIXES: 2})

    def test_no_sources_raises(self) -> None:
        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # ruff: ignore[any-type]
            return d0

        with pytest.raises(ValueError, match=r"\brequires\b.*\bsource\b"):
            expand(_fn)

    def test_apply_equivalence(self) -> None:
        from enum import IntEnum

        class Versus(IntEnum):
            LOSE = -1
            DRAW = 0
            WIN = 1

            @staticmethod
            def raw_vs(us_outcome: int, them_outcome: int) -> "Versus":
                return (
                    Versus.LOSE
                    if us_outcome < them_outcome
                    else Versus.WIN
                    if us_outcome > them_outcome
                    else Versus.DRAW
                )

            @staticmethod
            def vs(us: HResult[int], them: HResult[int]) -> "Versus":
                return Versus.raw_vs(us.outcome, them.outcome)

        for us_h, them_h in (
            ((5 @ pd6).at(-1), (4 @ pd6).at(-1)),
            (5 @ d6, 4 @ d6),
        ):
            apply_version = (us_h).apply(Versus.raw_vs, them_h)
            expand_version = expand(
                Versus.vs, us_h, them_h, min_path_probability=Fraction(0)
            )
            assert apply_version == expand_version


class TestExpandContext:
    @pytest.mark.parametrize(
        ("min_path_probability", "independent", "expected", "truncated"),
        [
            (None, False, H({3: 1}), True),
            (Fraction(0), False, H({1: 1, 2: 1, 3: 2}), False),
            (Fraction(1, 3), True, H({1: 1, 2: 1, 3: 2}), False),
            (None, True, H({1: 1, 2: 1, 3: 2}), False),
        ],
    )
    def test_min_path_probability_nested_override(
        self,
        *,
        min_path_probability: Fraction | None,
        independent: bool,
        expected: H[int],
        truncated: bool,
    ) -> None:
        def callback(result: HResult[int]) -> H[int] | int:
            if result.outcome == 1:
                return expand(
                    lambda inner: inner.outcome,
                    d2,
                    min_path_probability=min_path_probability,
                    independent=independent,
                )
            else:
                return 3

        with pytest.warns(TruncationWarning) if truncated else nullcontext():
            # each outcome in a d2 is above the minimum path probability of 1/3
            result = expand(callback, d2, min_path_probability=Fraction(1, 3))
        assert result == expected

    def test_min_path_probability_narrowing_override_after_zero(self) -> None:
        def callback(_result: HResult[int]) -> H[int]:
            return expand(
                lambda inner: inner.outcome,
                d2,
                min_path_probability=Fraction(1, 3),
            )

        with pytest.warns(TruncationWarning):
            result = expand(callback, d2, min_path_probability=Fraction(0))
        assert result == H({})

    def test_independent_call_restores_enclosing_context(self) -> None:
        inner_h = H(-6)

        def callback(result: HResult[int]) -> H[int]:
            if result.outcome == 1:
                # This will survive
                min_path_probability = Fraction(0)
                independent = True
            else:
                # These won't
                min_path_probability = None
                independent = False

            return expand(
                lambda inner_result: inner_result.outcome,
                inner_h,
                min_path_probability=min_path_probability,
                independent=independent,
            )

        with pytest.warns(TruncationWarning):
            result = expand(callback, H(3), min_path_probability=Fraction(1, 3))
        assert result == inner_h

    def test_min_path_probability_out_of_range_raises(self) -> None:
        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # ruff: ignore[any-type]
            return d0

        for bad_min_path_probability in (Fraction(-1), Fraction(2)):
            with pytest.raises(ValueError, match=r"\bbetween zero and one\b"):
                expand(_fn, d0, min_path_probability=bad_min_path_probability)


class TestExpandTruncation:
    _D6X_TRUNCATED_AT_3RD_ROLL = H(
        {
            1: 30,
            2: 30,
            3: 30,
            4: 30,
            5: 30,
            7: 5,
            8: 5,
            9: 5,
            10: 5,
            11: 5,
            13: 1,
            14: 1,
            15: 1,
            16: 1,
            17: 1,
        }
    )

    def test_callback_truncates_itself(self) -> None:
        with pytest.warns(TruncationWarning, match=r"\bpath probability\b"):
            assert (
                expand(
                    _explode_with_truncation,
                    d6,
                    min_path_probability=Fraction(1, 6**4 - 1),
                )
                == self._D6X_TRUNCATED_AT_3RD_ROLL
            )

    def test_precision_limit_truncation(self) -> None:
        assert (
            expand(
                _explode_with_truncation,
                d6,
                truncate_countdown=3,
            )
            == self._D6X_TRUNCATED_AT_3RD_ROLL
        )

    def test_recursion_depth_truncation(self) -> None:
        with pytest.warns(TruncationWarning, match=r"\brecursion depth exceeded\b"):
            assert (
                expand(
                    _explode_with_truncation,
                    d6,
                    rcrs_err_countdown=3,
                )
                == self._D6X_TRUNCATED_AT_3RD_ROLL
            )

    def test_recursion_eventually_truncates(self) -> None:
        # Always_recurses has no base case: every branch hits RecursionError and
        # is dropped, leaving an empty histogram. A TruncationWarning is emitted
        # by the innermost expand that catches the RecursionError.
        def _always_recurses(result: HResult[int]) -> H[int] | int:
            return expand(_always_recurses, result.h) + 1

        with pytest.warns(TruncationWarning, match=r"\brecursion\b"):
            result = expand(_always_recurses, d1)
        assert result == d0


@pytest.mark.benchmark
@pytest.mark.skipif(
    find_spec("pytest_benchmark") is None,
    reason="requires benchmark fixture",
)
class TestExpandTruncationBenchmark:
    def test_default(self, benchmark: "BenchmarkFixture") -> None:
        def _callback(r: HResult[int]) -> int:
            return r.outcome * 2

        h = d6
        benchmark(expand, _callback, h)

    def test_skip_truncation(self, benchmark: "BenchmarkFixture") -> None:
        def _callback(r: HResult[int]) -> int:
            return r.outcome * 2

        h = d6
        benchmark(expand, _callback, h, min_path_probability=Fraction(0))


class TestExplodeN:
    def test_explode_n_natural_order(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d6x = d6 + x
        assert explode_n(d6x, n=1) == H(
            {
                2 * x + 7: 1,
                2 * x + 8: 1,
                2 * x + 9: 1,
                2 * x + 10: 1,
                2 * x + 11: 1,
                2 * x + 12: 1,
                x + 1: 6,
                x + 2: 6,
                x + 3: 6,
                x + 4: 6,
                x + 5: 6,
            }
        )


# ---- Helpers -------------------------------------------------------------------------


def _explode_with_truncation(
    result: HResult[int],
    *,
    rcrs_err_countdown: int = sys.getrecursionlimit(),
    truncate_countdown: int = sys.getrecursionlimit(),
) -> H[int] | int:
    if rcrs_err_countdown <= 0:
        raise RecursionError("artificial recursion limit")
    elif truncate_countdown <= 0:
        return d0
    elif result.outcome < max(result.h):
        return result.outcome
    else:
        return (
            expand(
                _explode_with_truncation,
                result.h,
                rcrs_err_countdown=rcrs_err_countdown - 1,
                truncate_countdown=truncate_countdown - 1,
            )
            + result.outcome
        )

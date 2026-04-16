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
import warnings
from collections import Counter, UserString
from enum import IntEnum, auto
from fractions import Fraction
from typing import Any, Never

import pytest

from dyce import H, HResult, P, PResult, expand, explode_n
from dyce.evaluation import TruncationWarning
from dyce.lifecycle import ExperimentalWarning
from dyce.types import BeartypeCallHintViolation

__all__ = ()


class TestExpand:
    def test_h_and_p_sources(self) -> None:
        d6 = H(6)
        d8 = H(8)
        d10 = H(10)
        p_2d8 = 2 @ P(d8)

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

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            assert expand(_fn, d6, p_2d8, d10) == d6 + p_2d8 + d10

    def test_source_neither_h_nor_p_raises(self) -> None:
        class TotalStr(UserString):
            __slots__ = ()

            @property
            def total(self) -> int:
                return len(self)

        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # noqa: ANN401
            return H({})

        with (  # noqa: PT012
            pytest.raises(
                (TypeError, BeartypeCallHintViolation),
                match=r"\b(unrecognized source type|violates type hint)\b",
            ),
            warnings.catch_warnings(),
        ):
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            expand(_fn, TotalStr("I'm an imposter!"))  # type: ignore[call-overload] # ty: ignore[no-matching-overload]

    def test_callback_returns_h_with_zero_count_outcomes(self) -> None:
        class Result(IntEnum):
            ONES = auto()
            FIVES_OR_SIXES = auto()

        def _fn(p_result: PResult[int]) -> H[Result]:
            c = Counter(p_result.roll)
            return H({Result.ONES: c[1], Result.FIVES_OR_SIXES: c[5] + c[6]})

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            assert expand(_fn, 4 @ P(6)) == H(
                {Result.ONES: 1, Result.FIVES_OR_SIXES: 2}
            )

    def test_no_sources_raises(self) -> None:
        def _fn(*_args: Any, **_kw: Any) -> H[Never]:  # noqa: ANN401
            return H({})

        with (  # noqa: PT012
            warnings.catch_warnings(),
            pytest.raises(ValueError, match=r"\brequires\b.*\bsource\b"),
        ):
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            expand(_fn)


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
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            with pytest.warns(TruncationWarning, match=r"\bpath probability\b"):
                assert (
                    expand(
                        _explode_with_truncation,
                        H(6),
                        precision=Fraction(1, 6**4 - 1),
                    )
                    == self._D6X_TRUNCATED_AT_3RD_ROLL
                )

    def test_precision_limit_truncation(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            assert (
                expand(
                    _explode_with_truncation,
                    H(6),
                    truncate_countdown=3,
                )
                == self._D6X_TRUNCATED_AT_3RD_ROLL
            )

    def test_recursion_depth_truncation(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            with pytest.warns(TruncationWarning, match=r"\brecursion\b"):
                assert (
                    expand(
                        _explode_with_truncation,
                        H(6),
                        rcrs_err_countdown=3,
                    )
                    == self._D6X_TRUNCATED_AT_3RD_ROLL
                )

    def test_recursion_eventually_truncates(self) -> None:
        # Always_recurses has no base case: every branch hits RecursionError and
        # is dropped, leaving an empty histogram. A TruncationWarning is emitted
        # by the innermost expand that catches the RecursionError.
        d1 = H(1)

        def _always_recurses(result: HResult[int]) -> H[int] | int:
            return expand(_always_recurses, result.h) + 1

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
            with pytest.warns(TruncationWarning, match=r"\brecursion\b"):
                result = expand(_always_recurses, d1)
        assert result == H({})


class TestExplodeN:
    def test_explode_n_natural_order(self) -> None:
        sympy = pytest.importorskip("sympy", reason="requires sympy")
        x = sympy.symbols("x")
        d6x = H(6) + x
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ExperimentalWarning)
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


def _explode_with_truncation(
    result: HResult[int],
    *,
    rcrs_err_countdown: int = sys.getrecursionlimit(),
    truncate_countdown: int = sys.getrecursionlimit(),
) -> H[int] | int:
    if rcrs_err_countdown <= 0:
        raise RecursionError("artificial recursion limit")
    elif truncate_countdown <= 0:
        return H({})
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

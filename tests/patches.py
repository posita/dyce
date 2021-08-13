# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from typing import Iterator
from unittest.mock import MagicMock

from dyce import H, OutcomeT

__all__ = ()


# ---- Functions -----------------------------------------------------------------------


def patch_roll(h: H, *args: OutcomeT) -> None:
    roll_func = h.roll

    def _f() -> Iterator[OutcomeT]:
        yield from args

        while True:
            yield roll_func()

    h.roll = MagicMock(side_effect=_f())  # type: ignore

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

from importlib.util import find_spec
from random import Random
from typing import cast

import pytest

from dyce import rng
from dyce.rng import _RandSeedT

__all__ = ()

SEED_INT_64 = 0x64656164
SEED_INT_128 = 0x6465616462656566
SEED_INT_192 = 0x646561646265656663616665
SEED_OBJECT = (0x646561646265656663616665,)


class TestRngNumpy:
    pytest.importorskip("numpy")

    def test_numpy_rng_installed(self) -> None:
        from dyce.rng import PCG64DXSMRandom

        assert isinstance(rng._DEFAULT_RNG, PCG64DXSMRandom)  # noqa: SLF001

    def test_numpy_rng_getrandbits_negative_raises(self) -> None:
        from dyce.rng import PCG64DXSMRandom

        rng = PCG64DXSMRandom()
        with pytest.raises(ValueError, match=r"^number of bits must be non-negative$"):
            rng.getrandbits(-1)

    def test_numpy_rng(self) -> None:
        from dyce.rng import PCG64DXSMRandom

        rng = PCG64DXSMRandom()
        for seed, random, getrandbits, randbytes in (
            (
                SEED_INT_64,
                0.5066807340643421,
                0x6CCCD2511ED4B58,
                bytes.fromhex("6cccd2511ed4b581"),
            ),
            (
                SEED_INT_128,
                0.16159916444553268,
                0x32CDBF5A16905E2,
                bytes.fromhex("32cdbf5a16905e29"),
            ),
            (
                SEED_INT_192,
                0.09272816060986888,
                0xE0D0D43C6108BD1,
                bytes.fromhex("e0d0d43c6108bd17"),
            ),
            (
                cast("_RandSeedT", SEED_OBJECT),
                0.012806848293232753,
                0x6A9E9295424F470,
                bytes.fromhex("6a9e9295424f4703"),
            ),
        ):
            _test_random_w_seed_helper(rng, seed, random)
            _test_getrandbits_w_seed_helper(rng, seed, 60, getrandbits)
            _test_randbytes_w_seed_helper(rng, seed, randbytes)


@pytest.mark.skipif(
    find_spec("numpy") is not None,
    reason="requires numpy not be installed",
)
class TestRngStandard:
    def test_standard_rng_installed(self) -> None:
        assert rng._DEFAULT_RNG.__class__ is Random  # noqa: SLF001
        for seed in (
            SEED_INT_64,
            SEED_INT_128,
            SEED_INT_192,
        ):
            _test_random_w_seed_helper(rng._DEFAULT_RNG, seed)  # noqa: SLF001


def _test_getrandbits_w_seed_helper(
    rng: Random,
    seed: _RandSeedT,
    bits: int,
    expected: int,
) -> None:
    rng.seed(seed)
    state = rng.getstate()
    val = rng.getrandbits(bits)
    assert val == expected
    rng.setstate(state)
    assert rng.getrandbits(bits) == val


def _test_randbytes_w_seed_helper(
    rng: Random,
    seed: _RandSeedT,
    expected: bytes,
) -> None:
    rng.seed(seed)
    state = rng.getstate()
    val = rng.randbytes(len(expected))
    assert val == expected
    rng.setstate(state)
    assert rng.randbytes(len(expected)) == val
    rng.setstate(state)
    assert rng.randbytes(len(expected)) == val


def _test_random_w_seed_helper(
    rng: Random,
    seed: _RandSeedT,
    expected: float | None = None,
) -> None:
    rng.seed(seed)
    state = rng.getstate()
    val = rng.random()
    assert val >= 0.0
    assert val < 1.0
    if expected is not None:
        assert val == expected
    assert type(rng)(seed).random() == val
    rng.setstate(state)
    assert rng.random() == val
    rng.seed(seed)
    assert rng.random() == val

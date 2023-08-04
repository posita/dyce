# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from random import Random
from typing import Optional

import pytest

from dyce import rng
from dyce.rng import _RandSeedT

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


SEED_INT_64: int = 0x64656164
SEED_INT_128: int = 0x6465616462656566
SEED_INT_192: int = 0x646561646265656663616665


# ---- Tests ---------------------------------------------------------------------------


def test_numpy_rng_installed() -> None:
    try:
        from dyce.rng import PCG64DXSMRandom
    except ImportError:
        pytest.skip("requires numpy")

    assert isinstance(rng.DEFAULT_RNG, PCG64DXSMRandom)


def test_numpy_rng() -> None:
    try:
        from dyce.rng import PCG64DXSMRandom
    except ImportError:
        pytest.skip("requires numpy")

    rng = PCG64DXSMRandom()
    seed: _RandSeedT
    random: float
    getrandbits: int
    randbytes: bytes

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
    ):
        _test_random_w_seed_helper(rng, seed, random)
        _test_getrandbits_w_seed_helper(rng, seed, 60, getrandbits)
        _test_randbytes_w_seed_helper(rng, seed, randbytes)


def test_standard_rng_installed() -> None:
    try:
        from dyce.rng import PCG64DXSMRandom  # noqa: F401

        pytest.skip("requires numpy not be installed")
    except ImportError:
        pass

    assert isinstance(rng.DEFAULT_RNG, Random)


def test_standard_rng() -> None:
    rng = Random()

    for seed in (
        SEED_INT_64,
        SEED_INT_128,
        SEED_INT_192,
    ):
        _test_random_w_seed_helper(rng, seed)


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
    expected: Optional[float] = None,
) -> None:
    rng.seed(seed)
    state = rng.getstate()
    val = rng.random()
    assert val >= 0.0 and val < 1.0

    if expected is not None:
        assert val == expected

    assert type(rng)(seed).random() == val

    rng.setstate(state)
    assert rng.random() == val

    rng.seed(seed)
    assert rng.random() == val

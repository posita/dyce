# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from decimal import Decimal
from random import Random
from typing import Optional

import pytest

import dyce.rng
from dyce.rng import _RandSeed

__all__ = ()


# ---- Data ----------------------------------------------------------------------------


SEED_INT_128 = 0x6265656663616665
SEED_FLOAT = float(
    Decimal(
        "9856940084378475016744131457734599215371411366662962480265638551381775059468656635085733393811201634227995293393551923733235754825282073085472925752147516616452603904"
    ),
)
SEED_BYTES_128 = b"beefcafe"[::-1]
SEED_INT_192 = 0x646561646265656663616665
SEED_BYTES_192 = b"deadbeefcafe"[::-1]


# ---- Tests ---------------------------------------------------------------------------


def test_numpy_rng() -> None:
    pytest.importorskip("numpy.random", reason="requires numpy")
    assert hasattr(dyce.rng, "NumpyRandom")
    assert isinstance(dyce.rng.RNG, dyce.rng.NumpyRandom)


def test_numpy_rng_pcg64dxsm() -> None:
    numpy_random = pytest.importorskip("numpy.random", reason="requires numpy")

    if not hasattr(numpy_random, "PCG64DXSM"):
        pytest.skip("requires numpy.random.PCG64DXSM")

    rng = dyce.rng.NumpyRandom(numpy_random.PCG64DXSM())
    _test_w_seed_helper(rng, SEED_INT_128, 0.7903327469601987)
    _test_w_seed_helper(rng, SEED_FLOAT, 0.6018795857570297)
    _test_w_seed_helper(rng, SEED_BYTES_128, 0.5339952033746491)
    _test_w_seed_helper(rng, SEED_INT_192, 0.9912715409588355)
    _test_w_seed_helper(rng, SEED_BYTES_192, 0.13818265573158406)

    with pytest.raises(ValueError):
        _test_w_seed_helper(rng, object())  # type: ignore


def test_numpy_rng_pcg64() -> None:
    numpy_random = pytest.importorskip("numpy.random", reason="requires numpy")

    if not hasattr(numpy_random, "PCG64"):
        pytest.skip("requires numpy.random.PCG64")

    rng = dyce.rng.NumpyRandom(numpy_random.PCG64())
    _test_w_seed_helper(rng, SEED_INT_128, 0.9794491381144006)
    _test_w_seed_helper(rng, SEED_FLOAT, 0.8347478482621317)
    _test_w_seed_helper(rng, SEED_BYTES_128, 0.7800090883745199)
    _test_w_seed_helper(rng, SEED_INT_192, 0.28018439479392754)
    _test_w_seed_helper(rng, SEED_BYTES_192, 0.4814859325412144)

    with pytest.raises(ValueError):
        _test_w_seed_helper(rng, object())  # type: ignore


def test_numpy_rng_default() -> None:
    numpy_random = pytest.importorskip("numpy.random", reason="requires numpy")

    if not hasattr(numpy_random, "default_rng"):
        pytest.skip("requires numpy.random.default_rng")

    rng = dyce.rng.NumpyRandom(numpy_random.default_rng().bit_generator)
    _test_w_seed_helper(rng, SEED_INT_128)
    _test_w_seed_helper(rng, SEED_FLOAT)
    _test_w_seed_helper(rng, SEED_BYTES_128)
    _test_w_seed_helper(rng, SEED_INT_192)
    _test_w_seed_helper(rng, SEED_BYTES_192)

    with pytest.raises(ValueError):
        _test_w_seed_helper(rng, object())  # type: ignore


def _test_w_seed_helper(
    rng: Random,
    seed: _RandSeed,
    expected: Optional[float] = None,
) -> None:
    rng.seed(seed)
    state = rng.getstate()
    val = rng.random()
    assert val >= 0.0 and val < 1.0

    if expected is not None:
        assert expected == val

    rng.setstate(state)
    assert rng.random() == val

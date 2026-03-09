# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from abc import ABC
from random import Random
from typing import Any

from numerary.bt import beartype

__all__ = ("RNG",)


# ---- Types ---------------------------------------------------------------------------


_RandSeedT = int | float | str | bytes | bytearray | None


# ---- Data ----------------------------------------------------------------------------


DEFAULT_RNG: Random
RNG: Random


# ---- Classes -------------------------------------------------------------------------


try:
    from numpy.random import PCG64DXSM, BitGenerator, Generator, default_rng

    _BitGeneratorT = type[BitGenerator]

    class NumPyRandomBase(Random, ABC):
        r"""
        Base class for a [``#!python
        random.Random``](https://docs.python.org/3/library/random.html#random.Random)
        implementation that uses a [``#!python
        numpy.random.BitGenerator``](https://numpy.org/doc/stable/reference/random/bit_generators/index.html)
        under the covers. Motivated by
        [avrae/d20#7](https://github.com/avrae/d20/issues/7).

        The [initializer][rng.NumPyRandomBase.__init__] takes an optional *seed*, which is
        passed to
        [``NumPyRandomBase.bit_generator``][dyce.rng.NumPyRandomBase.bit_generator] via
        [``NumPyRandomBase.seed``][dyce.rng.NumPyRandomBase.seed] during construction.
        """

        bit_generator: _BitGeneratorT
        _generator: Generator

        @beartype
        def __init__(self, seed: _RandSeedT = None):
            # Parent calls self.seed(seed)
            super().__init__(seed)

        # ---- Overrides ---------------------------------------------------------------

        @beartype
        def getrandbits(self, k: int) -> int:
            # Adapted from the implementation for random.SystemRandom.getrandbits
            if k < 0:
                raise ValueError("number of bits must be non-negative")

            numbytes = (k + 7) // 8  # bits / 8 and rounded up
            x = int.from_bytes(self.randbytes(numbytes), "big")

            return x >> (numbytes * 8 - k)  # trim excess bits

        @beartype
        def getstate(self) -> tuple[Any, ...]:
            return (self._generator.bit_generator.state,)

        @beartype
        def randbytes(self, n: int) -> bytes:
            return self._generator.bytes(n)

        @beartype
        def random(self) -> float:
            return self._generator.random()

        @beartype
        def seed(self, a: object = ..., version: int = 2) -> None:
            self._generator = default_rng(self.bit_generator(a))

        @beartype
        def setstate(self, state: tuple[Any, ...]) -> None:
            (_state,) = state
            self._generator.bit_generator.state = _state

    class PCG64DXSMRandom(NumPyRandomBase):
        r"""
        A [``NumPyRandomBase``][dyce.rng.NumPyRandomBase] based on
        [``numpy.random.PCG64DXSM``](https://numpy.org/doc/stable/reference/random/bit_generators/pcg64dxsm.html#numpy.random.PCG64DXSM).
        """

        bit_generator = PCG64DXSM

    DEFAULT_RNG = PCG64DXSMRandom()
except ImportError:
    DEFAULT_RNG = Random()

RNG = DEFAULT_RNG

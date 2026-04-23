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

from abc import ABC, abstractmethod
from collections.abc import Hashable
from random import Random
from typing import Any

__all__ = ("RNG",)

_RandSeedT = int | float | str | bytes | bytearray | None

_DEFAULT_RNG: Random
RNG: Random

try:
    from numpy.random import PCG64DXSM, BitGenerator, Generator, default_rng

    _BitGeneratorT = type[BitGenerator]

    class NumPyRandomBase(Random, ABC):
        r"""
        Base class for a [`#!python random.Random`](https://docs.python.org/3/library/random.html#random.Random) implementation that uses a [`#!python numpy.random.BitGenerator`](https://numpy.org/doc/stable/reference/random/bit_generators/index.html) under the covers.
        Motivated by [avrae/d20#7](https://github.com/avrae/d20/issues/7).

        The [initializer][rng.NumPyRandomBase.__init__] takes an optional *seed*, which is passed to [`NumPyRandomBase.bit_generator`][dyce.rng.NumPyRandomBase.bit_generator] via [`NumPyRandomBase.seed`][dyce.rng.NumPyRandomBase.seed] during construction.
        """

        _generator: Generator

        def __init__(self, seed: object = None) -> None:
            # Parent calls self.seed(seed)
            super().__init__(seed)  # type: ignore[arg-type] # ty: ignore[invalid-argument-type]

        @property
        @abstractmethod
        def bit_generator(self) -> _BitGeneratorT: ...

        def getrandbits(self, k: int) -> int:
            # Adapted from the implementation for random.SystemRandom.getrandbits
            if k < 0:
                raise ValueError("number of bits must be non-negative")
            numbytes = (k + 7) // 8  # bits / 8 and rounded up
            x = int.from_bytes(self.randbytes(numbytes), "big")
            return x >> (numbytes * 8 - k)  # trim excess bits

        def getstate(self) -> tuple[Any, ...]:
            return (self._generator.bit_generator.state,)

        def randbytes(self, n: int) -> bytes:
            return self._generator.bytes(n)

        def random(self) -> float:
            return self._generator.random()

        def seed(
            self,
            a: object | None = None,
            version: int = 2,  # noqa: ARG002
        ) -> None:
            if a is None or isinstance(a, (bool, int)):
                seed = a
            else:
                seed = abs(hash(a) if isinstance(a, Hashable) else id(a))
            self._generator = default_rng(self.bit_generator(seed))

        def setstate(self, state: tuple[Any, ...]) -> None:
            (state_item,) = state
            self._generator.bit_generator.state = state_item

    class PCG64DXSMRandom(NumPyRandomBase):
        r"""
        A [`NumPyRandomBase`][dyce.rng.NumPyRandomBase] based on [`numpy.random.PCG64DXSM`](https://numpy.org/doc/stable/reference/random/bit_generators/pcg64dxsm.html#numpy.random.PCG64DXSM).
        """

        @property
        def bit_generator(self) -> _BitGeneratorT:
            return PCG64DXSM

    _DEFAULT_RNG = PCG64DXSMRandom()
except ImportError:
    _DEFAULT_RNG = Random()

RNG = _DEFAULT_RNG

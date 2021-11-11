# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from abc import ABC
from random import Random
from sys import version_info
from typing import NewType, Sequence, Type, Union

from numerary.bt import beartype

__all__ = ("RNG",)


# ---- Types ---------------------------------------------------------------------------


_RandState = NewType("_RandState", object)
_RandSeed = Union[None, int, Sequence[int]]


# ---- Data ----------------------------------------------------------------------------


RNG: Random
DEFAULT_RNG: Random


# ---- Classes -------------------------------------------------------------------------


try:
    from numpy.random import PCG64DXSM, BitGenerator, Generator, default_rng

    _BitGeneratorT = Type[BitGenerator]

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

        if version_info < (3, 11):

            @beartype
            def __new__(cls, seed: _RandSeed = None):
                r"""
                Because ``#!python random.Random`` is broken in versions <3.11, ``#!python
                random.Random``’s vanilla implementation cannot accept non-hashable
                values as the first argument. For example, it will reject lists of
                ``#!python int``s as *seed*. This implementation of ``#!python __new__``
                fixes that.

                See:

                * https://bugs.python.org/issue44260
                * https://bugs.python.org/issue40346#msg402508
                """
                return super(NumPyRandomBase, cls).__new__(cls)

        @beartype
        def __init__(self, seed: _RandSeed = None):
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
        # TODO(posita): See <https://github.com/python/typeshed/issues/6063>
        def getstate(self) -> _RandState:  # type: ignore [override]
            return _RandState(self._generator.bit_generator.state)

        @beartype
        def randbytes(self, n: int) -> bytes:
            return self._generator.bytes(n)

        @beartype
        def random(self) -> float:
            return self._generator.random()

        @beartype
        def seed(  # type: ignore [override]
            self,
            a: _RandSeed,
            version: int = 2,
        ) -> None:
            self._generator = default_rng(self.bit_generator(a))

        @beartype
        def setstate(  # type: ignore [override]
            self,
            # TODO(posita): See <https://github.com/python/typeshed/issues/6063>
            state: _RandState,
        ) -> None:
            self._generator.bit_generator.state = state

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

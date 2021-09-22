# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from random import Random
from typing import Any, NewType, Optional, Union

__all__ = ("RNG",)


# ---- Types ---------------------------------------------------------------------------


_RandSeed = Union[int, float, str, bytes, bytearray]
_RandState = NewType("_RandState", Any)


# ---- Data ----------------------------------------------------------------------------


RNG: Random = Random()


try:
    import numpy.random
    from numpy.random import BitGenerator, Generator

    class NumpyRandom(Random):
        r"""
        Defines a [``!#python
        random.Random``](https://docs.python.org/3/library/random.html#random.Random)
        implementation that accepts and uses a [``!#python
        numpy.random.BitGenerator``](https://numpy.org/doc/stable/reference/random/bit_generators/index.html)
        under the covers. Motivated by
        [avrae/d20#7](https://github.com/avrae/d20/issues/7).
        """

        def __init__(self, bit_generator: BitGenerator):
            self._g = Generator(bit_generator)

        def random(self) -> float:
            return self._g.random()

        def seed(self, a: Optional[_RandSeed], version: int = 2) -> None:
            if a is not None and not isinstance(a, (int, float, str, bytes, bytearray)):
                raise ValueError(f"unrecognized seed type ({type(a)})")

            bg_type = type(self._g.bit_generator)

            if a is None:
                self._g = Generator(bg_type())
            else:
                # This is somewhat fragile and may not be the best approach. It uses
                # `random.Random` to generate its own state from the seed in order to
                # maintain compatibility with accepted seed types. (NumPy only accepts
                # ints whereas the standard library accepts ints, floats, bytes, etc.).
                # That state consists of a 3-tuple: (version: int, internal_state:
                # tuple[int], gauss_next: float) at least for for versions through 3 (as
                # of this writing). We feed internal_state as the seed for the NumPy
                # BitGenerator.
                version, internal_state, _ = Random(a).getstate()
                self._g = Generator(bg_type(internal_state))

        def getstate(self) -> _RandState:
            return _RandState(self._g.bit_generator.state)

        def setstate(self, state: _RandState) -> None:
            self._g.bit_generator.state = state

    if hasattr(numpy.random, "PCG64DXSM"):
        RNG = NumpyRandom(numpy.random.PCG64DXSM())
    elif hasattr(numpy.random, "PCG64"):
        RNG = NumpyRandom(numpy.random.PCG64())
    elif hasattr(numpy.random, "default_rng"):
        RNG = NumpyRandom(numpy.random.default_rng().bit_generator)
except ImportError:
    pass

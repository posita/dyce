# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

from typing import Tuple, Union

from .h import *  # noqa: F401,F403
from .p import *  # noqa: F401,F403
from .r import *  # noqa: F401,F403
from .types import *  # noqa: F401,F403

__version__: Union[
    Tuple[int, int, str],
    Tuple[int, int, str, str],
    Tuple[int, int, int],
    Tuple[int, int, int, str],
    Tuple[int, int, int, str, str],
]
__vers_str__: str

try:
    # See <https://www.moritzkoerber.com/posts/versioning-with-setuptools_scm/>
    from ._version import version as __vers_str__
    from ._version import version_tuple as __version__
except Exception:
    __vers_str__ = "0.0.unknown version"
    __version__ = (0, 0, "unknown version")

__all__ = ()

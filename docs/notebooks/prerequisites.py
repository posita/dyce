# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

"""Notebook prerequisite installer.

Works in regular Jupyter (delegates to pip) and JupyterLite (delegates to piplite).
Callers should ``await`` the result; IPython supports top-level ``await`` in both
environments.
"""

import importlib.util
from collections.abc import Callable
from typing import Any

get_ipython: Callable[[], Any]


async def install_if_missing(
    *packages: "tuple[str, str] | tuple[str, str, str]",
) -> None:
    """Install packages that are not already importable.

    Each package is either a ``(import_name, install_spec)`` pair — the same spec is
    used for both pip and piplite — or a ``(import_name, pip_spec, piplite_spec)``
    triple for cases where the version specifier must differ between environments (e.g.
    dev wheels whose local segment confuses piplite's version resolver).
    """
    try:
        import piplite  # type: ignore[missing-import] # pyrefly: ignore[missing-import] # ty: ignore[unresolved-import]

        in_piplite = True
    except ImportError:
        in_piplite = False

    to_install: list[str] = []
    for pkg in packages:
        if importlib.util.find_spec(pkg[0]) is None:
            spec = pkg[2] if len(pkg) > 2 and in_piplite else pkg[1]  # ty: ignore[index-out-of-bounds]
            to_install.append(spec)

    if not to_install:
        return

    if in_piplite:
        for spec in to_install:
            await piplite.install(spec, keep_going=True)  # pyrefly: ignore[unbound-name]
    else:
        get_ipython().run_line_magic(  # type: ignore[name-defined] # noqa: F821
            "pip",
            "install --quiet " + " ".join(f"'{s}'" for s in to_install),
        )

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

import logging
import os
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from collections.abc import Sequence
from pathlib import Path

_LOGGER = logging.getLogger("mkdocs.hooks")


def on_pre_build(**_kwargs: object) -> None:
    _uv_run(("make", "-C", "docs-src", "-j", "4"))


def _uv_run(cmd: Sequence[str]) -> None:
    uv_cmd = ["uv", "run", "--group", "docs"]
    venv_path = Path(os.getenv("VIRTUAL_ENV", "")).resolve()
    mkdocs_path = Path(sys.argv[0]).resolve()
    if venv_path.stem.startswith(".venv") and mkdocs_path.is_relative_to(venv_path):
        uv_cmd.append("--active")
    uv_cmd.extend(cmd)
    _LOGGER.info("running %s", " ".join(uv_cmd))
    subprocess.run(uv_cmd, check=True)  # ruff: ignore[subprocess-without-shell-equals-true]

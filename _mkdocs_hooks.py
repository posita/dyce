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
import re
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
import tomllib
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

_LOGGER = logging.getLogger("mkdocs.hooks")

_BUNDLED_PKG_NAMES = ("optype",)


def on_pre_build(**_kwargs: object) -> None:
    _uv_run(("make", "-C", "docs-src", "-j", "4"))


def on_post_build(config: "MkDocsConfig", **_kwargs: object) -> None:
    cmd = ["uv", "build", "--wheel"]
    _LOGGER.info("running %s", " ".join(cmd))
    subprocess.run(cmd, check=True)  # ruff: ignore[subprocess-without-shell-equals-true]

    cmd = [
        "jupyter",
        "lite",
        "build",
        "--debug",
        "--output-dir",
        f"{config.site_dir}/jupyter",
    ]
    wheels: list[Path | str] = [_get_latest_pkg_wheel_from_dist()]
    wheels.extend(_bundled_wheel_urls(_BUNDLED_PKG_NAMES))
    # Fuck you, Jupyter Lite, for costing me hours to work through your lies. (See
    # <https://github.com/jupyterlite/jupyterlite/issues/1563>.)
    for wheel in wheels:
        cmd.extend(("--piplite-wheels", str(wheel)))
    _uv_run(cmd)


def _bundled_wheel_urls(pkg_names: Iterable[str]) -> Iterator[str]:
    uv_lock_path = Path("uv.lock")
    for pkg_name in pkg_names:
        with uv_lock_path.open("rb") as f:
            uv_lock = tomllib.load(f)
        pkg = next(p for p in uv_lock["package"] if p["name"] == pkg_name)
        try:
            yield next(
                w["url"]
                for w in pkg.get("wheels", [])
                if re.search(r"\bnone-any\b", w["url"])
            )
        except StopIteration:
            raise RuntimeError(
                f"no none-any wheel for {pkg!r} found in {uv_lock_path}"
            ) from None


def _get_latest_pkg_wheel_from_dist() -> Path:
    return max(Path("dist").glob("dyce*-none-any.whl"), key=os.path.getmtime)


def _uv_run(cmd: Sequence[str]) -> None:
    uv_cmd = ["uv", "run", "--group", "docs"]
    venv_path = Path(os.getenv("VIRTUAL_ENV", "")).resolve()
    mkdocs_path = Path(sys.argv[0]).resolve()
    if venv_path.stem.startswith(".venv") and mkdocs_path.is_relative_to(venv_path):
        uv_cmd.append("--active")
    uv_cmd.extend(cmd)
    _LOGGER.info("running %s", " ".join(uv_cmd))
    subprocess.run(uv_cmd, check=True)  # ruff: ignore[subprocess-without-shell-equals-true]

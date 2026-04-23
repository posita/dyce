import logging
import pathlib  # noqa: TC003
import shutil
import subprocess  # noqa: S404

_LOGGER = logging.getLogger(__name__)


def on_pre_build(**_kwargs: object) -> None:
    # Use copy2 to preserve modification times to avoid a feedback loop with
    # `mkdocs serve --livereload`.
    shutil.copy2("README.md", "docs/index.md")
    shutil.copy2("LICENSE", "docs/license.md")


def on_post_build(config: dict, **_kwargs: object) -> None:
    cmd = ["uv", "build", "--wheel"]
    _LOGGER.debug("running %s", " ".join(cmd))
    subprocess.run(cmd, check=True)  # noqa: S603
    cmd = [
        "jupyter",
        "lite",
        "build",
        "--debug",
        "--output-dir",
        f"{config['site_dir']}/jupyter",
    ]
    wheels: list[pathlib.Path] = []
    # wheels.extend(pathlib.Path("dist").glob("dyce*.whl"))  # noqa: ERA001
    for wheel in wheels:
        str(wheel)
        cmd.extend(("--piplite-wheel", str(wheel)))
    _LOGGER.debug("running %s", " ".join(cmd))
    subprocess.run(cmd, check=True)  # noqa: S603

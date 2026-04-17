import importlib.metadata
import logging
import pathlib
import re
import shutil
import subprocess  # noqa: S404

_LOGGER = logging.getLogger(__name__)

_RAW_VERSION = importlib.metadata.version("dyce")
# Dev/dirty builds (e.g. "0.1.0.dev5+gabcdef") fall back to "main".
_IS_RELEASE = "+" not in _RAW_VERSION and ".dev" not in _RAW_VERSION
_GIT_REF = f"v{_RAW_VERSION}" if _IS_RELEASE else "main"
# mike deploys under "major.minor"; dev builds link to "latest".
_parts = _RAW_VERSION.split(".")
_DOCS_VERSION = f"{_parts[0]}.{_parts[1]}" if _IS_RELEASE else "latest"


def on_page_markdown(markdown: str, **_kwargs: object) -> str:
    markdown = re.sub(
        r"<!-- mkdocs:hide:start -->.*?<!-- mkdocs:hide:end -->",
        "",
        markdown,
        flags=re.DOTALL,
    )
    return markdown.replace("{dyce_git_ref}", _GIT_REF)


def on_pre_build(**_kwargs: object) -> None:
    readme = pathlib.Path("README.md").read_text("utf_8")
    index = readme
    # Replace 'main' with the version-specific git ref in GitHub source URLs.
    index = re.sub(
        r"(https?://(?:raw\.githubusercontent\.com|github\.com)/posita/dyce/(?:blob/|tree/)?)main\b",
        rf"\g<1>{_GIT_REF}",
        index,
    )
    # Replace 'latest' with the docs version in docs site URLs.
    index = index.replace(
        "https://posita.github.io/dyce/latest/",
        f"https://posita.github.io/dyce/{_DOCS_VERSION}/",
    )
    # For release builds, restore version-specific shields.io badge URLs and PyPI link.
    if _IS_RELEASE:
        index = re.sub(
            r"(https://img\.shields\.io/pypi/[^/]+/dyce)(\.svg)",
            rf"\g<1>/{_RAW_VERSION}\g<2>",
            index,
        )
        index = re.sub(
            r"(https://pypi\.org/project/dyce/)(?=\))",
            rf"\g<1>{_RAW_VERSION}/",
            index,
        )
    index_path = pathlib.Path("docs/index.md")
    # Only write if changed to avoid a feedback loop with `mkdocs serve --livereload`.
    if not index_path.exists() or index_path.read_text("utf_8") != index:
        index_path.write_text(index, "utf_8")

    # Use copy2 to preserve modification times to avoid a feedback loop with
    # `mkdocs serve --livereload`.
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
    wheels.extend(pathlib.Path("dist").glob("dyce*.whl"))
    for wheel in wheels:
        cmd.extend(("--piplite-wheel", str(wheel)))
    _LOGGER.warning("running %s", " ".join(cmd))
    subprocess.run(cmd, check=True)  # noqa: S603

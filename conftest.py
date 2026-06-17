import platform
from os import environ
from pathlib import Path

import pytest

# Pin because without width argument, H.format bars scale to COLUMNS, and tox overrides
# COLUMNS for some reason.
environ["COLUMNS"] = ""


@pytest.fixture(autouse=True)
def suppress_dyce_warnings() -> None:
    import warnings

    from dyce import TruncationWarning

    # Lazy imports are necessary so that we don't inadvertently import library code
    # before plugins (e.g,. coverage) can work their magic
    from dyce.lifecycle import ExperimentalWarning

    warnings.filterwarnings("ignore", category=ExperimentalWarning)
    warnings.filterwarnings("ignore", category=TruncationWarning)


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,  # noqa: ARG001
) -> bool:
    # nb_*.py are jupytext notebook sources. Their top-level await makes them
    # unimportable. plot_*.py have some doc-specific imports (e.g., jinja2) that aren't
    # (and as-of-yet shouldn't) matter for testing.
    if collection_path.match("docs/assets/nb_*.py") or collection_path.match(
        "docs/assets/plot_*.py"
    ):
        return True
    if platform.python_implementation() == "PyPy":
        # Skip these because Matplotlib is not compatible with PyPy. See
        # <http://packages.pypy.org/>.
        return collection_path.match("docs/assets/") or collection_path.name == "viz.py"
    return False

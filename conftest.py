import platform
from os import environ
from pathlib import Path

import pytest

# Pin because without width argument, H.format bars scale to COLUMNS, and tox overrides
# COLUMNS for some reason.
environ["COLUMNS"] = ""


@pytest.fixture(autouse=True)  # ruff: ignore[pytest-fixture-autouse]
def suppress_dyce_warnings() -> None:
    import warnings

    from dyce import TruncationWarning

    # Lazy imports are necessary so that we don't inadvertently import library code
    # before plugins (e.g,. coverage) can work their magic
    from dyce.lifecycle import ExperimentalWarning

    warnings.simplefilter("ignore", ExperimentalWarning)
    warnings.simplefilter("ignore", TruncationWarning)


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,  # ruff: ignore[unused-function-argument]
) -> bool:
    if (
        # Auto-generated doc-specific files
        collection_path.match("docs/index.md")
        or collection_path.match("docs/license.md")
        or collection_path.match("docs/jupyter")
        # The top-level await makes nb_*.py unimportable
        or collection_path.match("docs-src/nb_*.py")
        # plot_*.py have some doc-specific imports (e.g., jinja2) that aren't (and
        # as-of-yet shouldn't) matter for testing
        or collection_path.match("docs-src/plot_*.py")
    ):
        return True
    if platform.python_implementation() == "PyPy":
        # Skip these because Matplotlib is not compatible with PyPy. See
        # <http://packages.pypy.org/>.
        return collection_path.match("docs-src/") or collection_path.match(
            "dyce/viz/matplotlib.py"
        )
    return False

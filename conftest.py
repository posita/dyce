import platform
from pathlib import Path

import pytest


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,  # noqa: ARG001
) -> bool:
    if platform.python_implementation() == "PyPy":
        # Skip these because Matplotlib is not compatible with PyPy. See
        # <http://packages.pypy.org/>.
        return collection_path.match("docs/assets/") or collection_path.name == "viz.py"
    else:
        # Do not skip
        return False

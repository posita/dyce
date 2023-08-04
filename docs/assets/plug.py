# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import importlib.machinery
import importlib.util
import pathlib
from typing import Any, Callable

__all__ = ("import_plug",)


def import_plug(arg: str, pfx: str) -> tuple[str, Callable[[str], Any]]:
    try:
        my_dir = pathlib.Path(__file__).parent
        mod_path = str(my_dir.joinpath(f"{pfx}_{arg}.py"))
        loader = importlib.machinery.SourceFileLoader(arg, mod_path)
        spec = importlib.util.spec_from_loader(arg, loader)
        assert spec
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        do_it = mod.do_it
    except (
        AssertionError,
        AttributeError,
        FileNotFoundError,
        ImportError,
        SyntaxError,
    ) as exc:
        raise argparse.ArgumentTypeError(f'unable to load "{arg}" ({exc})')
    else:
        return (arg, do_it)

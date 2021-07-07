# -*- encoding: utf-8 -*-
# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import pathlib
from typing import Callable, Tuple

__all__ = ("import_plug",)


def import_plug(arg: str, pfx: str) -> Tuple[str, Callable[[str], None]]:

    try:
        my_dir = pathlib.Path(__file__).parent
        mod_path = str(my_dir.joinpath("{}_{}.py".format(pfx, arg)))
        loader = importlib.machinery.SourceFileLoader(arg, mod_path)
        spec = importlib.util.spec_from_loader(arg, loader)
        assert spec
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        do_it = mod.do_it  # type: ignore
    except (
        AssertionError,
        AttributeError,
        FileNotFoundError,
        ImportError,
        SyntaxError,
    ) as exc:
        raise argparse.ArgumentTypeError('unable to load "{}" ({})'.format(arg, exc))
    else:
        return (arg, do_it)

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
from functools import partial
from typing import Any, Mapping

from plug import import_plug

from dyce.viz import Digraph

PARSER = argparse.ArgumentParser(description="Generate SVG files for documentation")
# TODO(posita): Get rid of all instances of gh here, below, and with Makefile and
# *_gh.png once this dumpster fire
# <https://github.community/t/support-theme-context-for-images-in-light-vs-dark-mode/147981>
# gets resolved
PARSER.add_argument("-s", "--style", choices=("dark", "light", "gh"), default="light")
PARSER.add_argument("fig", type=partial(import_plug, pfx="graph"))

COLORS = {
    "dark": ["Azure", "LightBlue", "LightPink"],
    "light": ["DarkSlateGray", "MediumBlue", "MediumVioletRed"],
}


def digraph(style: str, **kw_attrs: Mapping[str, Mapping[str, Any]]) -> Digraph:
    g = Digraph()
    g.attr(
        bgcolor="transparent",
        color=COLORS[style][0],
        fontcolor=COLORS[style][0],
        fontname="Helvetica",
    )
    g.attr(
        "node",
        shape="box",
        color=COLORS[style][0],
        fontcolor=COLORS[style][0],
        fontname="Helvetica",
    )
    g.attr(
        "edge",
        color=COLORS[style][0],
        fontcolor=COLORS[style][0],
        fontname="Courier New",
    )

    for kw, attrs in kw_attrs.items():
        g.attr(kw if kw else None, **attrs)

    return g


def _main() -> None:
    import graphviz

    args = PARSER.parse_args()
    mod_name, mod_do_it = args.fig
    svg_path = "graph_{}_{}".format(mod_name, args.style)
    g: graphviz.Digraph = mod_do_it(args.style)
    print("saving {}".format(svg_path))
    g.render(filename=svg_path, format="svg")


if __name__ == "__main__":
    _main()

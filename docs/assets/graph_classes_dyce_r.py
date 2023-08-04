# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from graph import COLORS, Dot


def do_it(style: str) -> Optional[Dot]:
    from graphviz import Source

    try:
        from pygraphviz import AGraph
    except ImportError as exc:
        logging.critical(exc)

        return None

    r_path = Path() / ".." / ".." / "dyce" / "r.py"
    cmd = (
        "pyreverse",
        "--only-classnames",
        "--output=dot",
        f"--project=dyce_r_{style}",
        str(r_path),
    )
    logging.info(" ".join(cmd))
    subprocess.run(cmd)

    src_g = AGraph()
    src_g.read(f"classes_dyce_r_{style}.dot")
    os.remove(f"classes_dyce_r_{style}.dot")

    src_g.remove_node("dyce.r.CoalesceMode")
    src_g.remove_node("dyce.r.Roll")
    src_g.remove_node("dyce.r.RollOutcome")

    for n in src_g.nodes():
        if n.endswith("WalkerVisitor"):
            src_g.remove_node(n)

    src_g.graph_attr.update(
        bgcolor="transparent",
        color=COLORS[style]["line"],
        fontcolor=COLORS[style]["line"],
        fontname="Helvetica",
    )

    for e in src_g.edges_iter():
        e.attr.update(
            color=COLORS[style]["line"],
            fontcolor=COLORS[style]["line"],
            fontname="Courier New",
        )

    for n in src_g.nodes_iter():
        n.attr.update(
            color=COLORS[style]["line"],
            fontcolor=COLORS[style]["line"],
            fontname="Helvetica",
        )

    s = Source(src_g.string_nop())

    return s

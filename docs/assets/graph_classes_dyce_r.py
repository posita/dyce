# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
import subprocess  # noqa: S404
from pathlib import Path

from graph import COLORS, Dot

_LOGGER = logging.getLogger(__name__)


def do_it(style: str) -> Dot | None:
    from graphviz import Source

    try:
        from pygraphviz import AGraph
    except ImportError as exc:
        _LOGGER.critical(exc)

        return None

    r_path = Path() / ".." / ".." / "dyce" / "r.py"
    cmd = (
        "pyreverse",
        "--only-classnames",
        "--output=dot",
        f"--project=dyce_r_{style}",
        str(r_path),
    )
    _LOGGER.info(" ".join(cmd))
    subprocess.run(cmd)  # noqa: S603

    src_g = AGraph()
    src_g.read(f"classes_dyce_r_{style}.dot")
    Path(f"classes_dyce_r_{style}.dot").unlink()

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

    return Source(src_g.string_nop())

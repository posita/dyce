# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import argparse
import html
import logging
from collections.abc import Mapping as MappingC
from functools import partial
from typing import Any, Iterator, Mapping, Optional, Union

from numerary.bt import beartype
from plug import import_plug

from dyce import R
from dyce.r import (
    BinarySumOpRoller,
    NarySumOpRoller,
    PoolRoller,
    RepeatRoller,
    Roll,
    RollerWalkerVisitor,
    RollOutcome,
    RollOutcomeWalkerVisitor,
    RollWalkerVisitor,
    SelectionRoller,
    UnarySumOpRoller,
    ValueRoller,
    walk,
)

try:
    from graphviz import Digraph
    from graphviz.dot import Dot
except ImportError:
    Digraph = Any
    Dot = Any

__all__ = ()


# ---- Types ---------------------------------------------------------------------------


try:
    from typing import Annotated

    from beartype.vale import Is

    _GraphvizAttrTypeVals = ("edge", "graph", "node")
    _GraphvizAttrTypeT = Annotated[str, Is[lambda text: text in _GraphvizAttrTypeVals]]
except ImportError:
    _GraphvizAttrTypeT = str  # type: ignore [misc]


# ---- Data ----------------------------------------------------------------------------

COLORS = {
    "light": {
        "line": "DarkSlateGray",
        "purple": "Indigo",
        "blue": "MediumBlue",
        "green": "MediumSeaGreen",
        "yellow": "Goldenrod",
        "orange": "DarkSalmon",
        "red": "MediumVioletRed",
    },
    "dark": {
        "line": "Azure",
        "purple": "Lavender",
        "blue": "LightBlue",
        "green": "LightGreen",
        "yellow": "LightGoldenRodYellow",
        "orange": "LightSalmon",
        "red": "LightPink",
    },
}

_PARSER = argparse.ArgumentParser(description="Generate SVG files for documentation")
_PARSER.add_argument("-s", "--style", choices=("dark", "light"), default="light")
_PARSER.add_argument(
    "-l",
    "--log-level",
    choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"),
    default="INFO",
)
_PARSER.add_argument("fig", type=partial(import_plug, pfx="graph"))

_VALUE_LEN = 24


# ---- Classes -------------------------------------------------------------------------


class GraphvizObjectResolver:
    @beartype
    def __init__(self):
        self._serial = 1
        self._names: dict[int, str] = {}

    @beartype
    def attrs_for_obj(
        self,
        obj: Union[R, Roll, RollOutcome],
        attr_type: _GraphvizAttrTypeT,
    ) -> Optional[Mapping[str, str]]:
        annotation = obj.annotation

        if not isinstance(annotation, MappingC):
            return None

        attrs = annotation.get(attr_type)

        if not isinstance(attrs, MappingC):
            return None

        return attrs

    @beartype
    def name_for_obj(self, obj: Union[R, Roll, RollOutcome]) -> str:
        if id(obj) not in self._names:
            self._names[id(obj)] = f"{type(obj).__name__}-{self._serial}"
            self._serial += 1

        return self._names[id(obj)]


class GraphizObjectResolverMixin:
    @beartype
    def __init__(self, g: Digraph, resolver: GraphvizObjectResolver):
        self._g = g
        self._resolver = resolver

    @property
    def g(self) -> Digraph:
        return self._g

    @property
    def resolver(self) -> Digraph:
        return self._resolver


class InterObjectVisitor(GraphizObjectResolverMixin, RollWalkerVisitor):
    @beartype
    def on_roll(self, roll: Roll, parents: Iterator[Roll]) -> None:
        edge_attrs = self.resolver.attrs_for_obj(roll, "edge") or {}
        self.g.edge(
            self.resolver.name_for_obj(roll),
            self.resolver.name_for_obj(roll.r),
            label="r",
            **edge_attrs,
        )

        for i, roll_outcome in enumerate(roll):
            edge_attrs = self.resolver.attrs_for_obj(roll_outcome, "edge") or {}
            self.g.edge(
                self.resolver.name_for_obj(roll),
                self.resolver.name_for_obj(roll_outcome),
                label=f"[{i}]",
                **edge_attrs,
            )


class RollClusterVisitor(GraphizObjectResolverMixin, RollWalkerVisitor):
    @beartype
    def on_roll(self, roll: Roll, parents: Iterator[Roll]) -> None:
        node_attrs = self.resolver.attrs_for_obj(roll, "node") or {}
        self.g.node(
            self.resolver.name_for_obj(roll),
            label=f"<<b>{type(roll).__name__}</b>>",
            **node_attrs,
        )

        for i, source_roll in enumerate(roll.source_rolls):
            edge_attrs = self.resolver.attrs_for_obj(source_roll, "edge") or {}
            self.g.edge(
                self.resolver.name_for_obj(roll),
                self.resolver.name_for_obj(source_roll),
                label=f"sources[{i}]",
                **edge_attrs,
            )


class RollerClusterVisitor(GraphizObjectResolverMixin, RollerWalkerVisitor):
    @beartype
    def on_roller(self, r: R, parents: Iterator[R]) -> None:
        node_attrs = self.resolver.attrs_for_obj(r, "node") or {}

        if isinstance(r, PoolRoller):
            label = f"<<b>{type(r).__name__}</b>>"
        elif isinstance(r, RepeatRoller):
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">n={r.n!r}</font>>'
        elif isinstance(r, SelectionRoller):
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">which={r.which!r}</font>>'
        elif isinstance(r, ValueRoller):
            value = _truncate(repr(r.value), is_html=True)
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">value={value}</font>>'
        elif isinstance(r, (BinarySumOpRoller)):
            if hasattr(r.bin_op, "__name__"):
                bin_op = r.bin_op.__name__
            else:
                bin_op = repr(r.bin_op)

            bin_op = _truncate(bin_op, is_html=True)
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">bin_op={bin_op}</font>>'
        elif isinstance(r, (UnarySumOpRoller)):
            if hasattr(r.un_op, "__name__"):
                un_op = r.un_op.__name__
            else:
                un_op = repr(r.un_op)

            un_op = _truncate(un_op, is_html=True)
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">un_op={un_op}</font>>'
        elif isinstance(r, (NarySumOpRoller)):
            if hasattr(r.op, "__name__"):
                op = r.op.__name__
            else:
                op = repr(r.op)

            op = _truncate(op, is_html=True)
            label = f'<<b>{type(r).__name__}</b><br/><font face="Courier New">op={op}</font>>'
        else:
            label = f"<<b>{type(r).__name__}</b>>"

        self.g.node(self.resolver.name_for_obj(r), label=label, **node_attrs)

        for i, source_roller in enumerate(r.sources):
            edge_attrs = self.resolver.attrs_for_obj(source_roller, "edge") or {}
            self.g.edge(
                self.resolver.name_for_obj(r),
                self.resolver.name_for_obj(source_roller),
                label=f"sources[{i}]",
                **edge_attrs,
            )


class RollOutcomeClusterVisitor(GraphizObjectResolverMixin, RollOutcomeWalkerVisitor):
    @beartype
    def on_roll_outcome(
        self, roll_outcome: RollOutcome, parents: Iterator[RollOutcome]
    ) -> None:
        node_attrs = self.resolver.attrs_for_obj(roll_outcome, "node")
        node_attrs = (
            {"style": "dotted"}
            if roll_outcome.value is None and node_attrs is None
            else node_attrs or {}
        )
        self.g.node(
            self.resolver.name_for_obj(roll_outcome),
            label=f'<<b>{type(roll_outcome).__name__}</b><br/><font face="Courier New">value={roll_outcome.value}</font>>',
            **node_attrs,
        )

        for i, source_roll_outcome in enumerate(roll_outcome.sources):
            edge_attrs = self.resolver.attrs_for_obj(source_roll_outcome, "edge") or {}
            self.g.edge(
                self.resolver.name_for_obj(roll_outcome),
                self.resolver.name_for_obj(source_roll_outcome),
                label=f"sources[{i}]",
                **edge_attrs,
            )


# ---- Functions -----------------------------------------------------------------------


@beartype
def digraph(style: str, **kw_attrs: Mapping[str, Mapping[str, Any]]) -> Digraph:
    g = Digraph()
    g.attr(
        bgcolor="transparent",
        color=COLORS[style]["line"],
        fontcolor=COLORS[style]["line"],
        fontname="Helvetica",
    )
    g.attr(
        "node",
        shape="box",
        color=COLORS[style]["line"],
        fontcolor=COLORS[style]["line"],
        fontname="Helvetica",
    )
    g.attr(
        "edge",
        color=COLORS[style]["line"],
        fontcolor=COLORS[style]["line"],
        fontname="Courier New",
    )

    for kw, attrs in kw_attrs.items():
        g.attr(kw if kw else None, **attrs)

    return g


@beartype
def graphviz_walk(
    g: Digraph,
    obj: Union[R, Roll, RollOutcome],
) -> None:
    resolver = GraphvizObjectResolver()
    walk(obj, InterObjectVisitor(g, resolver))

    with g.subgraph(name="cluster_rolls") as c:
        c.attr(label="<<i>Roll Tree</i>>", style="dotted")
        walk(obj, RollClusterVisitor(c, resolver))

    with g.subgraph(name="cluster_rollers") as c:
        c.attr(label="<<i>Roller Tree</i>>", style="dotted")
        walk(obj, RollerClusterVisitor(c, resolver))

    with g.subgraph(name="cluster_roll_outcomes") as c:
        c.attr(label="<<i>Roll Outcomes</i>>", style="dotted")
        walk(obj, RollOutcomeClusterVisitor(c, resolver))


@beartype
def _truncate(value: str, value_len: int = _VALUE_LEN, is_html: bool = False) -> str:
    value = value if len(value) <= value_len else (value[: value_len - 3] + "...")

    return html.escape(value) if is_html else value


@beartype
def _main() -> None:
    args = _PARSER.parse_args()
    logging.getLogger().setLevel(args.log_level)
    mod_name, mod_do_it = args.fig
    svg_path = f"graph_{mod_name}_{args.style}"
    g: Optional[Dot] = mod_do_it(args.style)

    if g is None:
        logging.warning(f"nothing generated for {svg_path}; skipping")
    else:
        print(f"saving {svg_path}")
        g.render(filename=svg_path, cleanup=True, format="svg")


# ---- Initialization ------------------------------------------------------------------


if __name__ == "__main__":
    _main()

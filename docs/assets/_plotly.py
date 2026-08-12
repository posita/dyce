# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

r"""
Companion to _plot.py, for generating interactive figures as HTML fragments instead of static images.
Emitted fragments depend on plotly.js.
"""

import argparse
import logging
from collections.abc import Callable
from pathlib import Path

from dyce.viz_plotly import PlotSpec, figure_from_spec

__all__ = ("main",)

FigCallbackT = Callable[[], PlotSpec]

DEFAULT_HEIGHT = "480px"

_PARSER = argparse.ArgumentParser(
    description="Generate interactive figure fragments for documentation"
)
_PARSER.add_argument(
    "-d",
    "--output-dir",
    type=Path,
    metavar="PATH",
    default=Path.cwd(),
    help="the directory in which to save the output fragment (default is .)",
)
_PARSER.add_argument(
    "-f",
    "--output-file",
    type=Path,
    metavar="PATH",
    help="the file to which to save the output fragment (relative to -d if not absolute) (default is an HTML file constructed from name)",
)
_PARSER.add_argument(
    "--log-level",
    default="WARNING",
    metavar="LEVEL",
    help="logging verbosity: DEBUG|INFO|WARNING|ERROR|CRITICAL (default: WARNING)",
)
_LOGGER = logging.getLogger(__name__)


def main(fig_callback: FigCallbackT, args: argparse.Namespace | None = None) -> None:
    import sys
    import warnings

    from dyce.lifecycle import ExperimentalWarning

    warnings.filterwarnings("ignore", category=ExperimentalWarning)
    args = args or _PARSER.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )
    name = Path(sys.argv[0]).stem
    output_file = Path(f"{name}.html") if not args.output_file else args.output_file
    output_path = args.output_dir.resolve().joinpath(output_file)

    _LOGGER.debug("calling %r", fig_callback)
    spec = fig_callback()
    fig = figure_from_spec(spec)
    # Plotly.py otherwise serializes its large default template into every
    # fragment. The documentation supplies its own transparent presentation.
    fig.update_layout(template="none")
    fragment = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=f"{name}-figure",  # for keeping output byte-stable
        default_width="100%",
        default_height=DEFAULT_HEIGHT,  # absolute height because 100% would resolve to zero
        config=spec.config,
    )
    _LOGGER.info("saving %s", output_path)
    output_path.write_text(fragment + "\n")

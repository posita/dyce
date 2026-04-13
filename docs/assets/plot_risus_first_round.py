# noqa: INP001 # =======================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from argparse import Namespace
from pathlib import Path

from _plot import main, name_from_path  # pyrefly: ignore[missing-import]
from _risus_data import Versus, scenarios  # pyrefly: ignore[missing-import]
from _risus_display import (  # pyrefly: ignore[missing-import]
    us_vs_them_heatmap_subplot,
    us_vs_them_md_table,
)

_LOGGER = logging.getLogger(__name__)


def callback(args: Namespace, _name: str, _output_path: Path) -> None:
    first_round_scenarios = scenarios(Versus.us_vs_them)
    print(us_vs_them_md_table("Standard<br>(First Round)", first_round_scenarios))  # noqa: T201
    text_color = "white" if args.style == "dark" else "black"
    us_vs_them_heatmap_subplot(first_round_scenarios, ax_color=text_color)


if __name__ == "__main__":
    main(name_from_path(__file__), callback)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging

from _plot import main  # pyrefly: ignore[missing-import]
from _risus_data import Versus, scenarios  # pyrefly: ignore[missing-import]
from _risus_display import (  # pyrefly: ignore[missing-import]
    us_vs_them_heatmap_subplot,
    us_vs_them_md_table,
)
from matplotlib import pyplot as plt

_LOGGER = logging.getLogger(__name__)


def fig_callback(line_color: str) -> None:
    plt.figure().set_size_inches(8, 4)
    first_round_scenarios = scenarios(Versus.us_vs_them)
    print(us_vs_them_md_table("Standard<br>(First Round)", first_round_scenarios))  # noqa: T201
    us_vs_them_heatmap_subplot(first_round_scenarios, ax_color=line_color)


if __name__ == "__main__":
    main(fig_callback)

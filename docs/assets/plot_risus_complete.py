# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

import logging
from functools import partial

from _plot import main  # pyrefly: ignore[missing-import]
from _risus_data import Versus, scenarios  # pyrefly: ignore[missing-import]
from _risus_display import (  # pyrefly: ignore[missing-import]
    us_vs_them_heatmap_subplot,
    us_vs_them_md_table,
)
from _risus_driver import risus_combat_driver  # pyrefly: ignore[missing-import]

_LOGGER = logging.getLogger(__name__)


def fig_callback(line_color: str) -> None:
    # This will show TruncationWarnings at any point where a recursive call to expand
    # within risus_combat_driver exhausts its precision budget, which is more likely to
    # happen the larger the pool size
    complete_combat_scenarios = scenarios(
        partial(
            risus_combat_driver,
            us_vs_them_func=Versus.us_vs_them,
        )
    )
    print(  # noqa: T201
        us_vs_them_md_table("Standard<br>(Complete Combat)", complete_combat_scenarios)
    )
    us_vs_them_heatmap_subplot(
        complete_combat_scenarios, cmap_name="cividis_r", ax_color=line_color
    )


if __name__ == "__main__":
    main(fig_callback)

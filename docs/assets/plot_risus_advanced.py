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
from _risus_advanced import (  # pyrefly: ignore[missing-import]
    deadly_combat_vs,
    evens_up_vs,
)
from _risus_data import scenarios  # pyrefly: ignore[missing-import]
from _risus_display import us_vs_them_heatmap_subplot  # pyrefly: ignore[missing-import]
from _risus_driver import risus_combat_driver  # pyrefly: ignore[missing-import]
from matplotlib import pyplot as plt

_LOGGER = logging.getLogger(__name__)


def fig_callback(line_color: str) -> None:
    our_pool_rel_sizes = tuple(range(5))
    their_pool_sizes = tuple(range(2, 7))
    deadly_combat_scenarios = scenarios(
        partial(
            risus_combat_driver,
            us_vs_them_func=deadly_combat_vs,
        ),
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )
    evens_up_combat_scenarios = scenarios(
        partial(
            risus_combat_driver,
            us_vs_them_func=partial(evens_up_vs, goliath=False),
        ),
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )
    evens_up_w_goliath_combat_scenarios = scenarios(
        partial(
            risus_combat_driver,
            us_vs_them_func=partial(evens_up_vs, goliath=True),
        ),
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )

    plt.gcf().set_size_inches(12, 10)
    axes = us_vs_them_heatmap_subplot(
        deadly_combat_scenarios,
        cmap_name="plasma",
        plt_rows=3,
        plt_row=1,
        ax_color=line_color,
    )
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=60)
    axes = us_vs_them_heatmap_subplot(
        evens_up_combat_scenarios,
        cmap_name="magma",
        plt_rows=3,
        plt_row=2,
        ax_color=line_color,
    )
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=60)
    axes = us_vs_them_heatmap_subplot(
        evens_up_w_goliath_combat_scenarios,
        cmap_name="magma",
        plt_rows=3,
        plt_row=3,
        ax_color=line_color,
    )
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=60)


if __name__ == "__main__":
    main(fig_callback)

# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:base]
from collections.abc import Callable, Sequence
from enum import IntEnum

from dyce import H
from dyce.d import d6

VersusFuncT = Callable[[int, int], H["Versus"]]


class Versus(IntEnum):
    LOSE = -1
    DRAW = 0
    WIN = 1

    @staticmethod
    def raw_vs(us_outcome: int, them_outcome: int) -> "Versus":
        return (
            Versus.LOSE
            if us_outcome < them_outcome
            else Versus.WIN
            if us_outcome > them_outcome
            else Versus.DRAW
        )

    @staticmethod
    def single_round_us_vs_them(
        our_pool_size: int, their_pool_size: int
    ) -> H["Versus"]:
        return (our_pool_size @ d6).apply(Versus.raw_vs, their_pool_size @ d6)


# --8<-- [end:base]

# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:base-use]
our_pool_size = 2
their_pool_size = 3
single_round_us_vs_them = Versus.single_round_us_vs_them(our_pool_size, their_pool_size)
print(single_round_us_vs_them.format(width=65, scaled=True))
# --8<-- [end:base-use]

assert single_round_us_vs_them == H(
    {Versus.LOSE: 1009, Versus.DRAW: 90, Versus.WIN: 197}
)

# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:display]
from typing import TYPE_CHECKING

import pandas as pd
from matplotlib.axes import Axes

ScenariosDataframesT = Sequence[pd.DataFrame]

if TYPE_CHECKING:

    def vs_scenarios_dataframes(
        us_vs_them_func: VersusFuncT,
        *,
        our_pool_rel_sizes: Sequence[int] = tuple(range(-1, 2)),
        their_pool_sizes: Sequence[int] = tuple(range(3, 6)),
    ) -> ScenariosDataframesT: ...

    def us_vs_them_heatmap_subplot(
        vs_dfs: ScenariosDataframesT,
        cmap_name: str = "viridis",
        plt_total_rows: int = 1,
        plt_cur_row: int = 0,
    ) -> list[Axes]: ...
# --8<-- [end:display]

# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:display-detail]
from typing import cast

import matplotlib as mpl
from matplotlib import pyplot as plt
from pandas import Index


def vs_scenarios_dataframes(
    us_vs_them_func: VersusFuncT,
    *,
    our_pool_rel_sizes: Sequence[int] = tuple(range(-1, 2)),
    their_pool_sizes: Sequence[int] = tuple(range(3, 6)),
) -> ScenariosDataframesT:
    vs_dfs: list[pd.DataFrame] = []
    for their_pool_size in their_pool_sizes:
        data: dict[str, dict[str, float]] = {}
        for our_pool_rel_size in our_pool_rel_sizes:
            our_pool_size = their_pool_size + our_pool_rel_size
            us_vs_them_results = H(Versus).merge(
                us_vs_them_func(our_pool_size, their_pool_size)
            )
            data[f"{our_pool_size}d6"] = {
                outcome.name: float(prob)
                for outcome, prob in us_vs_them_results.probability_items()
            }
        df = pd.DataFrame(
            list(data.values()),
            columns=[v.name for v in Versus],
            index=list(data.keys()),
        )
        df.index.name = f"{their_pool_size}d6"
        vs_dfs.append(df)

    return vs_dfs


def us_vs_them_heatmap_subplot(
    vs_dfs: ScenariosDataframesT,
    cmap_name: str = "viridis",
    plt_total_rows: int = 1,
    plt_cur_row: int = 0,
) -> list[Axes]:
    axes: list[Axes] = []
    col_names = [e.name for e in Versus]
    cmap = mpl.colormaps[cmap_name]
    lo_color = cmap(100.0)
    hi_color = cmap(0.0)

    for i, df in enumerate(vs_dfs):
        df = df.copy()  # noqa: PLW2901
        df.index = Index(
            data=[f"our\n {idx} …" for idx in df.index],
            dtype=df.index.dtype,
            name=f"… vs. their {df.index.name}",
        )
        ax = plt.subplot2grid(
            (plt_total_rows, len(vs_dfs)),
            (plt_cur_row, i),
        )
        ax.imshow(df, vmin=0.0, vmax=1.0, cmap=cmap_name)
        ax.set_xticks(range(len(col_names)), labels=col_names)
        ax.tick_params(axis="x", labelrotation=60.0)
        ax.set_yticks(range(len(df.index)), labels=df.index)
        for y, (_, row) in enumerate(df.iterrows()):
            for x, val in enumerate(row):
                ax.text(
                    x,
                    y,
                    f"{val:.0%}",
                    ha="center",
                    va="center",
                    color=hi_color if val > 0.5 else lo_color,
                )
        ax.set_title(cast("str", df.index.name))
        axes.append(ax)

    return axes


# --8<-- [end:display-detail]


def fig_callback_first_round(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:viz-first-round]
    vs_dfs = vs_scenarios_dataframes(Versus.single_round_us_vs_them)
    axes = us_vs_them_heatmap_subplot(vs_dfs, cmap_name="magma")
    plt.gcf().set_size_inches(6.4, 2.8)
    # --8<-- [end:viz-first-round]

    # Style (dark/light) tweaks
    for ax in axes:
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        ax.title.set_color(line_color)


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:driver]
from fractions import Fraction
from functools import cache

from dyce import HResult, expand


def risus_combat_driver(
    our_pool_size: int,  # our starting pool size
    their_pool_size: int,  # their starting pool size
    single_round_us_vs_them_func: VersusFuncT = Versus.single_round_us_vs_them,
) -> H[Versus]:
    # Preliminary checks before we start recursion
    if our_pool_size < 0 or their_pool_size < 0:
        raise ValueError(
            f"cannot have negative numbers (us: {our_pool_size}, "
            f"them: {their_pool_size})"
        )
    elif our_pool_size == 0 and their_pool_size == 0:
        # This should not happen unless we are called as
        # risus_combat_driver(0, 0, ...). In other words, this is the only
        # case where a combat will result in a draw. This is because, draws
        # are re-rolled during combat, so eliminate those results below.
        return H({Versus.DRAW: 1})

    # The @cache` decorator
    # (https://docs.python.org/3/library/functools.html#functools.cache)
    # does simple memoization for us because there are redundancies. For
    # example, we might compute a case where we lose a die, then our
    # opposition loses a die. We arrive at a similar case where our
    # opposition loses a die, then we lose a die. Both cases would be
    # identical from that point on. In this context, `@cache` helps us avoid
    # recomputing redundant sub-trees.
    @cache
    def _resolve_us_vs_them_func(
        our_pool_size: int,  # number of dice we still have
        their_pool_size: int,  # number of dice they still have
    ) -> H[Versus]:
        assert our_pool_size != 0 or their_pool_size != 0, (
            "In this function, the case where both parties are at zero is "
            "considered an error. Because only one party can lose a die "
            "during each round, the only way both parties can be at zero "
            "simultaneously is if they both started at zero. Since we guard "
            "against that case in the enclosing function, we don't have to "
            "worry about it here. Either our_pool_size is zero, "
            "their_pool_size is zero, or neither is zero."
        )
        if our_pool_size == 0:
            # Base case: we are out of dice, so they win
            return H({Versus.LOSE: 1})
        if their_pool_size == 0:
            # Base case: they are out of dice, so we win
            return H({Versus.WIN: 1})
        # Otherwise, the battle rages on ...
        this_round_results = single_round_us_vs_them_func(
            our_pool_size, their_pool_size
        )

        # Keeping in mind that we're inside our recursive implementation, we
        # define a dependent term suitable for dyce.expand, allowing us to
        # take our computation for this round, and use that machinery to
        # "fold in" subsequent rounds.
        def _resolve_next_round_from_this_round(
            this_round: HResult[Versus],
        ) -> H[Versus]:
            match this_round.outcome:
                case Versus.LOSE:
                    # We lost this round, so keep going with one fewer die
                    # in our pool (which could now be at zero dice)
                    return _resolve_us_vs_them_func(
                        our_pool_size - 1,
                        their_pool_size,
                    )
                case Versus.WIN:
                    # They lost this round, so keep going with one fewer die
                    # in their pool (which could now be at zero dice)
                    return _resolve_us_vs_them_func(
                        our_pool_size,
                        their_pool_size - 1,
                    )
                case Versus.DRAW:
                    # Ignore (i.e., immediately re-roll) all ties
                    return H({})
                case _:
                    # Should never be here
                    assert False, (  # noqa: B011, PT015
                        f"unrecognized this_round.outcome {this_round.outcome}"
                    )

        return expand(
            _resolve_next_round_from_this_round,
            this_round_results,
            precision=Fraction(1, 0x7FFFFFFF),
        )  # ty: ignore[invalid-return-type]

    return _resolve_us_vs_them_func(our_pool_size, their_pool_size)


# --8<-- [end:driver]


def fig_callback_multi_round_standard(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:viz-multi-round-standard]
    vs_dfs = vs_scenarios_dataframes(
        risus_combat_driver,
        our_pool_rel_sizes=tuple(range(-1, 3)),
        their_pool_sizes=range(2, 6),
    )
    axes = us_vs_them_heatmap_subplot(vs_dfs, cmap_name="magma")
    plt.gcf().set_size_inches(8.0, 3.2)
    # --8<-- [end:viz-multi-round-standard]

    # Style (dark/light) tweaks
    for ax in axes:
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        ax.title.set_color(line_color)


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:goliath-rule]
def single_round_goliath(
    h_result: HResult[Versus], *, our_pool_size: int, their_pool_size: int
) -> Versus:
    r"""
    Goliath Rule: Instead of re-rolling ties, the win goes to the party with
    fewer dice in this round.
    """
    return (
        Versus(
            # Resolves to 1 if we have fewer dice, -1 if they have fewer
            # dice, and 0 if we're tied
            int(our_pool_size < their_pool_size) - int(our_pool_size > their_pool_size)
        )
        if h_result.outcome == Versus.DRAW
        else h_result.outcome
    )


assert (
    single_round_goliath(
        HResult(h=H(Versus), outcome=Versus.DRAW),
        our_pool_size=1,
        their_pool_size=2,
    )
    is Versus.WIN
)
assert (
    single_round_goliath(
        HResult(h=H(Versus), outcome=Versus.DRAW),
        our_pool_size=2,
        their_pool_size=1,
    )
    is Versus.LOSE
)
assert (
    single_round_goliath(
        HResult(h=H(Versus), outcome=Versus.DRAW),
        our_pool_size=2,
        their_pool_size=2,
    )
    is Versus.DRAW
)
# --8<-- [end:goliath-rule]


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:vs-best-of-set]
from dyce import P


def best_of_set_single_round_us_vs_them(
    our_pool_size: int,
    their_pool_size: int,
    *,
    with_goliath_rule: bool,
) -> H[Versus]:
    our_best = (our_pool_size @ P(6)).h(-1)
    their_best = (their_pool_size @ P(6)).h(-1)
    raw_result = our_best.apply(Versus.raw_vs, their_best)

    return (
        expand(
            single_round_goliath,
            raw_result,
            our_pool_size=our_pool_size,
            their_pool_size=their_pool_size,
        )
        if with_goliath_rule
        else raw_result
    )


# --8<-- [end:vs-best-of-set]

# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:viz-multi-round-goliath-helper]
from typing import Protocol


class VersusFuncGoliathT(Protocol):
    def __call__(
        self,
        our_pool_size: int,
        their_pool_size: int,
        *,
        with_goliath_rule: bool,
    ) -> H[Versus]: ...


if TYPE_CHECKING:

    def viz_multi_round_goliath_helper(
        single_round_goliath_func: VersusFuncGoliathT,
    ) -> Sequence[Axes]: ...
# --8<-- [end:viz-multi-round-goliath-helper]


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:viz-multi-round-goliath-helper-detail]
def viz_multi_round_goliath_helper(
    single_round_goliath_func: VersusFuncGoliathT,
) -> Sequence[Axes]:
    from functools import partial

    all_axes: list[Axes] = []
    our_pool_rel_sizes = tuple(range(-1, 4))
    their_pool_sizes = tuple(range(2, 7))

    # Standard combat (for comparison)
    standard_vs_dfs = vs_scenarios_dataframes(
        risus_combat_driver,
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )
    axes_standard = us_vs_them_heatmap_subplot(
        standard_vs_dfs,
        plt_total_rows=3,
        plt_cur_row=0,
        cmap_name="viridis",
    )
    all_axes.extend(axes_standard)

    # Without the Goliath Rule
    risus_combat_driver_wo_goliath = partial(
        risus_combat_driver,
        single_round_us_vs_them_func=partial(
            single_round_goliath_func, with_goliath_rule=False
        ),
    )
    wo_goliath_dfs = vs_scenarios_dataframes(
        risus_combat_driver_wo_goliath,
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )
    axes_wo_goliath = us_vs_them_heatmap_subplot(
        wo_goliath_dfs,
        plt_total_rows=3,
        plt_cur_row=1,
        cmap_name="cividis",
    )
    all_axes.extend(axes_wo_goliath)

    # With the Goliath Rule
    risus_combat_driver_w_goliath = partial(
        risus_combat_driver,
        single_round_us_vs_them_func=partial(
            single_round_goliath_func, with_goliath_rule=True
        ),
    )
    w_goliath_dfs = vs_scenarios_dataframes(
        risus_combat_driver_w_goliath,
        our_pool_rel_sizes=our_pool_rel_sizes,
        their_pool_sizes=their_pool_sizes,
    )
    axes_w_goliath = us_vs_them_heatmap_subplot(
        w_goliath_dfs,
        plt_total_rows=3,
        plt_cur_row=2,
        cmap_name="plasma",
    )
    all_axes.extend(axes_w_goliath)

    return all_axes


# --8<-- [end:viz-multi-round-goliath-helper-detail]


def fig_callback_multi_round_best_of_set(line_color: str) -> None:
    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:viz-multi-round-best-of-set]
    axes = viz_multi_round_goliath_helper(best_of_set_single_round_us_vs_them)
    fig = plt.gcf()
    fig.set_size_inches(9.6, 9.6)
    fig.suptitle(
        "Full combat results based on starting pool sizes\n"
        "Standard (top row)\n"
        "Best-of-Set w/o the Goliath Rule (middle row)\n"
        "Best-of-Set w/ the Goliath Rule (bottom row)"
    )
    # --8<-- [end:viz-multi-round-best-of-set]

    # Style (dark/light) tweaks
    for ax in axes:
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        ax.title.set_color(line_color)
        fig.suptitle(fig.get_suptitle(), color=line_color)


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:evens-up-base]
from dyce import explode_n


class EvensUp(IntEnum):
    MISS = 0
    HIT = 1
    HIT_EXPLODE = 2


d_evens_up_raw = H(
    (
        EvensUp.MISS,  # 1
        EvensUp.HIT,  # 2
        EvensUp.MISS,  # 3
        EvensUp.HIT,  # 4
        EvensUp.MISS,  # 5
        EvensUp.HIT_EXPLODE,  # 6
    )
)
d_evens_up_raw_exploded = (
    explode_n(
        d_evens_up_raw,
        n=3,  # plenty deep for our needs
    )
    + 0  # make sure everything is an int
)
print(d_evens_up_raw_exploded)
# --8<-- [end:evens-up-base]

assert d_evens_up_raw_exploded == H(
    {0: 648, 1: 432, 2: 108, 3: 72, 4: 18, 5: 12, 6: 3, 7: 2, 8: 1}
)


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:evens-up-decode-hits]
def evens_up_decode_hits(outcome: int) -> int:
    # Clever math that is equivalent to:
    #     outcome // 2 +  # a tally of any exploded hits
    #     outcome % 2  # any final hit  # noqa: ERA001
    return (outcome + 1) // 2


d_evens_up = d_evens_up_raw_exploded.apply(evens_up_decode_hits).lowest_terms()
print(d_evens_up.format(width=65, scaled=True))
# --8<-- [end:evens-up-decode-hits]

assert d_evens_up == H({0: 216, 1: 180, 2: 30, 3: 5, 4: 1})


# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:evens-up]
def evens_up_single_round_us_vs_them(
    our_pool_size: int,
    their_pool_size: int,
    *,
    with_goliath_rule: bool,
) -> H[Versus]:
    raw_result = (our_pool_size @ d_evens_up).apply(
        Versus.raw_vs, their_pool_size @ d_evens_up
    )

    return (
        expand(
            single_round_goliath,
            raw_result,
            our_pool_size=our_pool_size,
            their_pool_size=their_pool_size,
        )
        if with_goliath_rule
        else raw_result
    )


# --8<-- [end:evens-up]


def fig_callback_multi_round_evens_up(line_color: str) -> None:

    # NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
    # --8<-- [start:viz-multi-round-evens-up]
    axes = viz_multi_round_goliath_helper(evens_up_single_round_us_vs_them)
    fig = plt.gcf()
    fig.set_size_inches(9.6, 9.6)
    fig.suptitle(
        "Full combat results based on starting pool sizes\n"
        "Standard (top row)\n"
        "Evens Up w/o the Goliath Rule (middle row)\n"
        "Evens Up w/ the Goliath Rule (bottom row)"
    )
    # --8<-- [end:viz-multi-round-evens-up]

    # Style (dark/light) tweaks
    for ax in axes:
        ax.tick_params(axis="x", colors=line_color)
        ax.tick_params(axis="y", colors=line_color)
        ax.title.set_color(line_color)
        fig.suptitle(fig.get_suptitle(), color=line_color)


if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    from _plot import _PARSER, main  # pyrefly: ignore[missing-import]

    args = _PARSER.parse_args()
    orig_output_file = args.output_file

    for suffix, fig_callback in {
        "first_round": fig_callback_first_round,
        "multi_round_standard": fig_callback_multi_round_standard,
        "multi_round_best_of_set": fig_callback_multi_round_best_of_set,
        "multi_round_evens_up": fig_callback_multi_round_evens_up,
    }.items():
        would_be_output_file = args.output_dir.resolve().joinpath(
            Path(f"{Path(sys.argv[0]).stem}_{suffix}_{args.style}.svg")
        )
        if not orig_output_file or would_be_output_file == orig_output_file:
            args.output_file = would_be_output_file
            main(fig_callback, args)

    would_be_output_file = args.output_dir.resolve().joinpath(
        Path(f"{Path(sys.argv[0]).stem}_evens_up_base.txt")
    )
    if not orig_output_file or would_be_output_file == orig_output_file:
        with would_be_output_file.open("w", encoding="utf_8") as f:
            f.write(repr(d_evens_up_raw_exploded) + os.linesep)

    would_be_output_file = args.output_dir.resolve().joinpath(
        Path(f"{Path(sys.argv[0]).stem}_evens_up_base_use.txt")
    )
    if not orig_output_file or would_be_output_file == orig_output_file:
        with would_be_output_file.open("w", encoding="utf_8") as f:
            f.write(single_round_us_vs_them.format(width=65, scaled=True) + os.linesep)

    would_be_output_file = args.output_dir.resolve().joinpath(
        Path(f"{Path(sys.argv[0]).stem}_evens_up_decode_hits.txt")
    )
    if not orig_output_file or would_be_output_file == orig_output_file:
        with would_be_output_file.open("w", encoding="utf_8") as f:
            f.write(d_evens_up.format(width=65, scaled=True) + os.linesep)


# TODO(posita): # noqa: TD003 - Maybe eliminate the tables, since the heat maps are
# NOTE: Changes to this section should be propagated to docs/assets/nb_ironsworn.py
# --8<-- [start:table]
import os
from collections.abc import Iterator

import jinja2  # noqa: F401

if TYPE_CHECKING:

    def us_vs_them_table_html(vs_dfs: ScenariosDataframesT) -> str: ...


def us_vs_them_table_html(vs_dfs: ScenariosDataframesT) -> str:
    def _html_gen() -> Iterator[str]:
        for df in vs_dfs:
            df = df.copy()  # noqa: PLW2901
            df.index = Index(
                data=[f"our\n {idx} …" for idx in df.index],
                dtype=df.index.dtype,
                name=f"… vs. their {df.index.name}",
            )
            yield df.style.format("{:.0%}").to_html()  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]

    return os.linesep.join(_html_gen())


# basically the same thing?
vs_dfs = vs_scenarios_dataframes(Versus.single_round_us_vs_them)
us_vs_them_table_html(vs_dfs)

# --8<-- [end:table]

# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## [`dyce`](https://posita.github.io/dyce/) modeling of [*Ironsworn*](https://www.ironswornrpg.com/)'s core mechanic
#
# Select ``Run All Cells`` from the ``Run`` menu above.

# %% jupyter={"source_hidden": true}
# Install additional requirements if necessary
from prerequisites import (  # pyright: ignore[reportMissingImports] # pyrefly: ignore[missing-import] # ty: ignore[unresolved-import]
    install_if_missing,
)

await install_if_missing(  # pyright: ignore # pyrefly: ignore[invalid-syntax] # noqa: PGH003
    ("dyce", "dyce~=0.7.0", "dyce"),  # piplite_spec omits version (local wheel)
)

import warnings

import matplotlib_inline
from matplotlib import style

from dyce.lifecycle import ExperimentalWarning

matplotlib_inline.backend_inline.set_matplotlib_formats("svg")
style.use("bmh")
warnings.filterwarnings("ignore", category=ExperimentalWarning)

# %%
from enum import IntEnum

from dyce import HResult, PResult, expand
from dyce.d import d6, p2d10


class IronDramaticResult(IntEnum):
    SPECTACULAR_FAILURE = -1
    FAILURE = 0
    WEAK_SUCCESS = 1
    STRONG_SUCCESS = 2
    SPECTACULAR_SUCCESS = 3


def iron_dramatic_dependent_term(
    action: HResult[int],
    challenges: PResult[int],
    *,
    action_mod: int = 0,
) -> IronDramaticResult:
    modded_action = action.outcome + action_mod
    assert len(challenges.roll) == 2, "pool must have exactly 2 challenge dice"
    first_challenge_outcome, second_challenge_outcome = challenges.roll
    challenge_doubles = first_challenge_outcome == second_challenge_outcome
    modded_action_beats_first_challenge = modded_action > first_challenge_outcome
    modded_action_beats_second_challenge = modded_action > second_challenge_outcome

    if modded_action_beats_first_challenge and modded_action_beats_second_challenge:
        return (
            IronDramaticResult.SPECTACULAR_SUCCESS
            if challenge_doubles
            else IronDramaticResult.STRONG_SUCCESS
        )
    elif modded_action_beats_first_challenge or modded_action_beats_second_challenge:
        return IronDramaticResult.WEAK_SUCCESS
    else:
        return (
            IronDramaticResult.SPECTACULAR_FAILURE
            if challenge_doubles
            else IronDramaticResult.FAILURE
        )


action_mods = list(range(-1, 4))
results_by_action_mods = {
    action_mod: expand(iron_dramatic_dependent_term, d6, p2d10, action_mod=action_mod)
    for action_mod in action_mods
}

# %%
import pandas as pd

data = [
    {
        outcome.name: float(prob)
        for outcome, prob in result.zero_fill(IronDramaticResult).probability_items()
    }
    for result in results_by_action_mods.values()
]

# TODO(posita): See <https://github.com/pandas-dev/pandas/issues/54386>
categories = [v.name for v in IronDramaticResult]
df = pd.DataFrame(data, columns=categories, index=action_mods)
df.index.name = "Action Modifier"
df.style.format("{:.2%}")

# %%
from matplotlib import pyplot as plt
from matplotlib import ticker

ax = df.plot(kind="barh", stacked=True)
ax.xaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
ax.set_title("Ironsworn distributions")
ax.legend(loc="center")

plt.tight_layout()

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
# ## [`dyce`](https://posita.github.io/dyce/) translation of one example from [`LordSembor/DnDice`](https://github.com/LordSembor/DnDice#examples)
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
from dyce import H, HResult, P, expand

normal_hit = H(12) + 5
critical_hit = 3 @ H(12) + 5
advantage = (2 @ P(20)).h(-1)


def crit(result: HResult[int]) -> H[int] | int:
    if result.outcome == 20:
        return critical_hit
    elif result.outcome + 5 >= 14:
        return normal_hit
    else:
        return 0


advantage_weighted = expand(crit, advantage)

# %%
from matplotlib import ticker

from dyce.viz import plot_line

ax = plot_line(
    normal_hit,
    critical_hit,
    advantage_weighted,
    labels=["Normal hit", "Critical hit", "Advantage-weighted"],
)
ax.xaxis.set_major_locator(ticker.IndexLocator(base=2, offset=1))
ax.legend()
ax.set_title("Advantage-weighted attack with critical hits")

from matplotlib import pyplot as plt

plt.tight_layout()

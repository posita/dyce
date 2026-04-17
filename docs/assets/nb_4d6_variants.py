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
# ## Modeling "[The Probability of 4d6, Drop the Lowest, Reroll 1s](http://prestonpoulter.com/2010/11/19/the-probability-of-4d6-drop-the-lowest-reroll-1s/)" in [``dyce``](https://posita.github.io/dyce/)
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
from dyce import H, P, expand

p_4d6 = 4 @ P(6)
d6_reroll_first_one = expand(
    lambda result: result.h if result.outcome == 1 else result.outcome,
    H(6),
)
p_4d6_reroll_first_one = 4 @ P(d6_reroll_first_one)
p_4d6_reroll_all_ones = 4 @ P(H(5) + 1)

attr_results: dict[str, H] = {
    "3d6": 3 @ H(6),
    "4d6 - discard lowest": p_4d6.h(slice(1, None)),
    "4d6 - re-roll first 1, discard lowest": p_4d6_reroll_first_one.h(slice(1, None)),
    "4d6 - re-roll all 1s (i.e., 4d(1d5 + 1)), discard lowest": p_4d6_reroll_all_ones.h(
        slice(1, None)
    ),
    "2d6 + 6": 2 @ H(6) + 6,
    "4d4 + 2": 4 @ H(4) + 2,
}

# %%
from dyce.viz import plot_line

labels, hs = zip(*attr_results.items(), strict=True)
ax = plot_line(*hs, labels=labels, markers="Ds^*xo")
ax.legend()
ax.set_title("Comparing various take-three-of-4d6 methods")

from matplotlib import pyplot as plt

plt.tight_layout()

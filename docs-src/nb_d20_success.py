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
#   language_info:
#     name: python
# ---

# %% [markdown]
# <!---
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!! IMPORTANT: READ THIS BEFORE EDITING! !!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# When updating a cell, plan to re-run the notebook locally and recommit the .ipynb
# afterward. Otherwise, the pre-populated output for that cell will disappear or be
# stale.
# -->
#
# ## Using [`dyce`](https://dycelib.org/) for success checks using a d20 and a target number
#
# Consider a mechanic where a roll on a fair twenty-sided die “succeeds” when it is greater than or equal to a specific value (a “target number”).
# This example compares the outcome distributions for one d20, the higher of two d20s (“advantage”), and the lower of two d20s (“disadvantage”).
#
# Select `Run All Cells` from the `Run` menu above.

# %% jupyter={"source_hidden": true}
# Install additional requirements if necessary
from prerequisites import (  # pyright: ignore[reportMissingImports] # ty: ignore[unresolved-import] # zuban: ignore[import-not-found]
    install_if_missing,
)

await install_if_missing(  # type: ignore[top-level-await]
    ("dyce", "dyce~=0.7.0", "dyce"),  # piplite_spec omits version (local wheel)
)

import warnings

import matplotlib.style as mstyle
import matplotlib_inline

from dyce.lifecycle import ExperimentalWarning

matplotlib_inline.backend_inline.set_matplotlib_formats("svg")  # type: ignore[no-untyped-call]
mstyle.use("bmh")
warnings.simplefilter("ignore", ExperimentalWarning)

# %%
from dyce import H, P

d20 = H(20)  # shorthand for an evenly-weighted 20-sided die
print(d20)

# %%
p2d20 = 2 @ P(d20)  # a pool of two such dice
d20_advantage = p2d20.at(-1)  # right-most index is highest
d20_disadvantage = p2d20.at(0)  # left-most index is lowest
print(d20_advantage)
print(d20_disadvantage)

# %% [markdown]
# With a single d20, the chance of rolling a 15 or higher is 30%.
# With advantage, it climbs to 51%.
# With disadvantage, it drops to 9%.

# %%
target_number = 15
# How often a d20 is greater than or equal to target_number
d20_vs_target = d20.ge(target_number)
print(d20_vs_target.format())

# %%
d20_advantage_vs_target = d20_advantage.ge(target_number)
print(d20_advantage_vs_target.format())

# %%
d20_disadvantage_vs_target = d20_disadvantage.ge(target_number)
print(d20_disadvantage_vs_target.format())

# %% [markdown]
# As one might expect, with a single d20, each outcome is equally likely, with 10.5 being the average.a
# With advantage, one is likely to roll at ***least*** a 15 over half the time, and one is nearly twice as likely to roll a 20.
# With disadvantage, one is likely to roll at ***most*** a 6 over half the time, and one is nearly twice as likely to roll a 1.

# %%
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

from dyce.viz.matplotlib import plot_burst

_, axes = plt.subplots(1, 2)
plot_burst(
    d20_advantage,
    d20,
    title="highest of 2d20\nor “advantage” (foreground)\nvs. d20 (background)",
    alpha=0.9,
    ax=axes[0],
    cmap="twilight_shifted",
    compare_cmap="twilight_r",
)
plot_burst(
    d20_disadvantage,
    d20,
    title="lowest of 2d20\nor “disadvantage” (foreground)\nvs. d20 (background)",
    alpha=0.9,
    ax=axes[1],
    cmap="twilight_shifted_r",
    compare_cmap="twilight",
)
for ax in axes:
    for wedge in (patch for patch in ax.patches if isinstance(patch, Wedge)):
        wedge.set_edgecolor(mpl.rcParams["text.color"])
plt.gcf().set_size_inches(8, 6)

plt.tight_layout()

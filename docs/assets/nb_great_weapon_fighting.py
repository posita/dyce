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
# ## [`dyce`](https://posita.github.io/dyce/) translation of one example from [`LordSembor/DnDice`](https://github.com/LordSembor/DnDice#examples)
#
# Select `Run All Cells` from the `Run` menu above.

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
from dyce import H, HResult, expand

single_attack = 2 @ H(6) + 5


def gwf_2014(result: HResult[int]) -> H[int] | int:
    # Re-roll either die if it is a one or two
    return result.h if result.outcome in (1, 2) else result.outcome


def gwf_2024(result: HResult[int]) -> H[int] | int:
    # Ones and twos are promoted to 3s
    return 3 if result.outcome in (1, 2) else result.outcome


h_gwf_2014 = 2 @ expand(gwf_2014, H(6)) + 5
h_gwf_2024 = 2 @ expand(gwf_2024, H(6)) + 5

# %%
import pandas as pd

data = [
    {outcome: float(prob) for outcome, prob in h.probability_items()}
    for h in (single_attack, h_gwf_2014, h_gwf_2024)
]
label_sa = "Normal attack"
label_gwf_2014 = "\u201cGWF\u201d (2014)"
label_gwf_2024 = "\u201cGWF\u201d (2024)"
df = pd.DataFrame(data, index=[label_sa, label_gwf_2014, label_gwf_2024])

# %% editable=false jupyter={"source_hidden": true}
# Display df as table
# Translated from print(df.style.format("{:.0%}").to_html()) in plot_great_weapon_fighting.py
import jinja2  # noqa: F401

df.style.format("{:.0%}")  # pyright: ignore[reportAttributeAccessIssue] # ty: ignore[unresolved-attribute]

# %%
from matplotlib import pyplot as plt

from dyce.viz import plot_burst, plot_line

cmap_sa = "Reds"
cmap_gwf_2014 = "Greens"
cmap_gwf_2024 = "Purples"

ax_sa = plt.subplot2grid((3, 2), (0, 0), rowspan=3)
plot_line(
    single_attack,
    h_gwf_2014,
    h_gwf_2024,
    labels=[label_sa, label_gwf_2014, label_gwf_2024],
    ax=ax_sa,
)
ax_sa.lines[0].set_color(plt.get_cmap(cmap_sa)(1.0))
ax_sa.lines[1].set_color(plt.get_cmap(cmap_gwf_2014)(1.0))
ax_sa.lines[2].set_color(plt.get_cmap(cmap_gwf_2024)(1.0))
ax_sa.legend()

ax_sa_gwf_2014 = plt.subplot2grid((3, 2), (0, 1))
plot_burst(
    h_gwf_2014,
    single_attack,
    cmap=cmap_gwf_2014,
    compare_cmap=cmap_sa,
    title=f"{label_sa}\nvs.\n{label_gwf_2014}",
    ax=ax_sa_gwf_2014,
)

ax_sa_gwf_2024 = plt.subplot2grid((3, 2), (1, 1))
plot_burst(
    h_gwf_2024,
    single_attack,
    cmap=cmap_gwf_2024,
    compare_cmap=cmap_sa,
    title=f"{label_sa}\nvs.\n{label_gwf_2024}",
    ax=ax_sa_gwf_2024,
)

ax_gwf_2014_2024 = plt.subplot2grid((3, 2), (2, 1))
plot_burst(
    h_gwf_2024,
    h_gwf_2014,
    cmap=cmap_gwf_2024,
    compare_cmap=cmap_gwf_2014,
    title=f"{label_gwf_2014}\nvs.\n{label_gwf_2024}",
    ax=ax_gwf_2014_2024,
)

plt.gcf().set_size_inches(9.6, 9.6)

plt.tight_layout()

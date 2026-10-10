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
# ## [`dyce`](https://dycelib.org/) example of a “diminishing explode” mechanic
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
from dyce import H, HResult
from dyce.d import d4, d6, d8, d10, d12, d20

progression = {
    d6: d4,
    d8: d6,
    d10: d8,
    d12: d10,
    d20: d12,
}


def diminishing_returns_resolver(
    result: HResult[int],
    _n_left: int,
    _n_done: int,
    *,
    progression: dict[H[int], H[int]],
) -> H[int] | int:
    if result.outcome == max(result.h) and result.h in progression:
        return progression[result.h]
    return result.outcome


# %%
import sys
from functools import partial

import matplotlib.ticker as mticker

from dyce import explode_n
from dyce.viz.matplotlib import plot_ridge

ax = plot_ridge(
    *(
        explode_n(
            d,
            n=sys.maxsize,  # unrestricted recursion, since our resolver determines how deep we go
            resolver=partial(
                diminishing_returns_resolver,
                progression=progression,
            ),
        )
        for d in progression
    ),
    labels=("d6", "d8", "d10", "d12", "d20"),
    cmap="coolwarm",
)
ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
ax.tick_params(axis="x", labelrotation=60)
ax.set_title("Diminishing explode mechanic for polygonal dice")

import matplotlib.pyplot as plt

plt.tight_layout()

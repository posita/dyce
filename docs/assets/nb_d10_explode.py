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
# ## [`dyce`](https://posita.github.io/dyce/) translation of the accepted answer to "[Roll and Keep in Anydice?](https://rpg.stackexchange.com/a/166637)"
#
# Select `Run All Cells` from the `Run` menu above.

# %% jupyter={"source_hidden": true}
# Install additional requirements if necessary
from prerequisites import (  # pyright: ignore[reportMissingImports] # pyrefly: ignore[missing-import] # ty: ignore[unresolved-import]
    install_if_missing,
)

await install_if_missing(  # type: ignore[top-level-await]
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
from dyce import H, P, explode_n

explode_depth = 2


def keep(p: P[int], k: int) -> H[int]:
    r"Negative k keeps lowest, otherwise keeps highest"
    return p.h(slice(-k, None) if k > 0 else slice(-k))


def nkk(n: int, k: int) -> H[int]:
    return keep(n @ P(explode_n(H(10), n=explode_depth)), k=k)


# %%
from matplotlib import pyplot as plt
from matplotlib import ticker

from dyce.viz.matplotlib import plot_ridge

k_start, k_end = 3, 6  # range: [start_k..end_k)
n_start, n_end = 5, 11  # range: [start_n..end_n)
rows_by_k = {
    k: [(f"{n}k{k}", nkk(n, k)) for n in range(n_start, n_end)]
    for k in range(k_start, k_end)
}
max_x = max(max(h) for rows in rows_by_k.values() for _, h in rows)
max_y = max(
    float(prob)
    for rows in rows_by_k.values()
    for _, h in rows
    for _, prob in h.probability_items()
)
for k, rows in rows_by_k.items():
    labels, hs = zip(*rows, strict=True)
    ax = plt.subplot2grid((k_end - k_start, 1), (k - k_start, 0))
    plot_ridge(*hs, labels=labels, cmap="cool", peak=max_y, ax=ax)
    for line in ax.lines:
        line.set_marker("")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.tick_params(axis="x", labelrotation=60)
    ax.set_title(f"Taking the {k} highest of $n$ exploding d10s")
    ax.set_xlim(left=0, right=max_x)  # subplots should share a horizontal scale
# subplots should share a vertical scale
axes = plt.gcf().get_axes()
y_lims = [ax.get_ylim() for ax in axes]
for ax in axes:
    ax.set_ylim(min(lo for lo, _ in y_lims), max(hi for _, hi in y_lims))
plt.gcf().set_size_inches(6.4, 8.0)

from matplotlib import pyplot as plt

plt.tight_layout()

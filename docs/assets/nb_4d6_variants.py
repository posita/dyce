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
# ## Modeling "[The Probability of 4d6, Drop the Lowest, Reroll 1s](http://prestonpoulter.com/2010/11/19/the-probability-of-4d6-drop-the-lowest-reroll-1s/)" in [`dyce`](https://posita.github.io/dyce/)
#
# Select `Run All Cells` from the `Run` menu above.

# %% jupyter={"source_hidden": true}
# Install additional requirements if necessary
from prerequisites import (  # pyright: ignore[reportMissingImports] # pyrefly: ignore[missing-import] # ty: ignore[unresolved-import]
    install_if_missing,
)

await install_if_missing(  # type: ignore[top-level-await] # noqa: PGH003
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
from matplotlib import pyplot as plt

from dyce.viz import plot_burst, plot_line

labels, hs = zip(*attr_results.items(), strict=True)

ax_lines = plt.subplot2grid((3, 3), (0, 0), colspan=3)
plot_line(*hs, labels=labels, markers="Ds^*xo", ax=ax_lines)
ax_lines.legend()
ax_lines.set_title("Comparing various take-three-of-4d6 methods")

for i, (label, h) in enumerate(attr_results.items()):
    ax_burst = plt.subplot2grid((3, 3), (1 + i // 3, i % 3))
    plot_burst(h, title=label, ax=ax_burst)
    ax_burst.set_title(ax_burst.get_title(), wrap=True)

plt.gcf().set_size_inches(9.6, 9.6)

plt.tight_layout()

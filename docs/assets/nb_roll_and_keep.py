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
# ## [`dyce`](https://posita.github.io/dyce/) translation of "[How do I implement this specialized roll-and-keep mechanic in AnyDice?](https://rpg.stackexchange.com/a/190806)"
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
from collections.abc import Iterator

from dyce import H, P


def roll_and_keep(p: P[int], k: int) -> H[int]:
    assert all(h == p[0] for h in p), "pool must be homogeneous"
    max_d = max(p[-1]) if p else 0
    return H.from_counts(
        (
            sum(roll[-k:]) + sum(1 for outcome in roll[:-k] if outcome == max_d),
            count,
        )
        for roll, count in p.rolls_with_counts()
    )


d, k = 6, 3


def roll_and_keep_hs() -> Iterator[tuple[str, H[int]]]:
    for n in range(k + 1, k + 9):
        p = n @ P(d)
        yield f"{n}d{d} keep {k} add +1", roll_and_keep(p, k)


def normal() -> Iterator[tuple[str, H[int]]]:
    for n in range(k + 1, k + 9):
        p = n @ P(d)
        yield f"{n}d{d} keep {k}", p.h(slice(-k, None))


# %%
from dyce.viz import plot_line

labels1, hs1 = zip(*tuple(normal()), strict=True)
ax = plot_line(*hs1, labels=labels1, markers=".", alpha=0.75)

labels2, hs2 = zip(*tuple(roll_and_keep_hs()), strict=True)
plot_line(*hs2, labels=labels2, markers="o", alpha=0.25, ax=ax)

ax.set_title("Roll-and-keep mechanic comparison")
ax.legend(loc="upper left")

from matplotlib import pyplot as plt

plt.tight_layout()

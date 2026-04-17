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
# ## [`dyce`](https://posita.github.io/dyce/) translation of the accepted answer to "[How do I count the number of duplicates in anydice?](https://rpg.stackexchange.com/a/111421)"
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
from dyce import H, P


def count_dupes(pool: P) -> H[int]:
    return H.from_counts(
        (sum(1 for i in range(1, len(roll)) if roll[i] == roll[i - 1]), count)
        for roll, count in pool.rolls_with_counts()
    )


res_15d6 = count_dupes(15 @ P(6))
res_8d10 = count_dupes(8 @ P(10))

# %%
from dyce.viz import plot_bar

ax = plot_bar(res_15d6, res_8d10, labels=["15d6", "8d10"])
ax.legend()
ax.set_title("Chances of rolling $n$ duplicates")

from matplotlib import pyplot as plt

plt.tight_layout()

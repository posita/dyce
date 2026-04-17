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
# ## [`dyce`](https://posita.github.io/dyce/) translation of one example from [`markbrockettrobson/python_dice`](https://github.com/markbrockettrobson/python_dice#usage)
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
from dyce import H

save_roll = H(20)
burning_arch_damage = 10 @ H(6) + 10
pass_save = save_roll.ge(10)
damage_half_on_save = burning_arch_damage // (pass_save + 1)

# %%
from matplotlib import ticker

from dyce.viz import plot_line

ax = plot_line(damage_half_on_save)
ax.xaxis.set_major_locator(ticker.IndexLocator(base=2, offset=0))
ax.set_title("Attack with saving throw for half damage")

from matplotlib import pyplot as plt

plt.tight_layout()

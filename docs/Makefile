# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

define _PY_PLOT_BURST_1
from dyce import H
from dyce.plt import plot_burst
h = 4@H((-1, 0, 1))
fig, _ = plot_burst(h)
fig.savefig("plot_burst_1.png", dpi=72)
endef

export _PY_PLOT_BURST_1

plot_burst_1.png: Makefile
	python -c "$${_PY_PLOT_BURST_1}"

define _PY_PLOT_BURST_2
from dyce import D
from dyce.plt import plot_burst
d20 = D(20)
fig, _ = plot_burst(d20.h(), outer=(
  ("crit. fail.", d20.le(1)[1]),
  ("fail.", d20.within(2, 14)[0]),
  ("succ.", d20.within(15, 19)[0]),
  ("crit. succ.", d20.ge(20)[1]),
), graph_color="RdYlBu_r")
fig.savefig("plot_burst_2.png", dpi=72)
endef

export _PY_PLOT_BURST_2

plot_burst_2.png: Makefile
	python -c "$${_PY_PLOT_BURST_2}"

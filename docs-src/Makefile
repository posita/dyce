# ======================================================================================
# Copyright and other protections apply. Please see the accompanying LICENSE file for
# rights and restrictions governing use of this software. All rights not expressly
# waived or licensed are reserved. If that file is missing or appears to be modified
# from its original, then please contact the author before viewing or using this
# software in any capacity.
# ======================================================================================

all : \
	../docs/dyce-powered.svg \
	../docs/index.md \
	../docs/license.md \
	../docs/images/plot_matplotlib_2d6_lo_hi_dark.svg \
	../docs/images/plot_matplotlib_2d6_lo_hi_light.svg \
	../docs/images/plot_matplotlib_3d6_selection_dark.svg \
	../docs/images/plot_matplotlib_3d6_selection_light.svg \
	../docs/images/plot_matplotlib_4d6_variants_dark.svg \
	../docs/images/plot_matplotlib_4d6_variants_light.svg \
	../docs/images/plot_matplotlib_advantage_dark.svg \
	../docs/images/plot_matplotlib_advantage_light.svg \
	../docs/images/plot_matplotlib_burning_arch_dark.svg \
	../docs/images/plot_matplotlib_burning_arch_light.svg \
	../docs/images/plot_matplotlib_d10_explode_dark.svg \
	../docs/images/plot_matplotlib_d10_explode_light.svg \
	../docs/images/plot_matplotlib_d20_success_dark.svg \
	../docs/images/plot_matplotlib_d20_success_light.svg \
	../docs/images/plot_matplotlib_d4s_dark.svg \
	../docs/images/plot_matplotlib_d4s_light.svg \
	../docs/images/plot_matplotlib_dupes_dark.svg \
	../docs/images/plot_matplotlib_dupes_light.svg \
	../docs/images/plot_matplotlib_great_weapon_fighting_dark.svg \
	../docs/images/plot_matplotlib_great_weapon_fighting_light.svg \
	../docs/images/plot_matplotlib_ironsworn_dark.svg \
	../docs/images/plot_matplotlib_ironsworn_light.svg \
	../docs/images/plot_matplotlib_risus_first_round_dark.svg \
	../docs/images/plot_matplotlib_risus_first_round_light.svg \
	../docs/images/plot_matplotlib_risus_multi_round_standard_dark.svg \
	../docs/images/plot_matplotlib_risus_multi_round_standard_light.svg \
	../docs/images/plot_matplotlib_roll_and_keep_dark.svg \
	../docs/images/plot_matplotlib_roll_and_keep_light.svg \
	../docs/images/plot_matplotlib_plot_bar_dark.svg \
	../docs/images/plot_matplotlib_plot_bar_light.svg \
	../docs/images/plot_matplotlib_plot_burst_dark.svg \
	../docs/images/plot_matplotlib_plot_burst_light.svg \
	../docs/images/plot_matplotlib_plot_bar_horizontal_dark.svg \
	../docs/images/plot_matplotlib_plot_bar_horizontal_light.svg \
	../docs/images/plot_matplotlib_plot_line_dark.svg \
	../docs/images/plot_matplotlib_plot_line_light.svg \
	../docs/images/plot_matplotlib_plot_line_at_most_dark.svg \
	../docs/images/plot_matplotlib_plot_line_at_most_light.svg \
	../docs/images/plot_matplotlib_plot_line_at_least_dark.svg \
	../docs/images/plot_matplotlib_plot_line_at_least_light.svg \
	../docs/images/plot_matplotlib_plot_ridge_dark.svg \
	../docs/images/plot_matplotlib_plot_ridge_light.svg \
	../requirements-dev.txt \
	jupyterlite \
	snippets/plot_plotly_3d6_selection.html \
	snippets/plot_plotly_bar_spec.html \
	snippets/plot_plotly_bar_spec_horizontal.html \
	snippets/plot_plotly_line_spec.html \
	snippets/plot_plotly_line_spec_at_least.html \
	snippets/plot_plotly_line_spec_at_most.html \
	snippets/plot_plotly_ridge_spec.html

.PHONY : all jupyterlite perf FORCE
FORCE :

perf : \
	perf_expand.txt \
	perf_rolls_with_counts.txt

../requirements-dev.txt : ../uv.lock
	cd .. && uv export --format requirements-txt --locked --no-hashes >$@

../docs/dyce-powered.svg : Makefile
	curl --fail --silent --show-error --location --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-%F0%9D%9A%8D%F0%9D%9A%A2%F0%9D%9A%8C%F0%9D%9A%8E--powered%21-gold'

../docs/index.md : ../README.md FORCE
	@set -eu; \
	raw_version=$$("$${PYTHON:-python3}" -c 'import importlib.metadata; print(importlib.metadata.version("dyce"))'); \
	case "$$raw_version" in \
		*+*|*.dev*) git_ref=main; docs_version=latest; release=;; \
		*) git_ref="v$$raw_version"; docs_version=$$(printf '%s' "$$raw_version" | cut -d. -f1,2); release=1;; \
	esac; \
	temp_file=$$(mktemp ../docs/.index.md.XXXXXX); \
	trap 'rm -f "$$temp_file" "$$temp_file.release"' 0; \
	sed \
		-e '/<!-- docs:hide:start -->/,/<!-- docs:hide:end -->/d' \
		-e "s#raw.githubusercontent.com/posita/dyce/main/#raw.githubusercontent.com/posita/dyce/$$git_ref/#g" \
		-e "s#github.com/posita/dyce/blob/main/#github.com/posita/dyce/blob/$$git_ref/#g" \
		-e "s#github.com/posita/dyce/tree/main/#github.com/posita/dyce/tree/$$git_ref/#g" \
		-e "s#https://dycelib.org/latest/#https://dycelib.org/$$docs_version/#g" \
		../README.md > "$$temp_file"; \
	if [ -n "$$release" ]; then \
		sed -E \
			-e "s#(https://img\.shields\.io/pypi/[^/]+/dyce)\.svg#\1/$$raw_version.svg#g" \
			-e "s#(https://pypi\.org/project/dyce/)\)#\1$$raw_version/)#g" \
			"$$temp_file" > "$$temp_file.release"; \
		mv "$$temp_file.release" "$$temp_file"; \
	fi; \
	if ! cmp -s "$$temp_file" "$@"; then \
		chmod 644 "$$temp_file"; \
		mv "$$temp_file" "$@"; \
	fi

../docs/license.md : ../LICENSE
	cp -p $< $@

../docs/notebooks/%.ipynb : nb_%.py
	jupytext --to notebook --update $< --output $@
	ruff check --fix $@
	ruff format $@
	touch $@

../docs/images/plot_matplotlib_risus_first_round_dark.svg \
../docs/images/plot_matplotlib_risus_multi_round_standard_dark.svg \
../docs/images/plot_matplotlib_risus_multi_round_best_of_set_dark.svg \
../docs/images/plot_matplotlib_risus_multi_round_evens_up_dark.svg &: plot_matplotlib_risus.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_matplotlib_risus.py --log-level INFO --style dark --output-dir ../docs/images

../docs/images/plot_matplotlib_risus_first_round_light.svg \
../docs/images/plot_matplotlib_risus_multi_round_standard_light.svg \
../docs/images/plot_matplotlib_risus_multi_round_best_of_set_light.svg \
../docs/images/plot_matplotlib_risus_multi_round_evens_up_light.svg &: plot_matplotlib_risus.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_matplotlib_risus.py --log-level INFO --style light --output-dir ../docs/images

../docs/images/plot_matplotlib_%_dark.svg : plot_matplotlib_%.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_matplotlib_$*.py --log-level INFO --style dark --output-file $@

../docs/images/plot_matplotlib_%_light.svg : plot_matplotlib_%.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_matplotlib_$*.py --log-level INFO --style light --output-file $@

snippets/plot_plotly_%.html : plot_plotly_%.py _plotly.py ../dyce/*.py ../dyce/viz/plotly.py
	"$${PYTHON:-python3}" plot_plotly_$*.py --log-level INFO --output-file $@

perf_%.txt : perf_%.ipy ../dyce/*.py ../dyce/*/*.py
	ipython3 --no-banner --quick --LoggingMagics.quiet=True perf_$*.ipy | tee $@

# Prints the pinned "none-any" wheel URL for each package named on the
# command line.
UV_LOCK_WHEELS = "$${PYTHON:-python3}" -c 'import sys, tomllib; packages = tomllib.load(open("uv.lock", "rb"))["package"]; print("\n".join(next(w["url"] for p in packages if p["name"] == pkg_name for w in p.get("wheels", []) if "none-any" in w["url"]) for pkg_name in sys.argv[1:]))'

jupyterlite : FORCE \
	../docs/notebooks/2d6_lo_hi.ipynb \
	../docs/notebooks/3d6_selection.ipynb \
	../docs/notebooks/4d6_variants.ipynb \
	../docs/notebooks/advantage.ipynb \
	../docs/notebooks/burning_arch.ipynb \
	../docs/notebooks/d10_explode.ipynb \
	../docs/notebooks/d20_success.ipynb \
	../docs/notebooks/dupes.ipynb \
	../docs/notebooks/great_weapon_fighting.ipynb \
	../docs/notebooks/ironsworn.ipynb \
	../docs/notebooks/risus.ipynb \
	../docs/notebooks/roll_and_keep.ipynb
	cd .. && uv build --wheel
	@cd .. && set -eu; \
		dyce_wheel=$$(ls -t dist/dyce*-none-any.whl | head -n 1); \
		test -f "$$dyce_wheel"; \
		optype_wheel=$$($(UV_LOCK_WHEELS) optype); \
		jupyter lite build --debug --output-dir docs/jupyter \
			--piplite-wheels "$$dyce_wheel" --piplite-wheels "$$optype_wheel"

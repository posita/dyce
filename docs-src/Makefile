all : \
	../docs/dyce-powered.svg \
	../docs/notebooks/2d6_lo_hi.ipynb \
	../docs/notebooks/4d6_variants.ipynb \
	../docs/notebooks/advantage.ipynb \
	../docs/notebooks/burning_arch.ipynb \
	../docs/notebooks/d10_explode.ipynb \
	../docs/notebooks/dupes.ipynb \
	../docs/notebooks/great_weapon_fighting.ipynb \
	../docs/notebooks/histogram.ipynb \
	../docs/notebooks/ironsworn.ipynb \
	../docs/notebooks/risus.ipynb \
	../docs/notebooks/roll_and_keep.ipynb \
	../docs/images/plot_2d6_lo_hi_dark.svg \
	../docs/images/plot_2d6_lo_hi_light.svg \
	../docs/images/plot_4d6_variants_dark.svg \
	../docs/images/plot_4d6_variants_light.svg \
	../docs/images/plot_advantage_dark.svg \
	../docs/images/plot_advantage_light.svg \
	../docs/images/plot_burning_arch_dark.svg \
	../docs/images/plot_burning_arch_light.svg \
	../docs/images/plot_d10_explode_dark.svg \
	../docs/images/plot_d10_explode_light.svg \
	../docs/images/plot_d4s_dark.svg \
	../docs/images/plot_d4s_light.svg \
	../docs/images/plot_dupes_dark.svg \
	../docs/images/plot_dupes_light.svg \
	../docs/images/plot_great_weapon_fighting_dark.svg \
	../docs/images/plot_great_weapon_fighting_light.svg \
	../docs/images/plot_histogram_dark.svg \
	../docs/images/plot_histogram_light.svg \
	../docs/images/plot_ironsworn_dark.svg \
	../docs/images/plot_ironsworn_light.svg \
	../docs/images/plot_risus_first_round_dark.svg \
	../docs/images/plot_risus_first_round_light.svg \
	../docs/images/plot_risus_multi_round_standard_dark.svg \
	../docs/images/plot_risus_multi_round_standard_light.svg \
	../docs/images/plot_roll_and_keep_dark.svg \
	../docs/images/plot_roll_and_keep_light.svg \
	../docs/images/plot_viz_plot_bar_dark.svg \
	../docs/images/plot_viz_plot_bar_light.svg \
	../docs/images/plot_viz_plot_burst_dark.svg \
	../docs/images/plot_viz_plot_burst_light.svg \
	../docs/images/plot_viz_plot_hbar_dark.svg \
	../docs/images/plot_viz_plot_hbar_light.svg \
	../docs/images/plot_viz_plot_line_dark.svg \
	../docs/images/plot_viz_plot_line_light.svg \
	../docs/images/plot_viz_plot_line_at_most_dark.svg \
	../docs/images/plot_viz_plot_line_at_most_light.svg \
	../docs/images/plot_viz_plot_line_at_least_dark.svg \
	../docs/images/plot_viz_plot_line_at_least_light.svg \
	../docs/images/plot_viz_plot_ridge_dark.svg \
	../docs/images/plot_viz_plot_ridge_light.svg \
	snippets/plotly_viz_plot_bar.html \
	snippets/plotly_viz_plot_hbar.html \
	snippets/plotly_viz_plot_line.html \
	snippets/plotly_viz_plot_line_at_least.html \
	snippets/plotly_viz_plot_line_at_most.html \
	snippets/plotly_viz_plot_ridge.html

perf : \
	perf_expand.txt \
	perf_rolls_with_counts.txt

# \
 # 	perf_pools_vs_rollers.txt

../docs/images/plot_risus_first_round_dark.svg \
../docs/images/plot_risus_multi_round_standard_dark.svg \
../docs/images/plot_risus_multi_round_best_of_set_dark.svg \
../docs/images/plot_risus_multi_round_evens_up_dark.svg &: plot_risus.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_risus.py --log-level INFO --style dark --output-dir ../docs/images

../docs/images/plot_risus_first_round_light.svg \
../docs/images/plot_risus_multi_round_standard_light.svg \
../docs/images/plot_risus_multi_round_best_of_set_light.svg \
../docs/images/plot_risus_multi_round_evens_up_light.svg &: plot_risus.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_risus.py --log-level INFO --style light --output-dir ../docs/images

../docs/notebooks/%.ipynb : nb_%.py
	jupytext --to notebook --update $< --output $@
	ruff check --fix $@
	ruff format $@

../docs/images/plot_%_dark.svg : plot_%.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_$*.py --log-level INFO --style dark --output-file $@

../docs/images/plot_%_light.svg : plot_%.py _plot.py ../dyce/*.py ../dyce/viz/matplotlib.py
	"$${PYTHON:-python3}" plot_$*.py --log-level INFO --style light --output-file $@

snippets/plotly_%.html : plotly_%.py _plotly.py ../dyce/*.py ../dyce/viz/plotly.py
	"$${PYTHON:-python3}" plotly_$*.py --log-level INFO --output-file $@

perf_%.txt : perf_%.ipy ../dyce/*.py ../dyce/*/*.py
	ipython3 --no-banner --quick --LoggingMagics.quiet=True perf_$*.ipy | tee $@

../docs/dyce-powered.svg : Makefile
	curl --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-%F0%9D%9A%8D%F0%9D%9A%A2%F0%9D%9A%8C%F0%9D%9A%8E--powered%21-gold'

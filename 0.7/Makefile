all : \
	dyce-powered.svg \
	notebooks/2d6_lo_hi.ipynb \
	notebooks/4d6_variants.ipynb \
	notebooks/advantage.ipynb \
	notebooks/burning_arch.ipynb \
	notebooks/d10_explode.ipynb \
	notebooks/dupes.ipynb \
	notebooks/great_weapon_fighting.ipynb \
	notebooks/histogram.ipynb \
	notebooks/ironsworn.ipynb \
	notebooks/risus.ipynb \
	notebooks/roll_and_keep.ipynb \
	assets/plot_2d6_lo_hi_dark.svg \
	assets/plot_2d6_lo_hi_light.svg \
	assets/plot_4d6_variants_dark.svg \
	assets/plot_4d6_variants_light.svg \
	assets/plot_advantage_dark.svg \
	assets/plot_advantage_light.svg \
	assets/plot_burning_arch_dark.svg \
	assets/plot_burning_arch_light.svg \
	assets/plot_d10_explode_dark.svg \
	assets/plot_d10_explode_light.svg \
	assets/plot_dupes_dark.svg \
	assets/plot_dupes_light.svg \
	assets/plot_great_weapon_fighting_dark.svg \
	assets/plot_great_weapon_fighting_light.svg \
	assets/plot_histogram_dark.svg \
	assets/plot_histogram_light.svg \
	assets/plot_ironsworn_dark.svg \
	assets/plot_ironsworn_light.svg \
	assets/plot_risus_first_round_dark.svg \
	assets/plot_risus_first_round_light.svg \
	assets/plot_risus_multi_round_standard_dark.svg \
	assets/plot_risus_multi_round_standard_light.svg \
	assets/plot_roll_and_keep_dark.svg \
	assets/plot_roll_and_keep_light.svg \
	assets/plot_viz_plot_bar_dark.svg \
	assets/plot_viz_plot_bar_light.svg \
	assets/plot_viz_plot_burst_dark.svg \
	assets/plot_viz_plot_burst_light.svg \
	assets/plot_viz_plot_hbar_dark.svg \
	assets/plot_viz_plot_hbar_light.svg \
	assets/plot_viz_plot_line_dark.svg \
	assets/plot_viz_plot_line_light.svg

# \
# 	assets/graph_classes_dyce_r_dark.svg \
# 	assets/graph_classes_dyce_r_light.svg \
# 	assets/graph_filter_dark.svg \
# 	assets/graph_filter_light.svg \
# 	assets/graph_rollin_value_dark.svg \
# 	assets/graph_rollin_value_light.svg \
# 	assets/graph_rollin_expr_dark.svg \
# 	assets/graph_rollin_expr_light.svg \
# 	assets/graph_rollin_pool_dark.svg \
# 	assets/graph_rollin_pool_light.svg \
# 	assets/graph_rollin_select_1_dark.svg \
# 	assets/graph_rollin_select_1_light.svg \
# 	assets/graph_rollin_select_2_dark.svg \
# 	assets/graph_rollin_select_2_light.svg \
# 	assets/graph_substitute_append_dark.svg \
# 	assets/graph_substitute_append_light.svg \
# 	assets/graph_substitute_replace_dark.svg \
# 	assets/graph_substitute_replace_light.svg

perf : \
	assets/perf_expand.txt \
	assets/perf_rolls_with_counts.txt

# \
 # 	assets/perf_pools_vs_rollers.txt

# assets/graph_%_dark.svg : assets/graph_%.py assets/Makefile assets/graph.py ../dyce/*.py
# 	"$${PYTHON:-python3}" assets/graph.py --style=dark $*

# assets/graph_%_light.svg : assets/graph_%.py assets/Makefile assets/graph.py ../dyce/*.py
# 	"$${PYTHON:-python3}" assets/graph.py --style=light $*

assets/plot_risus_first_round_dark.svg \
assets/plot_risus_multi_round_standard_dark.svg \
assets/plot_risus_multi_round_best_of_set_dark.svg \
assets/plot_risus_multi_round_evens_up_dark.svg &: assets/plot_risus.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_risus.py --log-level INFO --style dark --output-dir assets

assets/plot_risus_first_round_light.svg \
assets/plot_risus_multi_round_standard_light.svg \
assets/plot_risus_multi_round_best_of_set_light.svg \
assets/plot_risus_multi_round_evens_up_light.svg &: assets/plot_risus.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_risus.py --log-level INFO --style light --output-dir assets

assets/plot_%_dark.png : assets/plot_%.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_$*.py --log-level INFO --style dark --output-file $@

assets/plot_%_dark.svg : assets/plot_%.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_$*.py --log-level INFO --style dark --output-file $@

assets/plot_%_light.png : assets/plot_%.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_$*.py --log-level INFO --style light --output-file $@

assets/plot_%_light.svg : assets/plot_%.py assets/_plot.py ../dyce/*.py
	"$${PYTHON:-python3}" assets/plot_$*.py --log-level INFO --style light --output-file $@

notebooks/%.ipynb : assets/nb_%.py
	jupytext --to notebook --update $< --output $@
	ruff check --fix $@
	ruff format $@

assets/perf_%.txt : assets/perf_%.ipy ../dyce/*.py
	ipython3 --no-banner --quick --LoggingMagics.quiet=True assets/perf_$*.ipy | tee $@

dyce-powered.svg : Makefile
	curl --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-%F0%9D%9A%8D%F0%9D%9A%A2%F0%9D%9A%8C%F0%9D%9A%8E--powered%21-gold'

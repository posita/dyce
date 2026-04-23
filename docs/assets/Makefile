all : \
	../dyce-powered.svg \
	plot_2d6_lo_hi_dark.png \
	plot_2d6_lo_hi_light.png \
	plot_4d6_variants_dark.png \
	plot_4d6_variants_light.png \
	plot_advantage_dark.png \
	plot_advantage_light.png \
	plot_burning_arch_dark.png \
	plot_burning_arch_light.png \
	plot_d10_explode_dark.png \
	plot_d10_explode_light.png \
	plot_dupes_dark.png \
	plot_dupes_light.png \
	plot_great_weapon_fighting_dark.png \
	plot_great_weapon_fighting_light.png \
	plot_histogram_dark.png \
	plot_histogram_light.png \
	plot_ironsworn_dark.png \
	plot_ironsworn_light.png \
	plot_risus_first_round_dark.png \
	plot_risus_first_round_light.png \
	plot_roll_and_keep_dark.png \
	plot_roll_and_keep_light.png \
	plot_viz_plot_bar_dark.png \
	plot_viz_plot_bar_light.png \
	plot_viz_plot_burst_dark.png \
	plot_viz_plot_burst_light.png \
	plot_viz_plot_hbar_dark.png \
	plot_viz_plot_hbar_light.png \
	plot_viz_plot_line_dark.png \
	plot_viz_plot_line_light.png

# \
# 	graph_classes_dyce_r_dark.svg \
# 	graph_classes_dyce_r_light.svg \
# 	graph_filter_dark.svg \
# 	graph_filter_light.svg \
# 	graph_rollin_value_dark.svg \
# 	graph_rollin_value_light.svg \
# 	graph_rollin_expr_dark.svg \
# 	graph_rollin_expr_light.svg \
# 	graph_rollin_pool_dark.svg \
# 	graph_rollin_pool_light.svg \
# 	graph_rollin_select_1_dark.svg \
# 	graph_rollin_select_1_light.svg \
# 	graph_rollin_select_2_dark.svg \
# 	graph_rollin_select_2_light.svg \
# 	graph_substitute_append_dark.svg \
# 	graph_substitute_append_light.svg \
# 	graph_substitute_replace_dark.svg \
# 	graph_substitute_replace_light.svg

perf : \
	perf_expand.txt \
	perf_rolls_with_counts.txt

# \
 # 	perf_pools_vs_rollers.txt

graph_%_dark.svg : graph_%.py Makefile graph.py ../../dyce/*.py
	"$${PYTHON:-python3}" graph.py --style=dark $*

graph_%_light.svg : graph_%.py Makefile graph.py ../../dyce/*.py
	"$${PYTHON:-python3}" graph.py --style=light $*

plot_%_dark.png : plot_%.py Makefile _plot.py ../../dyce/*.py
	"$${PYTHON:-python3}" plot_$*.py --log-level INFO --style=dark

plot_%_light.png : plot_%.py Makefile _plot.py ../../dyce/*.py
	"$${PYTHON:-python3}" plot_$*.py --log-level INFO --style=light

perf_%.txt : perf_%.ipy Makefile ../../dyce/*.py
	ipython3 --no-banner --quick --LoggingMagics.quiet=True perf_$*.ipy | tee $@

../dyce-powered.svg : Makefile
	curl --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-%F0%9D%9A%8D%F0%9D%9A%A2%F0%9D%9A%8C%F0%9D%9A%8E--powered%21-gold'

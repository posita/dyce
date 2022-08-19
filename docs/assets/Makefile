all : \
	graph_classes_dyce_r_dark.svg \
	graph_classes_dyce_r_light.svg \
	graph_filter_dark.svg \
	graph_filter_light.svg \
	graph_rollin_value_dark.svg \
	graph_rollin_value_light.svg \
	graph_rollin_expr_dark.svg \
	graph_rollin_expr_light.svg \
	graph_rollin_pool_dark.svg \
	graph_rollin_pool_light.svg \
	graph_rollin_select_1_dark.svg \
	graph_rollin_select_1_light.svg \
	graph_rollin_select_2_dark.svg \
	graph_rollin_select_2_light.svg \
	graph_substitute_append_dark.svg \
	graph_substitute_append_light.svg \
	graph_substitute_replace_dark.svg \
	graph_substitute_replace_light.svg \
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
	plot_roll_and_keep_light.png

perf : \
	perf_appearances_in_rolls.txt \
	perf_foreach.txt \
	perf_pools_vs_rollers.txt \
	perf_rolls_with_counts.txt

graph_%_dark.svg : graph_%.py Makefile graph.py ../../dyce/h.py ../../dyce/p.py ../../dyce/r.py
	"$${PYTHON:-python}" graph.py --style=dark $*

graph_%_light.svg : graph_%.py Makefile graph.py ../../dyce/h.py ../../dyce/p.py ../../dyce/r.py
	"$${PYTHON:-python}" graph.py --style=light $*

plot_%_dark.png : plot_%.py Makefile plot.py ../../dyce/h.py ../../dyce/p.py
	"$${PYTHON:-python}" plot.py --style=dark $*

plot_%_light.png : plot_%.py Makefile plot.py ../../dyce/h.py ../../dyce/p.py
	"$${PYTHON:-python}" plot.py --style=light $*

perf_%.txt : perf_%.ipy Makefile ../../dyce/h.py ../../dyce/p.py ../../dyce/r.py
	ipython >$@ --no-banner --quick --LoggingMagics.quiet=True perf_$*.ipy

../dyce-powered.svg : Makefile
	curl --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-%F0%9D%9A%8D%F0%9D%9A%A2%F0%9D%9A%8C%F0%9D%9A%8E--powered%21-gold'

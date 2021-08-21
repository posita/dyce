all : \
	graph_classes_dyce_r_dark.svg \
	graph_classes_dyce_r_light.svg \
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
	graph_rollin_select_3_dark.svg \
	graph_rollin_select_3_light.svg \
	plot_2d6_lo_hi_gh.png \
	plot_4d6_variants_dark.png \
	plot_4d6_variants_light.png \
	plot_advantage_dark.png \
	plot_advantage_light.png \
	plot_burning_arch_dark.png \
	plot_burning_arch_light.png \
	plot_burst_1_dark.png \
	plot_burst_1_light.png \
	plot_burst_2_dark.png \
	plot_burst_2_light.png \
	plot_burst_3_dark.png \
	plot_burst_3_light.png \
	plot_d10_explode_dark.png \
	plot_d10_explode_light.png \
	plot_dupes_dark.png \
	plot_dupes_light.png \
	plot_great_weapon_fighting_dark.png \
	plot_great_weapon_fighting_light.png \
	plot_histogram_dark.png \
	plot_histogram_light.png \
	plot_risus_first_round_dark.png \
	plot_risus_first_round_light.png \
	plot_roll_and_keep_dark.png \
	plot_roll_and_keep_light.png

plot_%_dark.png : plot_%.py Makefile plot.py ../../dyce/h.py ../../dyce/p.py ../../dyce/viz.py
	"$${PYTHON:-python}" plot.py --style=dark $*

plot_%_light.png : plot_%.py Makefile plot.py ../../dyce/h.py ../../dyce/p.py ../../dyce/viz.py
	"$${PYTHON:-python}" plot.py --style=light $*

# TODO(posita): This should go away at some point. (See TODO in plot.py.)
plot_%_gh.png : plot_%.py Makefile plot.py ../../dyce/h.py ../../dyce/p.py ../../dyce/viz.py
	"$${PYTHON:-python}" plot.py --style=gh $*

graph_%_dark.svg : graph_%.py Makefile graph.py ../../dyce/h.py ../../dyce/p.py ../../dyce/r.py ../../dyce/viz.py
	"$${PYTHON:-python}" graph.py --style=dark $*

graph_%_light.svg : graph_%.py Makefile graph.py ../../dyce/h.py ../../dyce/p.py ../../dyce/r.py ../../dyce/viz.py
	"$${PYTHON:-python}" graph.py --style=light $*

../dyce-powered.svg : Makefile
	curl --output $@ 'https://img.shields.io/badge/%F0%9F%92%A5%F0%9F%8E%B2-dyce--powered%21-gold'

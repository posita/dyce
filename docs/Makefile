all : \
	plot_2d6_lo_hi_gh.png \
	plot_4d6_variants_gh.png \
	plot_advantage_gh.png \
	plot_burning_arch_gh.png \
	plot_burst_1_dark.png \
	plot_burst_1_light.png \
	plot_burst_2_dark.png \
	plot_burst_2_light.png \
	plot_d10_explode_gh.png \
	plot_dupes_gh.png \
	plot_great_weapon_fighting_gh.png \
	plot_histogram_dark.png \
	plot_histogram_light.png \
	plot_risus_first_round_dark.png \
	plot_risus_first_round_light.png

plot_%_dark.png : plot_%.py Makefile plot.py ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" plot.py --style=dark $*

plot_%_light.png : plot_%.py Makefile plot.py ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" plot.py --style=light $*

# See TODO in plot.py
plot_%_gh.png : plot_%.py Makefile plot.py ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" plot.py --style=gh $*

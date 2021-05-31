all : \
	plot_2d6_lo_hi_dark.png \
	plot_2d6_lo_hi_light.png \
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
	plot_d10_explode_dark.png \
	plot_d10_explode_light.png \
	plot_dupes_dark.png \
	plot_dupes_light.png \
	plot_great_weapon_fighting_dark.png \
	plot_great_weapon_fighting_light.png \
	plot_histogram_dark.png \
	plot_histogram_light.png \
	plot_risus_first_round_dark.png \
	plot_risus_first_round_light.png

plot_%_dark.png : plot_%.py Makefile ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" plot.py --style=dark $*

plot_%_light.png : plot_%.py Makefile ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" plot.py --style=light $*

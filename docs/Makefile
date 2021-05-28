all : \
	plot_2d6_lo_hi.png \
	plot_4d6_variants.png \
	plot_advantage.png \
	plot_burning_arch.png \
	plot_burst_1.png \
	plot_burst_2.png \
	plot_d10_explode.png \
	plot_dupes.png \
	plot_great_weapon_fighting.png \
	plot_histogram.png \
	plot_risus_first_round.png

%.png : %.py Makefile ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" $<

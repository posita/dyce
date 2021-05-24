all : plot_burst_1.png plot_burst_2.png plot_histogram.png plot_risus_first_round.png

%.png : %.py Makefile ../dyce/h.py ../dyce/p.py ../dyce/plt.py
	"$${PYTHON:-python}" $<

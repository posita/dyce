all : plot_burst_1.png plot_burst_2.png

%.png : %.py Makefile ../dyce/lib.py ../dyce/plt.py
	"$${PYTHON:-python}" $<

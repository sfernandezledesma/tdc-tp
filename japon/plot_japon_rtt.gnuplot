set title "Tiempos entre nodos para www.abu.ac.jp"
set key below
set multiplot

set xrange [0:11]

f(x) = a
fit f(x) 'datos_japon_rtt.txt' via a

plot 'datos_japon_rtt.txt' using 1:2 with points pt 5 title "Tiempos entre nodos (ms)", f(x) title "Promedio de tiempos (ms)"

pause -1 "asd"

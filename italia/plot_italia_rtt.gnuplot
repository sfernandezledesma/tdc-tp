set title "Tiempos entre nodos para santannapisa.it"
set key below
set multiplot

f(x) = a
fit f(x) 'datos_italia_rtt.txt' via a

plot 'datos_italia_rtt.txt' using 1:2 with points pt 5 title "Tiempos entre nodos (ms)", f(x) title "Promedio de tiempos (ms)"

pause -1 "asd"

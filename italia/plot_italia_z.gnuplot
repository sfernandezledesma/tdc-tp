set title "Valores Z para santannapisa.it"
set key below
set multiplot

f(x) = a
fit f(x) 'datos_italia_z.txt' via a

plot 'datos_italia_z.txt' using 1:2 with points pt 5 title "Valores Z", f(x) title "Media"

pause -1 "asd"
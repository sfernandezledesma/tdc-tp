import time
from scapy.all import sr
from scapy.layers.inet import IP, UDP, TCP, ICMP

def time_ms():
  return int(time.time_ns() / 1000000)

def ping(destino, time_to_live, time_out=1, verboso=False):
  return sr(IP(dst=destino, ttl=time_to_live)/ICMP(), timeout=time_out, verbose=verboso)

def pingUDP(destino, time_to_live, time_out=1, verboso=False):
  return sr(IP(dst=destino, ttl=time_to_live)/UDP(), timeout=time_out, verbose=verboso)

def miPing(destino, time_to_live, time_out=1, verboso=False):
  start_time_ms = time_ms()
  ans, unans = ping(destino, time_to_live, time_out, verboso)
  round_trip_time_ms = time_ms() - start_time_ms
  if len(ans[ICMP]) > 0:
    return [ans, round_trip_time_ms]
  else:
    start_time_ms = time_ms()
    ans, unans = pingUDP(destino, time_to_live, time_out, verboso)
    round_trip_time_ms = time_ms() - start_time_ms
    return [ans, round_trip_time_ms]

def traceroute(destino, maximo_ttl=40, timeout_sec=1, verboso=False):
  times = []
  ttl=1
  ip = ''
  while ttl <= maximo_ttl and ip != destino:
    res, round_trip_time_ms = miPing(destino, ttl, timeout_sec, verboso)
    if (round_trip_time_ms < timeout_sec * 1000): # solo estoy guardando los que respondieron
      ip = res[0][1].src
      times.append( (ttl, round_trip_time_ms, ip) ) # TTL, RTT, IP destino (res[0][0][1] es el paquete que llega)
    ttl = ttl+1      
  return times

def trace_n_veces(destino, maximo_ttl=40, timeout_sec=1, verboso=False, cantidad_mediciones=30):
  lista_times = []
  for i in range(cantidad_mediciones):
    lista_times.append(traceroute(destino, maximo_ttl, timeout_sec, verboso))
  return lista_times

def imprimir_mediciones(ip_destino, lista_times):
  timesArray = lista_times
  print("Deltas entre nodos que respondieron:")
  ttl_nodo_ant = 0
  rtt_nodo_ant = 0
  ttlpad   = 4
  ippad    = 17
  rttpad   = 10
  deltapad = 25
  estpad   = 5
  print(
    ("TTL".ljust(ttlpad," "))+
    ("IP".ljust(ippad," "))+
    ("RTT(ms)".ljust(rttpad," "))+
    ("RTT(i)-RTT(i-1) (ms)".ljust(deltapad," "))+
    ("Estimado".ljust(estpad," "))
  )
  for j in range(len(timesArray)):
    times = timesArray[j]
    ttl_nodo, rtt_nodo, ip_nodo  = [0, 0, '']
    i = 0
    while ip_nodo != ip_destino and i < len(times):
      ttl_nodo, rtt_nodo, ip_nodo = times[i]
      i = i+1
      ttl_dif = ttl_nodo - ttl_nodo_ant
      # estimado = ttl_dif > 1
      delta = int((rtt_nodo - rtt_nodo_ant)/ttl_dif)
      for ttl_j in range(ttl_nodo_ant+1,ttl_nodo):
        print(
          (f"{ttl_j}".rjust(2," ").ljust(ttlpad," "))+
          (f"*".ljust(ippad," "))+
          (f"*".rjust(3," ").ljust(rttpad," "))+
          (f"{delta}".rjust(4," ").ljust(deltapad," "))+
          (f"SI".ljust(estpad," "))
        )
      print(
          (f"{ttl_nodo}".rjust(2," ").ljust(ttlpad," "))+
          (f"{ip_nodo}".ljust(ippad," "))+
          (f"{rtt_nodo}".rjust(3," ").ljust(rttpad," "))+
          (f"{delta}".rjust(4," ").ljust(deltapad," "))+
          (f"NO".ljust(estpad," "))
        )
      ttl_nodo_ant, rtt_nodo_ant = [ttl_nodo, rtt_nodo]

def promediar_tiempo_entre_nodos(ip_destino, n_mediciones, minima_cantidad_mediciones_para_promediar=10):
  acum = {} # diccionario que va a tener a guardar (IP_1, IP_2) : (suma_tiempo_entre_ambos, cantidad_sumas)
  for medicion_tiempos in n_mediciones: # medicion_tiempos = lista de (TTL, RTT, IP destino)
    for i in range(1, len(medicion_tiempos)):
      # Me interesan solo los pares de nodos cuyas IP conocemos, o sea, los que respondieron y tienen TTL contiguo
      nodo_anterior = medicion_tiempos[i-1]
      nodo_actual = medicion_tiempos[i]
      ttl_anterior, rtt_anterior, ip_anterior = nodo_anterior
      ttl_actual, rtt_actual, ip_actual = nodo_actual
      diferencia_rtt = rtt_actual - rtt_anterior
      if (ttl_anterior + 1 == ttl_actual):
        enlace = (ip_anterior, ip_actual) # la clave es la tupla de IPs
        if enlace in acum:
          acum[enlace] = (acum[enlace][0] + diferencia_rtt, acum[enlace][1] + 1)
        else:
          acum[enlace] = (diferencia_rtt, 1)
  # Ahora promedio pero sacando los tiempos que se midieron muy pocas veces, para no promediar entre pocos valores
  promedio = {}
  for k, v in acum.items():
    if v[1] >= minima_cantidad_mediciones_para_promediar:
      promedio[k] = int(v[0] / v[1])
  return promedio


univ_japonesa = "www.abu.ac.jp"
ip_univ_japonesa = "183.90.238.55"
cantidad_mediciones = 30
li_times = trace_n_veces(ip_univ_japonesa, cantidad_mediciones=cantidad_mediciones)
#imprimir_mediciones(ip_univ_japonesa, li_times)
resultados = promediar_tiempo_entre_nodos(ip_univ_japonesa, li_times)
print(resultados)
# Promedio tiempo entre nodos para 30 mediciones:
# {
#   ('200.89.165.250', '185.70.203.32'): -10, 
#   ('129.250.6.85', '129.250.4.13'): 42, 
#   ('129.250.4.13', '129.250.6.30'): -13, 
#   ('129.250.6.30', '129.250.3.61'): 93, 
#   ('129.250.3.61', '129.250.7.31'): 0, 
#   ('129.250.7.31', '129.250.3.210'): 2, 
#   ('129.250.3.210', '61.200.91.186'): -7, 
#   ('210.188.213.76', '183.90.238.55'): 6, 
#   ('149.3.181.65', '129.250.2.12'): 132, 
#   ('129.250.2.12', '129.250.6.85'): 4
# }
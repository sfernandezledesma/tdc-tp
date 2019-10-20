import time, math
from scipy.stats import t
from scapy.all import sr
from scapy.layers.inet import IP, UDP, TCP, ICMP

def modified_thompson_tau(n):
  t_alpha_sobre_2 = t.ppf(0.975, n-2)
  return t_alpha_sobre_2 * (n - 1) / (math.sqrt(n) * math.sqrt(n - 2 + t_alpha_sobre_2 ** 2))

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

def promediar_tiempo_entre_nodos(ip_destino, n_mediciones, minima_cantidad_mediciones_para_promediar=2):
  acum = {} # diccionario que va a tener a guardar (IP_1, IP_2) : (suma_tiempo_entre_ambos, cantidad_sumas, ttl_2)
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
          acum[enlace] = (acum[enlace][0] + diferencia_rtt, acum[enlace][1] + 1, ttl_actual)
        else:
          acum[enlace] = (diferencia_rtt, 1, ttl_actual)
  # Ahora promedio pero sacando los tiempos negativos y los que se midieron muy pocas veces
  promedio = {}
  for k, v in acum.items():
    suma_tiempo_entre_ambos, cantidad_mediciones, ttl2 = v
    media = int(suma_tiempo_entre_ambos / cantidad_mediciones)
    if media >= 0 and cantidad_mediciones >= minima_cantidad_mediciones_para_promediar:
      promedio[k] = (media, ttl2)
  return promedio # dicc de (IP1,IP2): (promedio_tiempo_entre_nodos, TTL2)   Notar que TTL1 = TTL2 - 1

def reemplazar_rtt_de_cada_ip_por_el_minimo(n_mediciones):
  minimo_rtt_para_ip = {} # diccionario que va a guardar IP:minimo_rtt
  for medicion_tiempos in n_mediciones: # medicion_tiempos = lista de (TTL, RTT, IP destino)
    for ttl, rtt, ip in medicion_tiempos:
      if ip in minimo_rtt_para_ip:
        minimo_rtt_para_ip[ip] = rtt if rtt < minimo_rtt_para_ip[ip] else minimo_rtt_para_ip[ip]
      else:
        minimo_rtt_para_ip[ip] = rtt
  for medicion_tiempos in n_mediciones: # medicion_tiempos = lista de (TTL, RTT, IP destino)
    for i in range(len(medicion_tiempos)): # v = (TTL, RTT, IP destino)
      ttl, rtt, ip = medicion_tiempos[i]
      medicion_tiempos[i] = (ttl, minimo_rtt_para_ip[ip], ip)

def resultados_normalizados(res):
  res_norm = {}
  media = 0
  n = len(res)
  for tiempo_entre_nodos, ttl2 in res.values():
    media += tiempo_entre_nodos
  media = media / n

  desvio_estandar = 0
  for tiempo_entre_nodos, ttl2 in res.values():
    desvio_estandar += (tiempo_entre_nodos - media) ** 2
  desvio_estandar = (desvio_estandar / n) ** 0.5
  desvio_estandar = desvio_estandar if desvio_estandar != 0 else 1

  for k, v in res.items():
    tiempo_entre_nodos, ttl2 = v
    tiempo_normalizado = (tiempo_entre_nodos - media) / desvio_estandar
    res_norm[k] = (tiempo_normalizado, ttl2)
  return res_norm

def detectar_enlaces_intercontinentales(res):
  copia_res = dict(res)
  outliers = {}
  media_total = 0
  for tiempo_entre_nodos, ttl2 in res.values():
    media_total += tiempo_entre_nodos
  media_total = media_total / len(res)

  puede_haber_outliers = True
  while puede_haber_outliers:
    media = 0
    n = len(copia_res)
    for tiempo_entre_nodos, ttl2 in copia_res.values():
      media += tiempo_entre_nodos
    media = media / n

    desvio_estandar = 0
    for tiempo_entre_nodos, ttl2 in copia_res.values():
      desvio_estandar += (tiempo_entre_nodos - media) ** 2
    desvio_estandar = (desvio_estandar / n) ** 0.5
    
    mayor_delta_i = -1
    key_mayor_delta_i = None
    
    for k, v in  copia_res.items():
      tiempo_entre_nodos, ttl2 = v
      delta_i = abs(tiempo_entre_nodos - media)
      if delta_i > mayor_delta_i and tiempo_entre_nodos > media_total: # Pido que el candidato sea mayor a la media total
        mayor_delta_i = delta_i
        key_mayor_delta_i = k
    
    if key_mayor_delta_i and mayor_delta_i > modified_thompson_tau(n) * desvio_estandar: # Es outlier
      outliers[key_mayor_delta_i] = copia_res[key_mayor_delta_i]
      copia_res.pop(key_mayor_delta_i) # Lo saco y calculo todo de nuevo sin ese elemento
    else: # No es outlier, por lo tanto no hay mas
      puede_haber_outliers = False
  
  return outliers

ip_univ_japonesa = "183.90.238.55" # www.abu.ac.jp
ip_univ_italiana = "193.205.80.112" # santannapisa.it
ip_univ_australiana = "43.245.43.59" # unimelb.edu.au
ip = ip_univ_japonesa
cantidad_mediciones = 10

li_tiempos = trace_n_veces(ip, cantidad_mediciones=cantidad_mediciones)

# reemplazar_rtt_de_cada_ip_por_el_minimo(li_tiempos)
imprimir_mediciones(ip, li_tiempos)

resultados = promediar_tiempo_entre_nodos(ip, li_tiempos, cantidad_mediciones // 2)
print("TTL1\tTTL2\tIP1\t\t\tIP2\t\t\tTiempo entre nodos")
for k, v in resultados.items():
  ip1, ip2 = k
  tiempo_entre_nodos, ttl2 = v
  ttl1 = ttl2 - 1
  print(f"{ttl1}\t{ttl2}\t{ip1}\t\t{ip2}\t\t{tiempo_entre_nodos} ms")

res_normalizados = resultados_normalizados(resultados)
print("TTL1\tTTL2\tIP1\t\t\tIP2\t\t\tValor Z")
for k, v in res_normalizados.items():
  ip1, ip2 = k
  tiempo_entre_nodos, ttl2 = v
  ttl1 = ttl2 - 1
  print(f"{ttl1}\t{ttl2}\t{ip1}\t\t{ip2}\t\t{tiempo_entre_nodos}")

outliers = detectar_enlaces_intercontinentales(resultados)
print("OUTLIERS USANDO CIMBALA:")
print("========================")
print("TTL1\tTTL2\tIP1\t\t\tIP2\t\t\tTiempo entre nodos")
for k, v in outliers.items():
  ip1, ip2 = k
  tiempo_entre_nodos, ttl2 = v
  ttl1 = ttl2 - 1
  print(f"{ttl1}\t{ttl2}\t{ip1}\t\t{ip2}\t\t{tiempo_entre_nodos} ms")

outliers = detectar_enlaces_intercontinentales(res_normalizados)
print("OUTLIERS PARA RESULTADOS NORMALIZADOS:")
print("======================================")
print("TTL1\tTTL2\tIP1\t\t\tIP2\t\t\tValor Z")
for k, v in outliers.items():
  ip1, ip2 = k
  tiempo_entre_nodos, ttl2 = v
  ttl1 = ttl2 - 1
  print(f"{ttl1}\t{ttl2}\t{ip1}\t\t{ip2}\t\t{tiempo_entre_nodos}")
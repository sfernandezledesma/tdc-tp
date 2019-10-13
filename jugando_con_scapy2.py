from scapy.all import *
import time

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
  if len(ans[ICMP])>0:
    return [ans, round_trip_time_ms]
  else:
    start_time_ms = time_ms()
    ans, unans = pingUDP(destino, time_to_live, time_out, verboso)
    round_trip_time_ms = time_ms() - start_time_ms
    return [ans, round_trip_time_ms]

def traceroute(destino, maximo_ttl, timeout_sec, verboso):
  times = []
  ttl=1
  ip = ''
  while ttl <= maximo_ttl and ip != destino:
    """for ttl in range(1, maximo_ttl + 1):"""
    res, round_trip_time_ms = miPing(destino, ttl, timeout_sec, verboso)
    if (round_trip_time_ms < timeout_sec * 1000): # solo estoy guardando los que respondieron
      ip = res[0][1].src
      times.append( (ttl, round_trip_time_ms, ip) ) # TTL, RTT, IP destino (res[0][0][1] es el paquete que llega)
    ttl = ttl+1      
  return times

univ_japonesa = "www.abu.ac.jp"
ip_univ_japonesa = "183.90.238.55"
maximo_ttl = 40
timeout_sec = 1
verboso = False
timesArray = []
vecesTR = 30
for i in range(0,vecesTR):
  timesArray.append(traceroute(ip_univ_japonesa, maximo_ttl, timeout_sec, verboso))

"""print("Tiempos totales para cada TTL que respondió:")
print("TTL \t RTT")
for d in times:
  ttl = d[0]
  total_time = d[1]
  print(f"{ttl} \t {total_time} ms")
"""
print("Deltas entre nodos que respondieron:")
"""print("TTL\tIP\t\t\t\tTTL\tIP\t\t\t\tRTT(i)-RTT(i-1)")"""
"""for i in range(1,len(times)):
  ttl_nodo_1, rtt_nodo_1, ip_nodo_1 = times[i-1]
  ttl_nodo_2, rtt_nodo_2, ip_nodo_2 = times[i]
  delta = abs(rtt_nodo_2 - rtt_nodo_1)
  print(f"{ttl_nodo_1}\t{ip_nodo_1}\t\t\t{ttl_nodo_2}\t{ip_nodo_2}\t\t\t{delta} ms")
"""
ttl_nodo_ant = 0
rtt_nodo_ant = 0
"""print("TTLIP\t\t\t\tRTT\tRTT(i)-RTT(i-1)\tEstimado")"""
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
for j in range(0,len(timesArray)):
  times = timesArray[j]
  ttl_nodo, rtt_nodo, ip_nodo  = [0, 0, '']
  i = 0
  while ip_nodo != ip_univ_japonesa and i < len(times):
    ttl_nodo, rtt_nodo, ip_nodo = times[i]
    i = i+1
    ttl_dif = ttl_nodo - ttl_nodo_ant
    estimado = ttl_dif > 1
    delta = int((rtt_nodo - rtt_nodo_ant)/ttl_dif)
    for ttl_j in  range(ttl_nodo_ant+1,ttl_nodo):
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
  
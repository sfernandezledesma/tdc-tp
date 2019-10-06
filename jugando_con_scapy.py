from scapy.all import sr
from scapy.layers.inet import IP, ICMP
import time

def time_ms():
  return int(time.time_ns() / 1000000)

def ping(destino, time_to_live, time_out=1, verboso=False):
  return sr(IP(dst=destino, ttl=time_to_live)/ICMP(), timeout=time_out, verbose=verboso)

def traceroute(destino, maximo_ttl, timeout_sec, verboso):
  times = []
  for ttl in range(1, maximo_ttl + 1):
    start_time_ms = time_ms()
    res = ping(destino, ttl, timeout_sec, verboso)
    round_trip_time_ms = time_ms() - start_time_ms
    if (round_trip_time_ms < timeout_sec * 1000): # solo estoy guardando los que respondieron
      times.append((ttl, round_trip_time_ms, res[0][0][1].src)) # TTL, RTT, IP destino (res[0][0][1] es el paquete que llega)
  return times


univ_japonesa = "www.abu.ac.jp"
maximo_ttl = 25
timeout_sec = 1
verboso = False
times = traceroute(univ_japonesa, maximo_ttl, timeout_sec, verboso)

print("Tiempos totales para cada TTL que respondió:")
print("TTL \t RTT")
for d in times:
  ttl = d[0]
  total_time = d[1]
  print(f"{ttl} \t {total_time} ms")

print("Deltas entre nodos que respondieron:")
print("TTL\tIP\t\t\t\tTTL\tIP\t\t\t\tRTT(i)-RTT(i-1)")
for i in range(1,len(times)):
  ttl_nodo_1, rtt_nodo_1, ip_nodo_1 = times[i-1]
  ttl_nodo_2, rtt_nodo_2, ip_nodo_2 = times[i]
  delta = abs(rtt_nodo_2 - rtt_nodo_1)
  print(f"{ttl_nodo_1}\t{ip_nodo_1}\t\t\t{ttl_nodo_2}\t{ip_nodo_2}\t\t\t{delta} ms")

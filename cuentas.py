import csv
from math import sqrt
from scipy.stats import t

class EchoResult:
    def __init__(self,ttl,ip,rtt,ejecucion=None):
        self.ejecucion = ejecucion
        self.ttl = ttl
        self.ip = ip
        self.rtt = rtt
        self.mediaDif = None
    def __str__(self):
        return "e: %s, ttl: %s, ip: %s, rtt: %s, |x-X|: %s"%(self.ejecucion,self.ttl,self.ip,self.rtt, self.mediaDif)

results = []

with open('datos.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    ejecucion = 1
    _ttl = 0
    for row in csv_reader:
        ttl = int(row[0])
        ip = row[1]
        if ttl < _ttl:
            ejecucion = ejecucion+1
        if row[2] != "*":
            rtt = int(row[2])
        else: 
            rtt = '*'
        _ttl = ttl
        results.append(EchoResult(ttl,ip,rtt,ejecucion))

def filtrarTtl(lista,ttl):
    return filter(lambda x : x.ttl == ttl and x.ip != '*',lista)

def suma(lista):
    return reduce(lambda a,b : a+b,lista)

def promedio(lista):
    return suma(lista)/len(lista)

def desvioEstandarYPromedio(lista):
    n = len(lista)
    X = promedio(lista)
    sum = suma(map(lambda x : pow(abs(x - X),2),lista))
    s = sqrt(sum/n-1)
    return (s,X)

def calcularMediaYDesvioEstandar(lista):
    rtts = map(lambda echoResult : echoResult.rtt, lista)
    return (promedio(rtts), desvioEstandar(rtts))

def talfa(alpha,n):
    talfa_2 = t.pdf(alpha, df=n-2, scale=2)
    sqrtn = sqrt(n)
    sqrt_ = sqrt((n-2)+pow(talfa_2,2))
    ret = (talfa_2*(n-1))/(sqrtn*sqrt_)
    return ret

def descarta(x,X,s,ta):
    return abs(x-X) > ta*s

def ordernarERPor_dif(listaER,X):
    rtts = map(lambda echoResult : echoResult.rtt, listaER)
    return sorted(listaER, key=lambda er : abs(er.rtt-X),reverse=True)

def sarasaTTL(listaER, ttl):
    listaValidos = filtrarTtl(listaER, ttl)
    if len(listaValidos) > 1:
        rtts = map(lambda echoResult : echoResult.rtt, listaValidos)
        s, X = desvioEstandarYPromedio(rtts)
        a = ordernarERPor_dif(listaValidos,X)[0]
        print(descarta(a.rtt,X,s,talfa(0.05,len(listaValidos))))

def calcularMediaYDesvioEstandarTtl(lista, ttl):
    listaValidos = filtrarTtl(lista, ttl)
    if len(listaValidos) > 1:
        ret = calcularMediaYDesvioEstandar(listaValidos)
    else:
        ret = (None, None)
    return ret

alpha = 0.05

"""print(calcularMediaYDesvioEstandarTtl(results,28))"""
"""print(calcularTodosMediaYDesvioEstandar(results,40))"""
sarasaTTL(results,1)



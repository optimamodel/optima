""" Run optima.py to create the D structure, then run this """

from time import time
from model import model as modelnew
from model0 import model as modelold

t = time()
S = modelold(D.G, D.M, D.F[0], D.opt, verbose=0)
print(time()-t) # 1.3 s

t = time()
S = modelnew(D.G, D.M, D.F[0], D.opt, verbose=0)
print(time()-t) # 0.4 s -- >3 times faster!

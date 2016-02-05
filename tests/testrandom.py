"""
Version:
"""
import os
from pylab import *; from optima import *

sys.path.append(os.getcwd())


tmpP = loadobj('../tests/mozam.prj')

P = Project()
P.data = tmpP.data
P.makeparset()
P.runsim(die=True)

#plotpars(P)
#for p in range(12):
#    plotpeople(P, start=0, pops=p, skipempty=True, animate=False)
#pygui(P.results[-1])
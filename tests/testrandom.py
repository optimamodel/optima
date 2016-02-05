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
P.runsim()

#plotpars(P)
#plotpeople(P, start=0, pops=7, animate=True)
pygui(P.results[-1])
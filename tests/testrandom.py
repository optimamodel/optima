"""
Version:
"""
import os
from pylab import *; from optima import *


P = loadobj('../tests/misery.prj')

P = defaults.defaultproject('generalized')
plotpars(P)
plotpeople(P, start=0, pops=7, animate=True)
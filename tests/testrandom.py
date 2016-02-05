"""
Version:
"""
import os
from pylab import *; from optima import *


#P = loadobj('../tests/misery.prj')

P = Project(spreadsheet='/u/cliffk/unsw/optima/tests/exercise_template_20160204.xlsx')
plotpars(P)
plotpeople(P, start=0, pops=9, animate=False)
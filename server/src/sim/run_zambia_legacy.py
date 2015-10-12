from dataio import loaddata
from makedatapars import makedatapars
from makemodelpars import makemodelpars
D = loaddata('projects/zambia-with-new-testing.json')

D = makedatapars(D)
D['M'] = makemodelpars(D['P'],D['opt'])

from runsimulation import runsimulation
D = runsimulation(D,dosave=False)
from viewresults import viewuncerresults
viewuncerresults(D['plot']['E'])
import pylab
pylab.show()
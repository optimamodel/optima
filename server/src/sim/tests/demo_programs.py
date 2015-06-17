import add_optima_paths
import program
import region
import sim
import numpy

# This function tests the program calculation
r = region.Region.load('./regions/georgia_working.json')

# Make an example budget
a = r.D['data']['origalloc']
a = numpy.reshape(a, (-1, 1))
alloc = a
for i in xrange(0,len(r.D['opt']['partvec'])-1):
    alloc = numpy.append(alloc,a,axis=1)

alloc = a
for i in xrange(0,4):
    alloc = numpy.append(alloc,a,axis=1)

s = sim.SimBudget2('Test',r,alloc)
s.initialise()

m_new = s.parsmodel # New D.M

D = deepcopy(r.D)
from getcurrentbudget import getcurrentbudget
getcurrentbudget(D,a)
m_old = D['M'] # Old D.M
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

# alloc = a
# for i in xrange(0,4):
#     alloc = numpy.append(alloc,a,axis=1)

# Test only first program
r.D['programs'] = [r.D['programs'][0]]
r.D['data']['meta']['progs']['short'] = [r.D['data']['meta']['progs']['short'][0]]
r.program_sets[0]['programs'] = [r.program_sets[0]['programs'][0]]

s = sim.SimBudget2('Test',r,alloc)
s.initialise()

m_new = s.parsmodel # New D.M

from copy import deepcopy
D = deepcopy(r.D)
from getcurrentbudget import getcurrentbudget
D, newcov, newnonhivdalysaverted = getcurrentbudget(D,a)
from makemodelpars import makemodelpars
m_old = makemodelpars(D['P'],D['opt'], withwhat='c')

# print s.
# print D['P']['hivtest']['c']

print m_new['hivtest'][0]
print m_old['hivtest'][0]
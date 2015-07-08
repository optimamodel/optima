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


s = sim.SimBudget('Test',r,alloc)
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
print [x.name for x in s.program_set['programs']]

for par in m_new.keys():
	if type(m_old[par]) == dict:
		for key in m_old[par].keys():
			try:
				print "%s[%s]: old = %.6f, new = %.6f" % (par,key,m_old[par][key][0][0],m_new[par][key][0][0])
			except:
				try:
					print "%s[%s] (single): old = %.6f, new = %.6f" % (par,key,m_old[par][key][0],m_new[par][key][0])
				except:
					print "%s[%s] (??)" % (par,key)
	else:
		try:
			print "%s: old = %.6f, new = %.6f" % (par,key,m_old[par][0][0],m_new[par][0][0])
		except:
			try:
				print "%s (single): old = %.6f, new = %.6f" % (par,m_old[par][0],m_new[par][0])
			except:
				print "%s (??)" % (par)

import extra_utils
print extra_utils.dict_equal(m_old,m_new)
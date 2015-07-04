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

# Use the new programs to get the model parameters
s = sim.SimBudget2('Test',r,alloc)
s.initialise()
m_new = s.parsmodel # New D.M

# Use the old programs to get the model parametesr
from copy import deepcopy
D = deepcopy(r.D)
from getcurrentbudget import getcurrentbudget
D, newcov, newnonhivdalysaverted = getcurrentbudget(D,a)
from makemodelpars import makemodelpars
m_old = makemodelpars(D['P'],D['opt'], withwhat='c')

# Do some comparisons
print [x.name for x in s.program_set['programs']]

print m_old['numost'][0]
print m_new['numost'][0]

prognumber = 2
print D['programs'][prognumber]['convertedccparams']
print s.program_set['programs'][2].modalities[0].get_convertedccparams()

print s.program_set['programs'][2].modalities[0].cc_data
print D['programs'][prognumber]['ccparams']


# for par in m_new.keys():
# 	if type(m_old[par]) == dict:
# 		for key in m_old[par].keys():
# 			try:
# 				print "%s[%s]: old = %.6f, new = %.6f" % (par,key,m_old[par][key][0][0],m_new[par][key][0][0])
# 			except:
# 				try:
# 					print "%s[%s] (single): old = %.6f, new = %.6f" % (par,key,m_old[par][key][0],m_new[par][key][0])
# 				except:
# 					print "%s[%s] (??)" % (par,key)
# 	else:
# 		try:
# 			print "%s: old = %.6f, new = %.6f" % (par,key,m_old[par][0][0],m_new[par][0][0])
# 		except:
# 			try:
# 				print "%s (single): old = %.6f, new = %.6f" % (par,m_old[par][0],m_new[par][0])
# 			except:
# 				print "%s (??)" % (par)


# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from portfolio import Portfolio
from region import Region
from sim import Sim
from extra_utils import dict_equal
from copy import deepcopy

p1 = Portfolio('p-test')
#p1.appendregion(Region.load('./regions/Georgia good.json'))
p1.appendregion(Region.load('./regions/Malawi 150820.json'))

r1 = p1.regionlist[0]
#r2 = p1.regionlist[1]

## Temporary fixes regarding unfinished VMMC work. Will wait for Robyn's changes.
r1.metadata['programs'][0]['effects'] = []

r1.createsimbox('sb-test-sim', isopt = False, createdefault = True)
r1.simboxlist[-1].runallsims()

r1.createsimbox('sb-test-opt', isopt = True, createdefault = True)
r1.simboxlist[-1].runallsims()

r1.simboxlist[0].viewmultiresults()
r1.simboxlist[-1].viewmultiresults()

print()
print('%30s%15s' % ('Unoptimised...', 'Optimised...'))
for x in xrange(len(r1.metadata['inputprograms'])):
    print('%-15s%15.2f%15.2f' % (r1.metadata['inputprograms'][x]['short_name']+':',
                                 r1.simboxlist[-1].simlist[0].alloc[x],
                                 r1.simboxlist[-1].simlist[-1].alloc[x]))

#r1.simboxlist[-1].viewmultiresults()
#m1 = deepcopy(r1.simboxlist[-1].simlist[-1].parsmodel)
#s1 = deepcopy(r1.simboxlist[-1].simlist[-1].debug['structure'])
#r1.simboxlist[-1].simlist[-1].makemodelpars()
#r1.simboxlist[-1].simlist[-1].run()
#ma = deepcopy(r1.simboxlist[-1].simlist[-1].parsmodel)
#sa = deepcopy(r1.simboxlist[-1].simlist[-1].debug['structure'])
#r1.simboxlist[-1].simlist[-1].makemodelpars()
#r1.simboxlist[-1].simlist[-1].run()
#r1.simboxlist[-1].viewmultiresults()
#m2 = deepcopy(r1.simboxlist[-1].simlist[-1].parsmodel)
#s2 = deepcopy(r1.simboxlist[-1].simlist[-1].debug['structure'])
#
#p1.geoprioanalysis()

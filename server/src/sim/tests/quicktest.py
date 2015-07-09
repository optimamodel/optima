# -*- coding: utf-8 -*-
"""
Created on Tue Jul 07 22:24:46 2015

@author: David Kedziora
"""

import add_optima_paths
from region import Region

r = Region.load('./regions/Haiti.json')
sb = r.createsimbox('AndCrumpets', isopt = True, createdefault = True)

r.runsimbox(sb)
r.runsimbox(sb)
r.runsimbox(sb)
r.runsimbox(sb)
r.runsimbox(sb)
r.runsimbox(sb)
r.runsimbox(sb)
sb.viewmultiresults()   # They look the same.

from extra_utils import dict_equal

first = sb.simlist[0]
last = sb.simlist[-1]

print first.alloc
print last.alloc
print dict_equal(first.alloc, last.alloc)

print first.budget
print last.budget
print dict_equal(first.budget, last.budget)

print dict_equal(first.parsmodel, last.parsmodel)
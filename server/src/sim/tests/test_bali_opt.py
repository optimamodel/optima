# -*- coding: utf-8 -*-
"""
Created on Tue Jul 07 22:24:46 2015

@author: David Kedziora
"""

import add_optima_paths
from region import Region
from copy import deepcopy
import simbox

r = Region.load('./regions/indonesia_bali.json')
sb = r.createsimbox('asdf', isopt = True, createdefault = True)

r.runsimbox(sb)

# Now, we extract the optimized SimBudget with results computed by Cliff's optimize
s_cliff = sb.simlist[1]
s_reconstruct = deepcopy(s_cliff)
s_reconstruct.parsmodel = None
s_reconstruct.plotdata = None
s_reconstruct.plotdataopt = None
s_reconstruct.plotresults = None

# This can serve as a check that the deepcopy has worked
#print s_cliff.plotdata
#print s_reconstruct.plotdata

# Now, recompute using our initialization
s_reconstruct.initialise()
s_reconstruct.makemodelpars(randseed=4)
s_reconstruct.run()
sb2 = simbox.SimBox('check',r)
sb2.simlist = [s_cliff,s_reconstruct]
sb2.viewmultiresults() # See if they are the same...


# What does a non-opt sim look like?
sb3 = r.createsimbox('asdf2', isopt = False, createdefault = True)

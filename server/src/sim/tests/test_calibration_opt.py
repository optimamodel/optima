# -*- coding: utf-8 -*-
"""
Created on Tue Jul 07 22:24:46 2015

@author: David Kedziora
"""

import add_optima_paths
from region import Region
from copy import deepcopy
import simbox

# Run the code below while in the oop_experiment branch first, then 
# run everything else (with the block below commented out) in the 
# oop_calibration branch

# r = Region.load('./regions/indonesia_bali.json')
# sb = r.createsimbox('asdf', isopt = True, createdefault = True)
# r.runsimbox(sb)
# r.save('./bali_old_test.json')

original = Region.load('./bali_old_test.json')

new = Region.load('./regions/indonesia_bali.json')
sb = new.createsimbox('new_calibration', isopt = True, createdefault = True)
new.runsimbox(sb)

sb2 = simbox.SimBox('check',new)
sb2.simlist = [original.simboxlist[0].simlist[1],new.simboxlist[0].simlist[1]]
sb2.viewmultiresults() # See if they are the same...

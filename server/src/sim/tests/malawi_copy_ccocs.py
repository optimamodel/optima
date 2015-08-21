import add_optima_paths
from portfolio import Portfolio
from region import Region
from sim import Sim
from extra_utils import dict_equal
from copy import deepcopy

r = Region.load('./regions/Malawi 150820.json')
master_programs = deepcopy(r.D['programs'])

import os
flist = [x for x in os.listdir("C:/Users/romesh/Google Drive/Optima/Country applications/Malawi/Data/District level/Project files") if x.endswith('json')]

for fname in flist:
	r = Region.load("C:/Users/romesh/Google Drive/Optima/Country applications/Malawi/Data/District level/Project files/"+fname)
	r.D['programs'] = master_programs
	r.save("C:/Users/romesh/Google Drive/Optima/Country applications/Malawi/Data/District level/Project files/"+fname.replace('.json','_fixed.json'))





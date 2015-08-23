# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 04:34:26 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import tic, toc
from region import Region
from pylab import sort
from os import listdir
from multiprocessing import Process


n = 1e7
processes = []


def calculate_boc_for_region(regionname, integer):
    print('============ Starting region %s (%i) =============' % (regionname, integer))
    t = tic()
    targetregion = Region.load('./regions/' + regionname + '.json')           # Load up a Region from the json file.
    targetregion.recalculateBOC()
    targetregion.save('./regions/' + regionname + '.json')
    toc(t)
    print('============ Done with region %s =============' % regionname)
    

districts = sort([x.split('.')[0] for x in listdir('./regions/') if x.endswith('.json')])


print districts
for i,district in enumerate(districts):
    p = Process(target=calculate_boc_for_region, args=(district,i))
    p.start()
    processes.append(p)

for p in processes:
    p.join()


print('DONE.')




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
from multiprocessing import Process,freeze_support

usebatch = True


def calculate_boc_for_region(regionname, integer):
    print('============ Starting region %s (%i) =============' % (regionname, integer))
    t = tic()
    targetregion = Region.load('./regions/' + regionname + '.json')           # Load up a Region from the json file.
    targetregion.recalculateBOC()
    targetregion.save('./regions/' + regionname + '.json')
    toc(t)
    print('============ Done with region %s =============' % regionname)
    
if __name__ == '__main__':
    freeze_support()
    processes = []
    districts = sort([x.split('.')[0] for x in listdir('./regions/') if x.endswith('.json')])
    for i,district in enumerate(districts):
        if usebatch:
            p = Process(target=calculate_boc_for_region, args=(district,i))
            p.start()
            processes.append(p)
        else:
            calculate_boc_for_region(district,i)

    if usebatch:
        for p in processes:
            p.join()


print('DONE.')




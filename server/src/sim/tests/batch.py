# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 04:34:26 2015

@author: cliffk
"""

import add_optima_paths # analysis:ignore
from utils import run, tic, toc
from region import Region
from pylab import sort
from os import listdir
from pylab import pause

n = 1e7


def batch():
    districts = sort([x.rstrip('.json') for x in listdir('./regions/') if x.endswith('.json')])
    districts = districts[:4]
    for district in districts:
        string = "from batch import calculate_boc_for_region; calculate_boc_for_region('%s')" % district
        print string
        command = 'python -c "%s" &' % string
        run(command, printoutput=True)
        





def calculate_boc_for_region(regionname):
#    targetregion = Region.load('./regions/' + regionname + '.json')           # Load up a Region from the json file.
#    targetregion.recalculateBOC()
#    targetregion.save('./regions/' + regionname + '.json')
    print('hi from %s' % regionname)
    tmp = 0
    t = tic()
    for i in range(int(n)): tmp += 1
    toc(t)
    
    print('============ Done with region %s =============' % regionname)
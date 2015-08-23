# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths # analysis:ignore
from portfolio import Portfolio
from region import Region
from os import listdir
from pylab import sort
from multiprocessing import Process, Queue
from numpy import empty

usebatch = True

# Create a Portfolio to hold all of Malawi's districts (i.e. Regions).
p1 = Portfolio('Malawi 2015-Aug-23')
districts = sort([x.split('.')[0] for x in listdir('./regions/') if x.endswith('.json')])

regionlist = empty(len(districts),dtype=object)

def loaddistrict(district, i, regionlist):
    newregion = Region.load('./regions/' + district + '.json')           # Load up a Region from the json file.
    regionlist[i] = newregion                         # Put that Region into a Portfolio.
    print('Region alloc total: %f' % sum(newregion.data['origalloc'])) 
    

processes = []
for i,district in enumerate(districts):
    if usebatch:
        p = Process(target=loaddistrict, args=(district,i,regionlist))
        p.start()
        processes.append(p)
    else:
        loaddistrict(district,i,regionlist)

for newregion in regionlist:
    p1.appendregion(newregion)

if usebatch:
    for p in processes:
        p.join()
      


print('Running GPA...')
import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

p1.geoprioanalysis(usebatch=False)                # Run the GPA algorithm.


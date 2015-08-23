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

usebatch = True

# Create a Portfolio to hold all of Malawi's districts (i.e. Regions).
p1 = Portfolio('malawi-gpa')
districts = sort([x.split('.')[0] for x in listdir('./regions/') if x.endswith('.json')])

outputqueue = Queue()

def loaddistrict(district, i, outputqueue):
    newregion = Region.load('./regions/' + district + '.json')           # Load up a Region from the json file.
    outputqueue.put(newregion)                        # Put that Region into a Portfolio.
    print('Region alloc total: %f' % sum(newregion.data['origalloc'])) 
    

processes = []
for i,district in enumerate(districts):
    p = Process(target=loaddistrict, args=(district, i, outputqueue))
    p.start()
    processes.append(p)

regionlist = []
for i in range(len(districts)):
    regionlist.append(outputqueue.get())

for newregion in regionlist:
    p1.appendregion(newregion)



#print('Running GPA...')
#p1.geoprioanalysis(usebatch=True)                # Run the GPA algorithm.

print('Saving portfolio...')
p1.save()


print('Done.')


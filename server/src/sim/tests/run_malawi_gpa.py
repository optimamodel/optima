# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from portfolio import Portfolio
from region import Region
import os

# Create a Portfolio to hold all of Malawi's districts (i.e. Regions).
p1 = Portfolio('Malawi Project')

nationcheck = Region.load('./regions/Malawi 150820.json')

# List all the json files in the regions sub-directory.
templist = [x for x in os.listdir('./regions/') if x.endswith('.json')]

calc = 0
for x in templist:
    # Make sure you only select files with the right format (i.e. Regex 4 Dummies).
    if x[2] == '.':# and x[0:2] in ['11','12']:#,'13','14','15','16','17']:
        newregion = Region.load('./regions/' + x)           # Load up a Region from the json file.
        newregion.setregionname(x[4:-5])                   # Give it a nicer name.
        print newregion.metadata['programs'][0]['effects']   # Neutralise VMMC as per Robyn's request.
        p1.appendregion(newregion)                          # Put that Region into a Portfolio.
        print sum(newregion.data['origalloc'])        
        calc += sum(newregion.data['origalloc'])
print calc
print sum(nationcheck.data['origalloc'])

# Ignore this. It helps you run a simulation and an optimisation for a region of your choice.
def testsimopt(r1):

    r1.createsimbox('sb-test-sim', isopt = False, createdefault = True)
    r1.simboxlist[-1].runallsims()
    
    r1.createsimbox('sb-test-opt', isopt = True, createdefault = True)
    r1.simboxlist[-1].runallsims()
    
    r1.simboxlist[0].viewmultiresults()
    r1.simboxlist[-1].viewmultiresults()
    
    print
    print('%30s%15s' % ('Unoptimised...', 'Optimised...'))
    for x in xrange(len(r1.metadata['inputprograms'])):
        print('%-15s%15.2f%15.2f' % (r1.metadata['inputprograms'][x]['short_name']+':',
                                     r1.simboxlist[-1].simlist[0].alloc[x],
                                     r1.simboxlist[-1].simlist[-1].alloc[x]))

#testsimopt(newregion)

p1.geoprioanalysis()                # Run the GPA algorithm.

p1.quicksaveregions()

p1.geoprioreview(p1.gpalist[0])     # Did those results go by too quickly? Review the plots and a results summary.

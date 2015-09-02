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

# List all the json files in the regions sub-directory.
templist = [x for x in os.listdir('./regions/') if x.endswith('.json')]

normaliser = Region.load('./regions/Malawi 150820.json')
denom = sum(normaliser.calibrations[0]['popsize'])

from datetime import date
from numpy import nan, zeros, isnan, array, logical_or, nonzero

popcalc = 0
alloccalc = 0

for x in templist:
    # Make sure you only select files with the right format (i.e. Regex 4 Dummies).
    if x[2] == '.':
        print(x)
        newregion = Region.load('./regions/' + x)           # Load up a Region from the json file.
        
        totalloc = sum(newregion.data['origalloc'])        
        
        numer = sum(newregion.calibrations[0]['popsize'])
        popcalc += numer
#        newregion.data['origalloc'] *= numer/denom
        p1.appendregion(newregion)                          # Put that Region into a Portfolio.
        
#        totalloc = sum(newregion.data['origalloc'])
        alloccalc += totalloc
        
        print numer
        print totalloc
        
#p1.quicksaveregions()
print popcalc
print denom

print alloccalc
print sum(normaliser.data['origalloc'])

alloccalc2 = 0
for someregion in p1.regionlist:
    regpoptot = sum(someregion.calibrations[0]['popsize'])
    someregion.data['origalloc'] *= regpoptot/popcalc
    totalloc = sum(someregion.data['origalloc'])  
    alloccalc2 += totalloc
print alloccalc2
print sum(normaliser.data['origalloc'])

p1.quicksaveregions()


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

#p1.geoprioanalysis()                # Run the GPA algorithm.

#p1.geoprioreview(p1.gpalist[0])     # Did those results go by too quickly? Review the plots and a results summary.

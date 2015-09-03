# -*- coding: utf-8 -*-
"""
Created on Thu Jul 23 18:03:48 2015

@author: David Kedziora
"""

import add_optima_paths
from portfolio import Portfolio
from project import Project
import os

# Create a Portfolio to hold all of Malawi's districts (i.e. Projects).
p1 = Portfolio('Malawi Project')

# List all the json files in the projects sub-directory.
templist = [x for x in os.listdir('./projects/') if x.endswith('.json')]

normaliser = Project.load('./projects/Malawi 150820.json')
denom = sum(normaliser.calibrations[0]['popsize'])

from datetime import date
from numpy import nan, zeros, isnan, array, logical_or, nonzero

popcalc = 0
alloccalc = 0

for x in templist:
    # Make sure you only select files with the right format (i.e. Regex 4 Dummies).
    if x[2] == '.':
        print(x)
        newproject = Project.load('./projects/' + x)           # Load up a Project from the json file.
        
        totalloc = sum(newproject.data['origalloc'])        
        
        numer = sum(newproject.calibrations[0]['popsize'])
        popcalc += numer
#        newproject.data['origalloc'] *= numer/denom
        p1.appendproject(newproject)                          # Put that Project into a Portfolio.
        
#        totalloc = sum(newproject.data['origalloc'])
        alloccalc += totalloc
        
        print numer
        print totalloc
        
#p1.quicksaveprojects()
print popcalc
print denom

print alloccalc
print sum(normaliser.data['origalloc'])

alloccalc2 = 0
for someproject in p1.projectlist:
    regpoptot = sum(someproject.calibrations[0]['popsize'])
    someproject.data['origalloc'] *= regpoptot/popcalc
    totalloc = sum(someproject.data['origalloc'])  
    alloccalc2 += totalloc
print alloccalc2
print sum(normaliser.data['origalloc'])

p1.quicksaveprojects()


# Ignore this. It helps you run a simulation and an optimisation for a project of your choice.
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

#testsimopt(newproject)

#p1.geoprioanalysis()                # Run the GPA algorithm.

#p1.geoprioreview(p1.gpalist[0])     # Did those results go by too quickly? Review the plots and a results summary.

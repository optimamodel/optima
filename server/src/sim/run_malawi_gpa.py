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

nationcheck = Project.load('./projects/Malawi 150820.json')

# List all the json files in the projects sub-directory.
templist = [x for x in os.listdir('./projects/') if x.endswith('.json')]

calc = 0
for x in templist:
    # Make sure you only select files with the right format (i.e. Regex 4 Dummies).
    if x[2] == '.':# and x[0:2] in ['11','12']:#,'13','14','15','16','17']:
        newproject = Project.load('./projects/' + x)           # Load up a Project from the json file.
        newproject.setprojectname(x[4:-5])                   # Give it a nicer name.
        print newproject.metadata['programs'][0]['effects']   # Neutralise VMMC as per Robyn's request.
        p1.appendproject(newproject)                          # Put that Project into a Portfolio.
        print sum(newproject.data['origalloc'])        
        calc += sum(newproject.data['origalloc'])
print calc
print sum(nationcheck.data['origalloc'])

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

p1.geoprioanalysis()                # Run the GPA algorithm.

p1.quicksaveprojects()

p1.geoprioreview(p1.gpalist[0])     # Did those results go by too quickly? Review the plots and a results summary.

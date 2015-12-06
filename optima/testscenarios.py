# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:24:45 2015

@author: cliffk
"""


## Define tests to run here!!!
tests = [
'standardscen',
]


##############################################################################
## Initialization
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

def done(t=0):
    print('Done.')
    toc(t)
    blank()
    





blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()


## GUI test
if 'standardscen' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
        
    ## Define scenarios
    scenlist = [
        {'name': 'Current conditions', 'pars': []},
         {'name': 'Less casual condom use in men',
          'pars': [{'endval': 0.1,
            'endyear': 2015,
            'names': ['condom', 'cas'],
            'pops': 0,
            'startval': 0.1,
            'startyear': 2005}]},
         {'name': 'Less regular condom use',
          'pars': [{'endval': 0.01,
            'endyear': 2015,
            'names': ['condom', 'reg'],
            'pops': 11,
            'startval': 0.01,
            'startyear': 2005}]},
         {'name': 'More casual acts, men',
          'pars': [{'endval': 100.,
            'endyear': 2015,
            'names': ['numacts', 'cas'],
            'pops': 0,
            'startval': 100.,
            'startyear': 2005}]},
         {'name': 'Increased STI prevalence in women',
          'pars': [{'endval': 0.5,
            'endyear': 2015,
            'names': ['stiprev'],
            'pops': 1,
            'startval': 0.5,
            'startyear': 2005}]}
        ]
    
    P.copyparset('default', 'scentest')
    from scenarios import runscenarios
    allresults = runscenarios(P, P.parsets['default'], scenlist=scenlist)
     
#    from gui import gui
#    gui([results1, results2])
    from plotpeople import plotpeople
    plotpeople(allresults)

    done(t)
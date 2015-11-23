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
    results1 = P.runsim('default')
    
    
    ## Define scenarios
    scenlist = [
        {'name': 'Current conditions', 'pars': []},
         {'name': 'less fsw condom',
          'pars': [{'endval': 0.1,
            'endyear': 2015,
            'names': ['condom', 'com'],
            'pops': 0,
            'startval': 0.1,
            'startyear': 2005}]},
         {'name': 'less reg cond',
          'pars': [{'endval': 0.01,
            'endyear': 2015,
            'names': ['condom', 'reg'],
            'pops': 11,
            'startval': 0.01,
            'startyear': 2005}]},
         {'name': 'more comm acts',
          'pars': [{'endval': 1000.0000000000001,
            'endyear': 2015,
            'names': ['numacts', 'com'],
            'pops': 0,
            'startval': 1000.0000000000001,
            'startyear': 2005}]},
         {'name': 'reg acts',
          'pars': [{'endval': 0,
            'endyear': 2015,
            'names': ['numacts', 'reg'],
            'pops': 11,
            'startval': 200,
            'startyear': 2005}]},
         {'name': 'discharge-all',
          'pars': [{'endval': 0.5,
            'endyear': 2015,
            'names': ['stiprevdis'],
            'pops': 11,
            'startval': 0.5,
            'startyear': 2005}]}
        ]
    
    
    
    P.copyparset('default', 'scentest')
    results2 = P.runsim('scentest')
    
    from gui import gui
    from plotpeople import plotpeople
    gui([results1, results2])
    plotpeople([results1, results2])

    done(t)
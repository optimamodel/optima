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
## Initialization -- same for every test script
##############################################################################

from optima import tic, toc, blank, pd # analysis:ignore

if 'doplot' not in locals(): doplot = True

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
        {'name': 'Less casual condom use',
          'pars': [{'endval': 0.1,
            'endyear': 2015,
            'name': 'condcas',
            'for': ('M 15-49', 'F 15-49'),
            'startval': 0.1,
            'startyear': 2005}]},
         {'name': 'More casual acts',
          'pars': [{'endval': 100.,
            'endyear': 2015,
            'name': 'actscas',
            'for': ('F 15-49', 'M 15-49'),
            'startval': 100.,
            'startyear': 2005}]},
         {'name': 'Increased STI prevalence in women',
          'pars': [{'endval': 0.5,
            'endyear': 2015,
            'name': 'stiprev',
            'for': 1,
            'startval': 0.5,
            'startyear': 2005}]}
        ]
    
    from scenarios import runscenarios
    allresults = runscenarios(P, P.parsets['default'], scenlist=scenlist)
     
#    from gui import gui
#    gui([results1, results2])
    if doplot:
        from plotpeople import plotpeople
        plotpeople(allresults)

    done(t)
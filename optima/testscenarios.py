# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 16:24:45 2015

@author: cliffk
"""


## Define tests to run here!!!
tests = [
'standardscen',
]

doplot=False
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
    from defaultprograms import defaultprogset
    from numpy import array
    
    P = Project(spreadsheet='test7pops.xlsx')
    R = defaultprogset(P, addpars=True, filterprograms=['Condoms', 'FSW_programs'])
    R.covout['condcas'][('Clients', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('Clients', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcas'][('MSM', 'MSM')].addccopar({'intercept': (0.5,0.55), 't': 2016.0, 'Condoms':(0.55,0.65)})
    R.covout['condcas'][('M 15+', 'FSW')].addccopar({'intercept': (0.3,0.35), 't': 2016.0, 'Condoms':(0.45,0.55), 'FSW_programs':(0.55,0.65)})
    R.covout['condcas'][('M 15+', 'F 15+')].addccopar({'intercept': (0.2,0.3), 't': 2016.0, 'Condoms':(0.35,0.45)})
    R.covout['condcom'][('Clients', 'FSW')].addccopar({'intercept': (0.6,0.65), 't': 2016.0, 'FSW_programs':(0.9,0.95)})
    R.covout['hivtest']['FSW'].addccopar({'intercept': (0.35,0.45), 't': 2016.0, 'FSW_programs':(0.6,0.65)})
    
    ## Define scenarios
    scenlist = [
        {'name': 'Current conditions',
                 'parset': P.parsets['default'],
                 'type': 'parameter',
                 'pars': []},
        {'name': 'Less casual condom use',
         'parset': P.parsets['default'],
         'type': 'parameter',
         'pars': [{'endval': 0.1,
            'endyear': 2015,
            'name': 'condcas',
            'for': ('M 15+', 'F 15+'),
            'startval': 0.1,
            'startyear': 2005}]},
         {'name': 'More casual acts',
          'parset': P.parsets['default'],
          'type': 'parameter',
          'pars': [{'endval': 100.,
            'endyear': 2015,
            'name': 'actscas',
            'for': ('M 15+', 'F 15+'),
            'startval': 100.,
            'startyear': 2005}]},
         {'name': 'Increased STI prevalence in women',
          'parset': P.parsets['default'],
          'type': 'parameter',
          'pars': [{'endval': 0.5,
            'endyear': 2015,
            'name': 'stiprev',
            'for': 1,
            'startval': 0.5,
            'startyear': 2005}]},
         {'name': 'Double investment in condom program',
          'parset': P.parsets['default'],
          'type': 'program',
          'progset': R,
          'budgets': [
           {'Condoms':array([1e7]),
            'FSW_programs':array([1e6])},
           {'Condoms':array([2e7]),
            'FSW_programs':array([1e6])},
            ],
          'coveragelevels': None},
         {'name': 'A million people covered by the condom program',
          'parset': P.parsets['default'],
          'type': 'program',
          'progset': R,
          'budgets': None,
          'coveragelevels': [
           {'Condoms':array([285706.84495908]),
            'FSW_programs':array([15352.67106128])},
           {'Condoms':array([1e6]),
            'FSW_programs':array([15352.67106128])},
            ]}
        ]
    
    from scenarios import runscenarios
    allresults = runscenarios(scenlist=scenlist)
     
#    from gui import gui
#    gui([results1, results2])
    if doplot:
        from plotpeople import plotpeople
        plotpeople(allresults)

    done(t)
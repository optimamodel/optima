"""
Test optimization

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan05 by cliffk
"""

## Define tests to run here!!!
tests = [
'tmp',
#'minimizeoutcomes',
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






## Temp test
if 'tmp' in tests:
    t = tic()

    print('Running standard scenarios test...')
    from optima import Project, runscenarios
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
         {'name': 'Double investment in condom program',
          'parset': P.parsets['default'],
          'type': 'program',
          'progset': R,
          'budgets': [
           {'Condoms':array([2e9]),
            'FSW_programs':array([1e9])},
            ],
          'coveragelevels': None,
          't': [2010]},
        ]
    
    allresults = runscenarios(scenlist=scenlist)
    
    done(t)






## Minimize money test
if 'minimizeoutcomes' in tests:
    t = tic()

    print('Running minimize outcomes test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results = P.minoutcomes(parset='default', progset='default', alloc=[1e6,1e6])
    
    if doplot:
        from gui import plotresults
        plotresults(results, toplot=['prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2016feb06 by cliffk
"""



## Define tests to run here!!!
tests = [
'force',
'treatment',
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










## Force-of-infection change test
if 'force' in tests:
    t = tic()

    print('Running force-of-infection test...')
    from optima import Project
    
    P = Project(spreadsheet='simple.xlsx')
    results1 = P.runsim('default')
    
    P.copyparset('default', 'forcetest')
    P.parsets['forcetest'].pars['force'].y[:] *= 3
    results2 = P.runsim('forcetest')
    
    if doplot:
        from optima import plotpeople
        plotpeople(P)

    done(t)




## Treatment change test
if 'treatment' in tests:
    t = tic()

    print('Running force-of-infection test...')
    from optima import Project
    
    P = Project(spreadsheet='simple.xlsx')
    results1 = P.runsim('default')
    
    P.copyparset('default', 'treatment')
    treatpar = P.parsets['treatment'].pars['numtx']
    treatpar.y['tot'][treatpar.t['tot']>=2010] *= 3
    results2 = P.runsim('treatment')
    
    if doplot:
        from optima import plotpeople
        plotpeople(P)

    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
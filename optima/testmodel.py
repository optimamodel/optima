"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov23 by cliffk
"""



## Define tests to run here!!!
tests = [
#'gui',
#'force',
'treatment',
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
if 'gui' in tests:
    t = tic()

    print('Running GUI test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    from gui import gui
    from plotpeople import plotpeople
    gui(results)
    plotpeople(results)

    done(t)





## Force-of-infection change test
if 'force' in tests:
    t = tic()

    print('Running force-of-infection test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results1 = P.runsim('default')
    
    P.copyparset('default', 'forcetest')
    P.parsets['forcetest'].pars[0]['force'][:] *= 3
    results2 = P.runsim('forcetest')
    
    from gui import gui
    from plotpeople import plotpeople
    gui([results1, results2])
    plotpeople([results1, results2])

    done(t)




## Treatment change test
if 'treatment' in tests:
    t = tic()

    print('Running force-of-infection test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results1 = P.runsim('default')
    
    P.copyparset('default', 'treatment')
    treatpar = P.parsets['treatment'].pars[0]['numtx']
    treatpar.y['tot'][:] *= 0
    results2 = P.runsim('treatment')
    
    from gui import gui
    from plotpeople import plotpeople
    gui([results1, results2])
    plotpeople([results1, results2])

    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
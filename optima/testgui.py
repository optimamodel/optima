"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan06 by cliffk
"""



## Define tests to run here!!!
tests = [
'plot',
'browser',
'gui',
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




## Python GUI test
if 'plot' in tests and doplot:
    t = tic()

    print('Running plot test...')
    from optima import Project, plotresults
    
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    plotresults(results, figsize=(14,10))

    done(t)




## mpld3 test
if 'browser' in tests and doplot:
    t = tic()

    print('Running browser test...')
    from optima import Project, browser
    
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    browser(results)

    done(t)






## Python GUI test
if 'gui' in tests and doplot:
    t = tic()

    print('Running GUI test...')
    from optima import Project, pygui
    
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    pygui(results)

    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
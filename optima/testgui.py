"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015dec23 by cliffk
"""



## Define tests to run here!!!
tests = [
#'browser',
'gui',
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






## mpld3 test
if 'browser' in tests:
    t = tic()

    print('Running GUI test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    print('  Starting browser...')
    from gui import browser
    browser(results)

    done(t)






## Python GUI test
if 'gui' in tests:
    t = tic()

    print('Running GUI test...')
    from optima import Project
    
    P = Project(spreadsheet='test7pops.xlsx')
    results = P.runsim('default')
    
    from gui import gui
    gui(results)

    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015nov23 by cliffk
"""



## Define tests to run here!!!
tests = [
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





## Project creation test
if 'gui' in tests:
    t = tic()

    print('Running make programs test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    results = P.runsim('default')
    
    from gui import gui
    from plotpeople import plotpeople
#    gui(results)
    plotpeople(results)

    done(t)






print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
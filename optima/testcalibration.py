"""
Test calibration..

To use: comment out lines in the definition of 'tests' to not run those tests.

NOTE: for best results, run in interactive mode, e.g.

python -i tests.py

Version: 2015dec28 by cliffk
"""



## Define tests to run here!!!
tests = [
'perturb',
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









## Perturbation test
if 'perturb' in tests:
    t = tic()

    print('Running GUI test...')
    from optima import Project
    
    P = Project(spreadsheet='test.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=10, span=0.99)
    results2 = P.runsim('sensitivity')
    
    from gui import gui
    gui(results2)

    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
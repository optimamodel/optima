"""
Test calibration

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2015dec29 by cliffk
"""



## Define tests to run here!!!
tests = [
'sensitivity',
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









## Sensitivity test
if 'sensitivity' in tests:
    t = tic()

    print('Running sensitivity test...')
    from optima import Project
    
    P = Project(spreadsheet='test7pops.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=10, span=0.5)
    results = P.runsim('sensitivity')
    
    from gui import gui
    gui(results, which=['prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
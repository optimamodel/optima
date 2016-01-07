"""
Test optimization

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan05 by cliffk
"""

## Define tests to run here!!!
tests = [
'minimizeoutcomes',
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
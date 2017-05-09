"""
Test script to see if Optima works.

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016feb09 by cliffk
"""



## Define tests to run here!!!
tests = [
#'plot',
'browser',
#'gui',
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
    from optima import defaultproject, plotresults
    
    P = defaultproject('concentrated')
    P.runsim() # Not necessary, but just in case results haven't been saved with the project
    plotresults(P.results[-1], toplot='cascade', figsize=(14,10))

    done(t)




## mpld3 test
if 'browser' in tests and doplot:
    t = tic()

    print('Running browser test...')
    from optima import defaultproject, browser
    
    P = defaultproject('concentrated')
    P.runsim() # Not necessary, but just in case results haven't been saved with the project
    browser(P.results[-1], toplot='cascade')

    done(t)






## Python GUI test
if 'gui' in tests and doplot:
    t = tic()

    print('Running GUI test...')
    from optima import defaultproject, pygui
    
    P = defaultproject('concentrated')
    results = P.runsim() # Showing another way of running
    pygui(results)

    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
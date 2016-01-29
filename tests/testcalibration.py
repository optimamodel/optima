"""
Test calibration

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan09 by cliffk
"""

## Define tests to run here!!!
tests = [
#'attributes',
'sensitivity',
#'manualfit',
'autofit',
#'autofitmulti',
#'longfit',
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




## Attributes test
if 'attributes' in tests:
    t = tic()

    print('Running attributes test...')
    from optima import Project
    P = Project(spreadsheet='simple.xlsx')
    P.parsets[0].listattributes()

    done(t)







## Sensitivity test
if 'sensitivity' in tests:
    t = tic()

    print('Running sensitivity test...')
    from optima import Project
    
    P = Project(spreadsheet='generalized.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=10, span=0.5)
    results = P.runsim('sensitivity')
    
    if doplot:
        from optima import pygui
        pygui(results, toplot=['prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)






## Manual calibration test
if 'manualfit' in tests and doplot:
    t = tic()

    print('Running manual calibration test...')
    from optima import Project
    
    P = Project(spreadsheet='generalized.xlsx')
    P.manualfit(orig='default', name='manual')
    
    done(t)






## Autofit test
if 'autofit' in tests:
    t = tic()

    print('Running autofit test...')
    from optima import Project
    
    P = Project(spreadsheet='generalized.xlsx')
    P.autofit(name='autofit', orig='default', what=['force'], maxtime=None, maxiters=30, inds=None) # Run automatic fitting
    results1 = P.runsim('default', end=2015) # Generate results
    results2 = P.runsim('autofit', end=2015)
    
    if doplot:
        from optima import plotresults
        plotresults(P.parsets['default'].getresults(), toplot=['prev-tot', 'prev-pops', 'numinci-pops'])
        plotresults(P.parsets['autofit'].getresults(), toplot=['improvement', 'prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)







## Autofit test
if 'autofitmulti' in tests:
    t = tic()

    print('Running autofitmulti test...')
    from optima import Project
    
    P = Project(spreadsheet='generalized.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=5, span=0.5) # Create MC initialization
    P.runsim('sensitivity', end=2015) # Generate results
    P.autofit(name='autofit', orig='sensitivity', what=['force'], maxtime=None, maxiters=30, inds=None) # Run automatic fitting
    
    
    if doplot:
        from optima import plotresults
        plotresults(P.parsets['sensitivity'].getresults(), toplot=['prev-tot', 'numinci-sta'])
        plotresults(P.parsets['autofit'].getresults(), toplot=['improvement', 'prev-tot', 'numinci-sta'])
    
    done(t)












## Autofit test
if 'longfit' in tests:
    t = tic()

    print('Running long autofit test...')
    from optima import Project
    
    P = Project(spreadsheet='generalized.xlsx')
    P.autofit(name='autofit', orig='default', what=['init','popsize','force','const'], maxiters=1000, inds=None, verbose=2) # Run automatic fitting
    results1 = P.runsim('default', end=2015) # Generate results
    results2 = P.runsim('autofit', end=2015)
    
    if doplot:
        from optima import plotresults
        plotresults(results1, toplot=['prev-tot', 'prev-pops', 'numinci-pops'])
        plotresults(results2, toplot=['improvement', 'prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)










print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
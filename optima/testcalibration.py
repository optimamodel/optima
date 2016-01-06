"""
Test calibration

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan05 by cliffk
"""

## Define tests to run here!!!
tests = [
'attributes',
'sensitivity',
'manualfit',
'autofit',
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
    
    P = Project(spreadsheet='test.xlsx')
    P.parsets[0].listattributes()

    done(t)







## Sensitivity test
if 'sensitivity' in tests:
    t = tic()

    print('Running sensitivity test...')
    from optima import Project
    
    P = Project(spreadsheet='test7pops.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=10, span=0.5)
    results = P.runsim('sensitivity')
    
    if doplot:
        from gui import pygui
        pygui(results, which=['prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)






## Manual calibration test
if 'manualfit' in tests and doplot:
    t = tic()

    print('Running manual calibration test...')
    from optima import Project
    
    P = Project(spreadsheet='test7pops.xlsx')
    P.manualfit(orig='default', name='manual')
    
    done(t)






## Autofit test
if 'autofit' in tests:
    t = tic()

    print('Running autofit test...')
    from optima import Project
    
    P = Project(spreadsheet='test7pops.xlsx')
    P.sensitivity(orig='default', name='sensitivity', n=3, span=0.5) # Create MC initialization
    P.autofit(name='autofit', orig='sensitivity', what=['force'], maxtime=None, niters=20, inds=None) # Run automatic fitting
    results1 = P.runsim('default', end=2015) # Generate results
    results2 = P.runsim('autofit', end=2015)
    
    if doplot:
        from gui import plotresults
        plotresults(results1, toplot=['prev-tot', 'prev-pops', 'numinci-pops']) # WARNING, can't display 2 GUIs at the same time, ugh!
        plotresults(results2, toplot=['prev-tot', 'prev-pops', 'numinci-pops'])
    
    done(t)



print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
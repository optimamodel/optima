"""
Test optimization

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2016jan28
"""

## Define tests to run here!!!
tests = [
#'minimizeoutcomes',
'minimizemoney',
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

from optima.defaults import defaultproject

T = tic()








## Minimize outcomes test
if 'minimizeoutcomes' in tests:
    t = tic()

    print('Running minimize outcomes test...')
    from optima import defaultobjectives
    
    P = defaultproject(which='generalized') 
    
    objectives = defaultobjectives()
    objectives['budget'] = 6e6 # Change default budget to optimize
    P.minoutcomes(name='minoutcome', parsetname='default', progsetname='default', objectives=objectives, method='asd', maxtime=10)
    
    print('Original allocation: '),
    print(P.results[-1].budget[0])
    print('Optimal allocation: '),
    print(P.optims[-1].getresults().budget[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budget', 'improvement', 'prev-tot', 'prev-per', 'numinci-tot'])
    
    done(t)






## Minimize money test
if 'minimizemoney' in tests:
    t = tic()

    print('Running minimize money test...')
    from optima import defaultobjectives
    
    P = defaultproject(which='generalized')

    coverage = P.progsets[-1].getprogcoverage(budget=P.progsets[-1].getdefaultbudget(),
                      t=2016,
                      parset=P.parsets['default'])

    outcomes = P.progsets[-1].getoutcomes(coverage=coverage,t=2016, parset=P.parsets['default'])
    
    objectives = defaultobjectives(which='money')
    objectives['deathfrac'] = 0.1
    objectives['incifrac'] = 0.5
    P.minmoney(name='minmoney', parsetname='default', progsetname='default', objectives=objectives, maxtime=10, debug=False)
    
    print('Original allocation: '),
    print(P.results[-1].budget[0])
    print('Optimal allocation: '),
    print(P.optims[-1].getresults().budget[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budget', 'improvement', 'prev-tot', 'prev-per', 'numinci-tot'])
    
    done(t)




print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
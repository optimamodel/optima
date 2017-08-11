"""
Test optimization

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2017jan13
"""

## Define tests to run here!!!
tests = [
'minimizeoutcomes',
#'investmentstaircase',
#'minimizemoney',
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

from optima import defaultproject
from pylab import seed
seed(0) # Ensure consistency across runs

T = tic()








## Minimize outcomes test
if 'minimizeoutcomes' in tests:
    t = tic()

    print('Running minimize outcomes test...')
    from optima import defaultobjectives, defaultconstraints, findinds
    from numpy import arange
    
    P = defaultproject('best') 
    
    objectives = defaultobjectives(P.progsets[0]) # This or P
    constraints = defaultconstraints(P) # This or P.progsets[0]
    P.optimize(name='minoutcome', maxtime=5, mc=0, parsetname=-1, progsetname=-1, objectives=objectives)
    
    # Check Pareto condition
    optim = P.optims[0]
    startind = findinds(P.results[-1].tvec, optim.objectives['start'])
    endind = findinds(P.results[-1].tvec, optim.objectives['end'])
    inds = arange(startind,endind)
    output = '=====================\n'
    output += 'Outcomes by population\n'
    output += '=====================\n'
    for key in optim.objectives['keys']:
        output += optim.objectives['keylabels'][key]+'\n'
        output += 'Population | Old val | New val | Improvement \n'
        for pn, pop in enumerate(P.results[-1].popkeys):
            origval = P.results[-1].main['num'+key].pops['Baseline'][pn,inds].sum()
            newval = P.results[-1].main['num'+key].pops['Optimal'][pn,inds].sum()
            output += '%s | %.1f | %.1f | %.1f \n' % (pop.rjust(10), origval, newval, (origval-newval)/origval)
    print output

    print('Original allocation: '),
    print(P.results[-1].budgets[0])
    print('Optimal allocation: '),
    print(P.optims[-1].getresults().budgets[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'improvement', 'prev-total', 'prev-population', 'numinci-total'], advanced=True)
    
    done(t)



if 'investmentstaircase' in tests:
    t = tic()

    print('Running investment staircase test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best') 
    
    objectives = defaultobjectives(P.progsets[0]) # This or P
    objectives['budgetscale'] = [0.1, 0.2, 0.5, 1., 1.2, 1.5]
    constraints = defaultconstraints(P) # This or P.progsets[0]
    P.optimize(name='minoutcome', parsetname='default', progsetname='default', objectives=objectives, maxtime=5, mc=0)
    
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budget', 'improvement', 'prev', 'numinci'])
    
    done(t)




## Minimize money test
if 'minimizemoney' in tests:
    t = tic()

    print('Running minimize money test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best')
    
    objectives = defaultobjectives(P.progsets[0], which='money')
    objectives['deathfrac'] = 0.1 # Yes, this means an increase in deaths
    objectives['incifrac'] = 0.2
    constraints = defaultconstraints(P)
    P.optimize(name='minmoney', parsetname='default', progsetname='default', objectives=objectives, constraints=constraints, maxtime=10, ccsample='random')
    
    print('Original allocation: ($%g)' % sum(P.results[-1].budgets[0][:]))
    print(P.results[-1].budgets[0])
    print('Optimal allocation: ($%g)' % sum(P.optims[-1].getresults().budgets[1][:]))
    print(P.optims[-1].getresults().budgets[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'prev-total', 'prev-population', 'numinci-total'], advanced=True)
    
    done(t)





print('\n\n\nDONE: ran %i tests' % len(tests))
toc(T)
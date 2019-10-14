"""
Test optimization

To use: comment out lines in the definition of 'tests' to not run those tests.
NOTE: for best results, run in interactive mode, e.g.
python -i tests.py

Version: 2019oct14
"""

## Define tests to run here!!!
tests = [
#'minimizeoutcomes',
# 'multichain',
# 'investmentstaircase',
#'minimizemoney',
#'optimizetesting',
'meet909090',
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
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best') 
    
    objectives = defaultobjectives(P.progsets[0]) # This or P
    constraints = defaultconstraints(P) # This or P.progsets[0]
    P.optimize(name='minoutcome', maxtime=5, mc=0, parsetname=-1, progsetname=-1, objectives=objectives)
    
    print('Original allocation: '),
    print(P.results[-1].budgets[0])
    print('Optimal allocation: '),
    print(P.optims[-1].getresults().budgets[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'improvement', 'prev-total', 'prev-population', 'numinci-total'], advanced=True)
    
    done(t)


if 'multichain' in tests:
    t = tic()

    print('Running multichain optimization test...')
    import optima as op
    import pylab as pl
    P = op.demo(0)
    results = P.optimize(multi=True, nchains=4, blockiters=10, nblocks=2, randseed=1)
    if doplot: 
        op.pygui(P, toplot=['improvement', 'budgets', 'numinci'])
        pl.figure(); pl.plot(results.multiimprovement.transpose())
    
    done(t)

if 'investmentstaircase' in tests:
    t = tic()

    print('Running investment staircase test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best') 
    
    objectives = defaultobjectives(P.progsets[0]) # This or P
    objectives['budgetscale'] = [0.1, 0.2, 0.5, 1., 1.2, 1.5]
    constraints = defaultconstraints(P) # This or P.progsets[0]
    P.optimize(name='minoutcome', parsetname='default', progsetname='default', objectives=objectives, maxtime=10, mc=0)
    
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'prev', 'numinci'])
    
    done(t)




## Minimize money test
if 'minimizemoney' in tests:
    t = tic()

    print('Running minimize money test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best')
    P.parset().fixprops(False)
    
    objectives = defaultobjectives(project=P, which='money')
    objectives['deathfrac'] = 0.25
    objectives['incifrac'] = 0.25
    constraints = defaultconstraints(project=P)
    P.optimize(name='minmoney', parsetname='default', progsetname='default', objectives=objectives, constraints=constraints, maxtime=10, ccsample='random')
    
    print('Original allocation: ($%g)' % sum(P.results[-1].budgets[0][:]))
    print(P.results[-1].budgets[0])
    print('Optimal allocation: ($%g)' % sum(P.optims[-1].getresults().budgets[1][:]))
    print(P.optims[-1].getresults().budgets[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'prev-total', 'prev-population', 'numinci-total'], advanced=True)
    
    done(t)



if 'optimizetesting' in tests:
    t = tic()

    print('Running optimize testing test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best')
    P.parset().fixprops(False)
    
    objectives = defaultobjectives(project=P, which='outcome')
    objectives['inciweight'] = 0
    objectives['deathweight'] = 0
    objectives['proptreat'] = 1.0
    constraints = defaultconstraints(project=P)
    P.optimize(name='maxdiag', mc=1, maxtime=30, parsetname='default', progsetname='default', objectives=objectives, constraints=constraints, ccsample='random')
    
    print('Original allocation: ($%g)' % sum(P.results[-1].budgets[0][:]))
    print(P.results[-1].budgets[0])
    print('Optimal allocation: ($%g)' % sum(P.optims[-1].getresults().budgets[1][:]))
    print(P.optims[-1].getresults().budgets[1]) # Showing that results are "stored" in the optimization -- same object as before
    if doplot: 
        from optima import pygui
        pygui(P.results[-1], toplot=['budgets', 'prev-total', 'prev-population', 'numinci-total'], advanced=True)
    
    done(t)
    

if 'meet909090' in tests:
    t = tic()

    print('Running minimize money test...')
    from optima import defaultobjectives, defaultconstraints
    
    P = defaultproject('best')
    P.parset().fixprops(False)
    P.pars()['leavecare'].m = 0 # Warning -- without this, targets can't be met
    
    objectives = defaultobjectives(project=P, which='money')
    objectives['deathfrac'] = -10.0 # Ignore epi side
    objectives['incifrac']  = -10.0
    objectives['dalyfrac']  = -10.0
    objectives['propdiag']       = 0.90
    objectives['proptreat']      = 0.81
    objectives['propsuppressed'] = 0.73
    constraints = defaultconstraints(project=P)
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
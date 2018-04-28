"""
Create a good test project.

Version: 2016feb08
"""

from optima import defaultproject, pygui, manualfit, Parscen, Budgetscen, Coveragescen, dcp, plotpars, plotpeople, loadproj, saveobj, migrate, makespreadsheet # analysis:ignore
from optima import tic, toc, blank, pd # analysis:ignore

## Options
tests = [
'standardrun',
#'autocalib',
#'manualcalib',
#'reconcile',
#'runscenarios',
#'optimize',
#'dosave',
]

filename = 'best.prj'
ind = -1 # Default index


## Housekeeping

if 'doplot' not in locals(): doplot = True
if 'runsensitivity' not in locals(): runsensitivity = False

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

## Make or load&migrate a project
if 'standardrun' in tests:
    P = defaultproject('best',dorun=False)
    P.parset().fixprops(False)
    P.pars()['hivdeath'].y['PWID'] = 2.0 # Increase death rate for PWID
    P.runsim(debug=True, start=2000, end=2015)
    if runsensitivity: P.sensitivity()
    if doplot: pygui(P)

## Calibration
if 'autocalib' in tests: 
    P.autofit(name='default', maxiters=60)
    if doplot: pygui(P.parsets[ind].getresults())

if 'manualcalib' in tests: 
    manualfit(P)

if 'reconcile' in tests:
    P.progsets[ind].reconcile(parset=P.parsets[ind], year=2016)

## Scenarios
if 'runscenarios' in tests:

    defaultbudget = P.progsets[ind].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    testprog = 'ART' # Try zero & infinite budgets for one test program
    pind = 0
    scenlist = [
        Parscen(name='Current conditions', parsetname=ind, pars=[]),
        Budgetscen(name='No budget', parsetname=ind, progsetname=pind, t=[2014], budget=nobudget),
        Budgetscen(name='Current budget', parsetname=ind, progsetname=pind, t=[2015], budget=defaultbudget),
        Coveragescen(name='No '+testprog+' coverage', parsetname=ind, progsetname=pind, t=[2014], coverage={testprog: 0.}),
        Budgetscen(name='Unlimited '+testprog+' budget', parsetname=ind, progsetname=pind, t=[2014], budget={testprog: 1e9}),
        Budgetscen(name='Unlimited spending', parsetname=ind, progsetname=pind, t=[2014], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscens(scenlist)
    P.runscenarios() 
    if doplot: pygui(P.results[ind], toplot='default')



if 'optimize' in tests:
    P.optimize(name='default',maxtime=10, mc=0)
    if doplot: pygui(P.results[ind])
    

if 'dosave' in tests:
    P.save(filename)
    
    

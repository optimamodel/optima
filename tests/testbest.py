"""
Create a good test project -- WARNING, this should be combined with testworkflow,
which is an outdated version of the same thing!

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, loadproj, saveobj, migrate, makespreadsheet # analysis:ignore
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
    P = defaults.defaultproject('best',dorun=False)
    P.runsim(debug=True, start=2000, end=2030)
    if doplot: pygui(P)

## Calibration
if 'autocalib' in tests: 
    P.autofit(name='default', maxiters=60)
    if doplot: pygui(P.parsets[ind].getresults())

if 'manualcalib' in tests: 
    P.manualfit()

if 'reconcile' in tests:
    P.progsets[ind].reconcile(parset=P.parsets[ind], year=2016)


## Scenarios
if 'runscenarios' in tests:
    defaultbudget = P.progsets[ind].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    scenlist = [
        Parscen(name='Current conditions', parsetname=ind, pars=[]),
        Budgetscen(name='No budget', parsetname=ind, progsetname=ind, t=[2016], budget=nobudget),
        Budgetscen(name='No FSW budget', parsetname=ind, progsetname=ind, t=[2016], budget={'FSW programs': 0.}),
        Budgetscen(name='Current budget', parsetname=ind, progsetname=ind, t=[2016], budget=defaultbudget),
        Budgetscen(name='Unlimited spending', parsetname=ind, progsetname=ind, t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscenlist(scenlist)
    P.runscenarios() 
    if doplot:
        plotpeople(P, P.results[ind].raw[ind][0]['people'])
        apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
        pygui(P.results[ind], toplot='default')



if 'optimize' in tests:
    P.optimize(maxtime=20)
    if doplot: pygui(P.results[ind])
    

if 'dosave' in tests:
    P.save(filename)
    
    

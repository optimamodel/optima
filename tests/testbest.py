"""
Create a good test project -- WARNING, this should be combined with testworkflow,
which is an outdated version of the same thing!

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, loadproj, saveobj, migrate, makespreadsheet, __file__ as optimapath # analysis:ignore
from optima import tic, toc, blank, pd # analysis:ignore

# Figure out the path 
parentdir = optimapath.split(os.sep)[:-2] # exclude /optima/__init__.pyc
testdir = parentdir + ['tests'+os.sep]
spreadsheetpath = os.sep.join(testdir)

## Options
tests = [
'standardrun',
#'autocalib',
#'manualcalib',
#'reconcile',
#'runscenarios',
#'optimize',
'dosave',
]

filename = 'best.prj'
ind = -1 # Default index
programdatafile = 'concentratedprogramdata.xlsx'
R.loadspreadsheet(spreadsheetpath+programdatafile)    


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
    P = defaults.defaultproject('best',dorun=False)
    P.runsim(die=True, start=2000, end=2020)
    if runsensitivity: P.sensitivity()
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
    testprog = 'Tracing' # Try zero & infinite budgets for one test program
    scenlist = [
        Budgetscen(name='No budget', parsetname=ind, progsetname=ind, t=[2016], budget=nobudget),
        Budgetscen(name='Current budget', parsetname=ind, progsetname=ind, t=[2016], budget=defaultbudget),
        Budgetscen(name='No '+testprog+' budget', parsetname=ind, progsetname=ind, t=[2016], budget={testprog: 0.}),
        Budgetscen(name='Unlimited '+testprog+' budget', parsetname=ind, progsetname=ind, t=[2016], budget={testprog: 1e9}),
        Budgetscen(name='Unlimited spending', parsetname=ind, progsetname=ind, t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscens(scenlist)
    P.runscenarios() 
    if doplot:
        plotpeople(P, P.results[ind].raw[ind][0]['people'])
        pygui(P.results[ind], toplot='default')



if 'optimize' in tests:
    P.optimize(maxtime=20)
    if doplot: pygui(P.results[ind])
    

if 'dosave' in tests:
    P.save(filename)
    
    

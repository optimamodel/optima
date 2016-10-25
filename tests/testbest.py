"""
Create a good test project -- WARNING, this should be combined with testworkflow,
which is an outdated version of the same thing!

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, loadobj, saveobj, migrate, makespreadsheet # analysis:ignore

## Options
standardrun = 1
migrations = 0 # Whether or not to try migrating an old project
autocalib = 0 # Whether or not to run autofitting
manualcalib = 0
reconcile = 0
runscenarios = 0 # Run scenarios
optimize = 0
dosave = 1
filename = 'best.prj'
ind = -1 # Default index

## Make or load&migrate a project
if standardrun:
    P = defaults.defaultproject('best',dorun=False)
    P.runsim(debug=True)
    pygui(P, toplot=['plhivbycd4'])

if migrations:
    oldprojectfile = '/Users/robynstuart/Google Drive/Optima/Global model/Cost optimization 2.0/Stage 7f optims/Cote dIvoire_0160816_reconciled.prj'
    oldP = loadobj(filename=oldprojectfile)
    P = migrate(oldP)
    P.runsim()
    makespreadsheet('newspreadsheet.xlsx', data=P.data)

## Calibration
if autocalib: 
    P.autofit(name='default', maxiters=60)
    pygui(P.parsets[ind].getresults())

if manualcalib: 
    P.manualfit()

if reconcile:
    P.progsets[ind].reconcile(parset=P.parsets[ind], year=2016)


### Scenarios
if runscenarios:
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
#    plotpeople(P, P.results[ind].raw[ind][0]['people'])
    apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
    pygui(P.results[ind], toplot='default')



if optimize:
    P.optimize(maxtime=20)
    pygui(P.results[ind])
    

if dosave:
    P.save(filename)
    
    

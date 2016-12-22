"""
Create a good test project -- WARNING, this should be combined with testworkflow,
which is an outdated version of the same thing!

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, loadproj, saveobj, migrate, makespreadsheet # analysis:ignore

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
#    from numpy import array, nan
#    P.pars()['proptx'].t[0]= array([0.,2020., 2030.])
#    P.pars()['proptx'].y[0]= array([nan,.9,.95])
#    P.pars()['fixpropdx'].y = 2014.
#    P.pars()['propdx'].t[0]= array([0.,2020., 2030.])
#    P.pars()['propdx'].y[0]= array([nan,.9,.95])
    P.runsim(debug=True)
    P.results[-1].export()

if migrations:
    oldprojectfile = '/Users/robynstuart/Google Drive/Optima/Optima HIV/Applications/!Other Applications/Global model/Cost optimization 2.0/Stage 7f optims/Cote dIvoire_20161201_reconciled.prj'
    P = loadproj(filename=oldprojectfile)
    P.runsim()
    P.makespreadsheet('newspreadsheet.xlsx')

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
    
    

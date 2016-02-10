"""
Create a good test project

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, loadobj, saveobj # analysis:ignore

## Options
autocalib = 0 # Whether or not to run autofitting
manualcalib = 0
runscenarios = 1 # Run scenarios
optimize = 0
dosave = 0
filename = 'best.prj'

P = defaults.defaultproject('best')
#P = loadobj('/u/cliffk/unsw/optima/tests/exercise_scenario.prj')
#P = loadobj('/u/cliffk/unsw/optima/tests/exercise_define_costoutcomefunctions.prj')

## Calibration
if autocalib: 
    P.autofit(name='default', maxiters=60)
    pygui(P.parsets[-1].getresults())

if manualcalib: 
    P.manualfit()


### Scenarios
if runscenarios:
    defaultbudget = P.progsets[-1].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    scenlist = [
        Parscen(name='Current conditions', parsetname=-1, pars=[]),
        Budgetscen(name='No budget', parsetname=-1, progsetname=-1, t=[2016], budget=nobudget),
        Budgetscen(name='Current budget', parsetname=-1, progsetname=-1, t=[2016], budget=defaultbudget),
        Budgetscen(name='Unlimited spending', parsetname=-1, progsetname=-1, t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscenlist(scenlist)
    P.runscenarios() 
#    plotpeople(P, P.results[-1].raw[-1][0]['people'])
    apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
    pygui(P.results[-1], toplot='default')



if optimize:
    P.optimize(maxtime=20)
    pygui(P.results[-1])
    

if dosave:
    saveobj(filename,P)
"""
Create a good test project

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople, saveobj # analysis:ignore

## Options
autocalib = 0 # Whether or not to run autofitting
manualcalib = 0
runscenarios = 1 # Run scenarios
optimize = 0
dosave = 1
filename = 'best.prj'

P = defaults.defaultproject('best')

## Calibration
if autocalib: 
    P.autofit(name='default', maxiters=60)
    pygui(P.parsets[-1].getresults())

if manualcalib: 
    P.manualfit()


### Scenarios
if runscenarios:
    defaultbudget = P.progsets['default'].getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    scenlist = [
        Parscen(name='Current conditions', parsetname='default', pars=[]),
#        Budgetscen(name='No budget', parsetname='default', progsetname='default', t=[2016], budget=nobudget),
        Budgetscen(name='Current budget', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
#        Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
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
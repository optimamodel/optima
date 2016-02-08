"""
Create a good test project

Version: 2016feb08
"""

from optima import defaults, pygui, Budgetscen, dcp, plotpars

## Options
precalibrate = True # Whether or not to run autofitting
P = defaults.defaultproject('concentrated')

## Calibration
if precalibrate: 
    P.parsets[0].pars[0]['force'].y[:] = [ 1.4,  0.9125,  0.9,  0.8,  1.35,  0.625]
    P.runsim()
else: P.autofit(name='default', maxiters=60)


#pygui(P.parsets[-1].getresults())

defaultbudget = P.progsets['default'].getdefaultbudget()
maxbudget = dcp(defaultbudget)
for key in maxbudget: maxbudget[key] += 1e14
scenlist = [
    Budgetscen(name='Current conditions', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
    Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
    ]

# Run the scenarios
P.addscenlist(scenlist)
P.runscenarios() 
 
# Output
apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
pygui(P.results[-1], toplot='default')
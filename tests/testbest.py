"""
Create a good test project

Version: 2016feb08
"""

from optima import defaults, pygui, Parscen, Budgetscen, dcp, plotpars, plotpeople

## Options
precalibrate = True # Whether or not to run autofitting
P = defaults.defaultproject('concentrated')
P.parsets[0].pars[0]['efftxunsupp'].y = 0.92 # WARNING, temporary

## Calibration
if precalibrate: 
    P.parsets[0].pars[0]['force'].y[:] = [ 1.8  ,  1.1  ,  0.875,  0.775,  1.45 ,  0.6  ]
    P.runsim()
else: P.autofit(name='default', maxiters=60)


#pygui(P.parsets[-1].getresults())

defaultbudget = P.progsets['default'].getdefaultbudget()
maxbudget = dcp(defaultbudget)
for key in maxbudget: maxbudget[key] += 1e14
nobudget = dcp(defaultbudget)
for key in nobudget: nobudget[key] *= 1e-6
scenlist = [
    Parscen(name='Current conditions', parsetname='default', pars=[]),
    Budgetscen(name='No budget', parsetname='default', progsetname='default', t=[2016], budget=nobudget),
    Budgetscen(name='Current budget', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
    Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
    ]

# Run the scenarios
P.addscenlist(scenlist)
P.runscenarios() 

#plotpeople(P, P.results[-1].raw[-1][0]['people'])
 
# Output
#apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
pygui(P.results[-1], toplot='default')
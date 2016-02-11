"""
Create a good test project

Version: 2016feb11
"""

import optima as op
infile = 'exercise_optimization.prj'
outfile = 'exercise_optimization.prj'
P = op.loadobj(infile)
#P.progsets[0].reconcile(parset=P.parsets[0], year=2016, maxiters=500)
#op.saveobj(outfile,P)

runoptimize = False
runscenarios = False
ind = 0




if runscenarios:
    defaultbudget = P.progsets[ind].getdefaultbudget()
    maxbudget = op.dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    nobudget = op.dcp(defaultbudget)
    for key in nobudget: nobudget[key] *= 1e-6
    scenlist = [
        op.Parscen(name='Current conditions', parsetname=ind, pars=[]),
        op.Budgetscen(name='No budget', parsetname=ind, progsetname=ind, t=[2016], budget=nobudget),
#        op.Budgetscen(name='Current budget', parsetname=ind, progsetname=ind, t=[2016], budget=defaultbudget),
        op.Budgetscen(name='Unlimited spending', parsetname=ind, progsetname=ind, t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.scens = op.odict()
    P.addscenlist(scenlist)
    P.runscenarios() 
    op.pygui(P.results[-1])


if runoptimize:
    P.optimize(maxtime=40)
    op.pygui(P.results[-1])
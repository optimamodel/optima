"""
TEST_OPTIMA

While optima.py is a demonstration of everything Optima can do, this is used to
test specific features.

Version: 2015jan18 by cliffk
"""


print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example'
verbose = 2
show_wait = False
nsims = 5
timelimit = 10

spaces = 10


print('\n'*spaces)
print('======================================================================')
print('                       TESTING BASIC FUNCTIONS')
print('======================================================================')

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
D.opt.nsims = nsims # Reset options

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)







print('\n'*spaces)
print('======================================================================')
print('                       TESTING MANUAL FITTING')
print('======================================================================')


print('\n\n\n4. Setting up manual fitting...')
from numpy import array, zeros


# Change F
F = D.F[0]
F.force = array(F.force) * 0.5

# Some changes to improve MSM fitting
Plist = [{'name':['const','trans','mmi'], 'data':5e-4}, \
         {'name':['const','trans','mmr'], 'data':1e-3}]

# Artifical change just to demonstrate changing M
tmp = zeros((D.G.npops, len(D.opt.partvec)))
for p in range(D.G.npops): tmp[p,:] = 200+(D.opt.partvec-2000)*50
Mlist = [{'name':['numacts','com'], 'data':tmp}]


print('\n\n\n5. Running manual fitting...')
from manualfit import manualfit
D = manualfit(D, F=F, Plist=Plist, Mlist=Mlist, simstartyear=2000, simendyear=2015, verbose=2)









print('\n'*spaces)
print('======================================================================')
print('                       TESTING AUTOMATIC FITTING')
print('======================================================================')


print('\n\n\n4. Running automatic fitting...')
from autofit import autofit
autofit(D, timelimit=timelimit, simstartyear=2000, simendyear=2015, verbose=verbose)








print('\n'*spaces)
print('======================================================================')
print('                       TESTING SCENARIOS')
print('======================================================================')


print('\n\n\n3. Defining scenarios...')
from bunch import Bunch as struct
scenariolist = [struct() for s in range(3)]

## Current conditions
scenariolist[0].name = 'Current conditions'
scenariolist[0].pars = [] # No changes

## Condom use
scenariolist[1].name = '99% condom use in KAPs'
scenariolist[1].pars = [struct() for s in range(4)]
# MSM regular condom use
scenariolist[1].pars[0].names = ['condom','reg']
scenariolist[1].pars[0].pops = 0
scenariolist[1].pars[0].startyear = 2005
scenariolist[1].pars[0].endyear = 2015
scenariolist[1].pars[0].startval = 0.99
scenariolist[1].pars[0].endval = 0.99
# MSM casual condom use
scenariolist[1].pars[1].names = ['condom','cas']
scenariolist[1].pars[1].pops = 0
scenariolist[1].pars[1].startyear = 2005
scenariolist[1].pars[1].endyear = 2015
scenariolist[1].pars[1].startval = 0.99
scenariolist[1].pars[1].endval = 0.99
# FSW commercial condom use
scenariolist[1].pars[2].names = ['condom','com']
scenariolist[1].pars[2].pops = 1
scenariolist[1].pars[2].startyear = 2005
scenariolist[1].pars[2].endyear = 2015
scenariolist[1].pars[2].startval = 0.99
scenariolist[1].pars[2].endval = 0.99
# Client commercial condom use
scenariolist[1].pars[3].names = ['condom','com']
scenariolist[1].pars[3].pops = 5
scenariolist[1].pars[3].startyear = 2005
scenariolist[1].pars[3].endyear = 2015
scenariolist[1].pars[3].startval = 0.99
scenariolist[1].pars[3].endval = 0.99

## Needle sharing
scenariolist[2].name = 'No needle sharing'
scenariolist[2].pars = [struct()]
scenariolist[2].pars[0].names = ['sharing']
scenariolist[2].pars[0].pops = 7
scenariolist[2].pars[0].startyear = 2002
scenariolist[2].pars[0].endyear = 2015
scenariolist[2].pars[0].startval = 0.0
scenariolist[2].pars[0].endval = 0.0


print('\n\n\n4. Running scenarios...')
from scenarios import runscenarios
D = runscenarios(D, scenariolist=scenariolist, verbose=verbose)











print('\n'*spaces)
print('======================================================================')
print('                       TESTING OPTIMIZATION')
print('======================================================================')




testconstant = False
testmultibudget = False
testtimevarying = False
testmultiyear = False
testconstraints = True


## Set parameters
projectname = 'example'
verbose = 10
ntimepm = 2 # AS: Just use 1 or 2 parameters... using 3 or 4 can cause problems that I'm yet to investigate
maxiters = 1e3
maxtime = 60 # Don't run forever :)

if maxtime:
    from time import time
    starttime = time()
    def stoppingfunc():
        if time()-starttime>maxtime:
            return True
        else:
            return False
else:
    stoppingfunc = None
    


if testconstant:
    print('\n\n\n3. Running constant-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testtimevarying:
    print('\n\n\n4. Running constant-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.timevarying = True
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testmultiyear:
    print('\n\n\n5. Running multi-year-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.funding = 'variable'
    objectives.outcome.variable = [6e6, 5e6, 3e6, 4e6, 3e6, 6e6] # Variable budgets
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testmultibudget:
    print('\n\n\n6. Running multiple-budget optimization...')
    from optimize import optimize, defaultobjectives
    objectives = defaultobjectives(D, verbose=verbose)
    objectives.funding = 'range'
    objectives.outcome.budgetrange.minval = 0
    objectives.outcome.budgetrange.maxval = 1
    objectives.outcome.budgetrange.step = 0.5
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)


if testconstraints:
    print('\n\n\n7. Running constrained constant-budget optimization...')
    from optimize import optimize, defaultobjectives, defaultconstraints
    objectives = defaultobjectives(D, verbose=verbose)
    constraints = defaultconstraints(D, verbose=verbose)
    constraintkeys = ['yeardecrease', 'yearincrease', 'totaldecrease', 'totalincrease']
    for key in constraintkeys:
        for p in range(D.G.nprogs):
            constraints[key][p].use = True # Turn on all constraints
    optimize(D, objectives=objectives, maxiters=maxiters, stoppingfunc=stoppingfunc, verbose=verbose)

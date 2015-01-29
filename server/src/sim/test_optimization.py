"""
TEST_OPTIMIZATION

This function tests that the optimization is working.

Version: 2015jan29 by cliffk
"""

print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example'
verbose = 10
ntimepm = 2 # AS: Just use 1 or 2 parameters... using 3 or 4 can cause problems that I'm yet to investigate
timelimit = 50

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
D.opt.nsims = 1 # Reset the number of simulations

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose, savetofile=False)

print('\n\n\n3. Running optimization...')
from optimize import optimize, defaultobjectives
objectives = defaultobjectives(D, verbose=verbose)
optimize(D, objectives=objectives, timelimit=timelimit, verbose=verbose)

print('\n\n\n4. Viewing optimization...')
from viewresults import viewmultiresults#, viewallocpies
viewmultiresults(D.plot.optim[0].multi)
#viewallocpies(D.plot.optim['Default'])

print('\n\n\nDONE.')

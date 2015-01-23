"""
TEST_OPTIMIZATION

This function tests that the optimization is working.

Version: 2015jan23 by cliffk
"""

print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example'
verbose = 2
timelimit = 30

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n4. Running optimization...')
from optimize import optimize
optimize(D, timelimit=timelimit, objectives={"year":{"start":2000,"end":2030}}, verbose=10)

print('\n\n\n5. Viewing optimization...')
from viewresults import viewmultiresults, viewallocpies
viewmultiresults(D.plot.OM)
viewallocpies(D.plot.OA)

print('\n\n\nDONE.')
"""
TEST_OPTIMIZATION

This function tests that the optimization is working.

Version: 2014nov27 by cliffk
"""


print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example'
verbose = 4

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n\n4. Running optimization...')
from scenarios import runscenarios
D = runscenarios(D, scenariolist=None, verbose=2)

print('\n\n\n5. Viewing optimization...')
from viewresults import viewmodels
viewmodels(D.plot.scens)

print('\n\n\nDONE.')
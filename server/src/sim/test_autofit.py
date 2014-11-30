"""
TEST_AUTOFIT

This function tests that automatic fitting is working.

Version: 2014nov30 by cliffk
"""


print('WELCOME TO OPTIMA')

## Set parameters
projectname = 'example'
verbose = 4
timelimit = 10 #otherwise it's too long for the build server

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n\n4. Viewing scenarios...')
whichgraphs = {'prev':[1,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}
from viewresults import viewepiresults
viewepiresults(D.plot.E, whichgraphs=whichgraphs, startyear=2000, endyear=2015, onefig=True, verbose=verbose)

print('\n\n\n5. Running automatic fitting...')
from autofit import autofit
autofit(D, timelimit=timelimit, startyear=2000, endyear=2010, verbose=verbose)

print('\n\n\n6. Viewing scenarios...')
viewepiresults(D.plot.E, whichgraphs=whichgraphs, startyear=2000, endyear=2015, onefig=True, verbose=verbose)

print('\n\n\nDONE.')
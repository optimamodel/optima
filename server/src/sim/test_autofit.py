"""
TEST_AUTOFIT

This function tests that automatic fitting is working.

Version: 2014dec01 by cliffk
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

print('\n\n\n3. Viewing results...')
whichgraphs = {'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}
from viewresults import viewuncerresults
viewuncerresults(D.plot.E, whichgraphs=whichgraphs, simstartyear=2000, simendyear=2015, onefig=True, verbose=verbose)

print('\n\n\n4. Running automatic fitting...')
from autofit import autofit
autofit(D, timelimit=timelimit, simstartyear=2000, simendyear=2015, verbose=verbose)

print('\n\n\n5. Viewing scenarios...')
viewuncerresults(D.plot.E, whichgraphs=whichgraphs, simstartyear=2000, simendyear=2015, onefig=True, verbose=verbose)

print('\n\n\nDONE.')

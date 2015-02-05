"""
TEST_SCENARIOS

This function tests that the scenarios are working.

Version: 2014dec02 by cliffk
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

print('\n\n\n3. Defining scenarios...')
from bunch import Bunch as struct
scenariolist = [struct() for s in range(4)]

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

## Needle sharing
scenariolist[3].name = 'ART'
scenariolist[3].pars = [struct()]
scenariolist[3].pars[0].names = ['txtotal']
scenariolist[3].pars[0].pops = 7
scenariolist[3].pars[0].startyear = 2002
scenariolist[3].pars[0].endyear = 2015
scenariolist[3].pars[0].startval = 0.2
scenariolist[3].pars[0].endval = 0.8


print('\n\n\n4. Running scenarios...')
from scenarios import runscenarios
D = runscenarios(D, scenariolist=scenariolist, verbose=verbose)

print('\n\n\n5. Viewing scenarios...')
from viewresults import viewmultiresults
viewmultiresults(D.plot.scens)

print('\n\n\nDONE.')

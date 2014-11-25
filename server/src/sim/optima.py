"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file
2. updatedata -- load the data into a structure
3. runsimulation -- run the simulation
4. epiresults -- calculate the results
5. viewresults -- display the results

Version: 2014nov23 by cliffk
"""

print('WELCOME TO OPTIMA')

import argparse
parser = argparse.ArgumentParser(description = "OPTIMA global procedure")
parser.add_argument("-p", "--projectname", type=str, default="example", help = "source project name")
parser.add_argument("-v", "--verbose",     type=int, default=4, help="increase output verbosity")
parser.add_argument("-w", "--wait", help="wait for user input after showing graphs", action="store_true")
args = parser.parse_args()

## Set parameters
projectname = args.projectname #'example'
verbose     = args.verbose #4
show_wait   = args.wait

print('\n\n1. Making project...')
from makeproject import makeproject, default_pops, default_progs
D = makeproject(projectname='example', pops=default_pops, progs = default_progs, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n2. Uploading spreadsheet...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n4. Making plot data...')
from gatherplotdata import gatherplotdata
D = gatherplotdata(D, verbose=verbose)

print('\n\n5. Viewing results...')
from viewresults import viewresults
viewresults(D.O, whichgraphs={'prev':[1,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}, onefig=True, verbose=verbose, show_wait=show_wait)

print('\n\nDONE.')


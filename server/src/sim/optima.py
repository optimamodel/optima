"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file
2. updatedata -- load the data into a structure
3. runsimulation -- run the simulation
4. gatherplotdata -- gather the data for the plots
5. viewresults -- display the results
6. autofit -- automatically calibrate
7. viewresults -- display the updated results
# 8. scenarios -- run some scenarios
# 9. viewscenarios -- view the results of the scenarios
10. optimize -- run an optimization
11. viewoptimization -- view an optimization

Version: 2014nov24 by cliffk
"""


print('WELCOME TO OPTIMA')

import argparse
parser = argparse.ArgumentParser(description = "OPTIMA global procedure")
parser.add_argument("-p", "--projectname", type=str, default="example", help = "source project name")
parser.add_argument("-v", "--verbose", type=int, default=4, help="increase output verbosity")
parser.add_argument("-w","--wait", help="wait for user input after showing graphs", action="store_true")
args = parser.parse_args()

## Set parameters
projectname = args.projectname #'example'
verbose = args.verbose #4
show_wait = args.wait

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname='example', pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Uploading spreadsheet...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n\n4. Making plot data...')
from gatherplotdata import gatherepidata
D.E = gatherepidata(D, verbose=verbose)

print('\n\n\n5. Viewing results...')
from viewresults import viewresults
viewresults(D.E, whichgraphs={'prev':[1,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}, startyear=2000, endyear=2015, onefig=True, verbose=verbose, show_wait=show_wait)

print('\n\n\n6. Automatic calibration...')
from autofit import autofit
D = autofit(D, timelimit=5, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n\n7. Viewing results again...')
viewresults(D.E)

print('\n\n\n8. Running scenarios...')
print('TBA')

print('\n\n\n9. Viewing scenarios...')
print('TBA')

print('\n\n\n10. Running optimization...')
from optimize import optimize
D = optimize(D, objectives=None, constraints=None, timelimit=5, verbose=2)

print('\n\n\n11. Viewing optimization...')
from optimize import viewoptimization
viewoptimization(D.O.optim)

print('\n\n\nDONE.')
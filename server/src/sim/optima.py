"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file
2. updatedata -- load the data into a structure
3. runsimulation -- run the simulation
4. viewresults -- display the results
5. autofit -- automatically calibrate
6. viewresults -- display the updated results
# 7. scenarios -- run some scenarios
# 8. viewscenarios -- view the results of the scenarios
9. optimize -- run an optimization
11. viewoptimization -- view an optimization

Version: 2014nov26 by cliffk
"""

print('WELCOME TO OPTIMA')

import argparse
parser = argparse.ArgumentParser(description = "OPTIMA global procedure")
parser.add_argument("-p", "--projectname", type=str, default="example", help = "source project name")
parser.add_argument("-v", "--verbose", type=int, default=4, help="increase output verbosity")
parser.add_argument("-w", "--wait", help="wait for user input after showing graphs", action="store_true")
parser.add_argument("-t", "--timelimit", type=int, default=3, help="time limit")
args = parser.parse_args()

## Set parameters
projectname = args.projectname #'example'
verbose = args.verbose # 4
show_wait = args.wait # True
timelimit = args.timelimit # 3 seconds

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname='example', pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n5. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

#print('\n\n\n6. Viewing results...')
#from viewresults import viewuncerresults
#viewuncerresults(D.plot.E, whichgraphs={'prev':[1,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}, startyear=2000, endyear=2015, onefig=True, verbose=verbose, show_wait=show_wait)
#
#print('\n\n\n7. Automatic calibration...')
#from autofit import autofit
#D = autofit(D, timelimit=timelimit, startyear=2000, endyear=2015, verbose=verbose)
#
#print('\n\n\n8. Viewing results again...')
#viewuncerresults(D.plot.E)
#
#print('\n\n\n9. Running scenarios...')
#from scenarios import runscenarios
#D = runscenarios(D, scenariolist=None, verbose=2)
#
#print('\n\n\n10. Viewing scenarios...')
#from viewresults import viewmultiresults
#viewmultiresults(D.plot.scens)

print('\n\n\n11. Running optimization...')
from optimize import optimize
D = optimize(D, objectives=None, constraints=None, endyear=2020, timelimit=timelimit, verbose=2)

#print('\n\n\n12. Viewing optimization...')
#from viewresults import viewallocpies
#viewallocpies(D.plot.OA)
#viewmultiresults(D.plot.OM)

print('\n\n\nDONE.')
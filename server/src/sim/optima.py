"""
OPTIMA

This function does everything. The basic procedure is as follows:

1. makeproject -- initialize the project file

1. loadspreadsheet -- load the data into a structure
2. data2pars -- convert the data into model parameters
3. setupmodel -- reconcile partnerships and calculate parameters to go into the model
4. model -- actually run the model

Version: 2014nov05 by cliffk
"""
print('WELCOME TO OPTIMA')
import shutil
import os
import argparse

parser = argparse.ArgumentParser(description = "OPTIMA global procedure")
parser.add_argument("-p", "--projectname", type=str, default="example", help = "source project name")
parser.add_argument("-v", "--verbose", type=int, default=4,
                    help="increase output verbosity")
parser.add_argument("-w","--wait", help="wait for user input after showing graphs", action="store_true")
args = parser.parse_args()

## Set parameters
projectname = args.projectname #'example'
verbose = args.verbose #4
show_wait = args.wait


print('\n\n\n1. Making project...')
from makeproject import makeproject, default_pops, default_progs
if os.path.exists(projectname+'.xlsx'):
  shutil.copy(projectname+'.xlsx', projectname+'_data.xlsx')
D = makeproject(projectname='example', pops=default_pops, progs = default_progs, datastart=2000, dataend=2015, verbose=verbose)

print('\n\n\n2. Uploading spreadsheet...')
from updatedata import updatedata
if os.path.exists(projectname+'_data.xlsx'):
  shutil.copy(projectname+'_data.xlsx', projectname+'.xlsx')
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Running simulation...')
from runsimulation import runsimulation
D = runsimulation(D, startyear=2000, endyear=2015, verbose=verbose)

print('\n\n\n4. Making results...')
from epiresults import epiresults
D = epiresults(D, verbose=verbose)

print('\n\n\n4. Viewing results...')
from viewresults import viewresults
viewresults(D, whichgraphs={'prev':1, 'inci':1, 'daly':1, 'death':1, 'pops':1, 'tot':1}, onefig=True, verbose=verbose, show_wait=show_wait)

print('\n\n\nDONE.')
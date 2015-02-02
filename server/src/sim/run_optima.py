"""
RuN_OPTIMA

While optima.py is a demonstration of everything Optima can do, this is used to
test specific features.

Version: 2015feb01 by cliffk
"""


print('WELCOME TO RUN_OPTIMA')

## Set parameters
projectname = 'example'
verbose = 4
show_wait = False
nsims = 5

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
D.opt.nsims = nsims # Reset options

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Viewing results...')
from viewresults import viewuncerresults
viewuncerresults(D.plot.E, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costcum':[1,1]}, simstartyear=2000, simendyear=2015, onefig=True, verbose=verbose, show_wait=show_wait)

print('\n\n\nDONE.')
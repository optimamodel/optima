"""
RUN_OPTIMA

Basic run.

Version: 2015feb01 by cliffk
"""


print('WELCOME TO RUN_OPTIMA')

from time import time
starttime = time()

## Set parameters
projectname = 'example'
verbose = 4
show_wait = False
nsims = 5

print('\n\n\n1. Making project...')
from makeproject import makeproject
D = makeproject(projectname=projectname, pops=['']*6, progs = ['']*7, datastart=2000, dataend=2015, verbose=verbose)
D['opt']['nsims'] = nsims # Reset options

print('\n\n\n2. Updating data...')
from updatedata import updatedata
D = updatedata(D, verbose=verbose)

print('\n\n\n3. Viewing results...')
from viewresults import viewuncerresults
viewuncerresults(D['plot']['E'])

print('\n\n\nDONE; elapsed: %f s' % (time()-starttime))
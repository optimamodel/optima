"""
Loads an old project version.

Version: 2017jan13
"""

import optima as op
from optima import tic, toc, blank, pd # analysis:ignore

## Options
tests = [
'basicmigration',
]

oldprojectname = 'concentrated_v2.0.4.prj' # Options are concentrated_v2.0.4.prj and concentrated_v2.1.prj

## Housekeeping

if 'doplot' not in locals(): doplot = True

def done(t=0):
    print('Done.')
    toc(t)
    blank()

blank()
print('Running tests:')
for i,test in enumerate(tests): print(('%i.  '+test) % (i+1))
blank()



##############################################################################
## The tests
##############################################################################

T = tic()

if 'basicmigration' in tests:
    
    # Figure out the path 
    import os
    optimapath = os.path.dirname(op.__file__)
    spreadsheetpath = os.path.join(optimapath, '..', 'tests', '') # Empty last part puts a /

    oldprojectfile = spreadsheetpath+oldprojectname
    P = op.loadproj(filename=oldprojectfile)
    P.runsim()
    if doplot: op.pygui(P)

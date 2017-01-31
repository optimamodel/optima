"""
Loads an old project version.

Version: 2017jan13
"""

import optima as op
from optima import tic, toc, blank, pd # analysis:ignore

## Options
tests = [
'migrations',
]

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

if 'migrations' in tests:
    
    # Figure out the path 
    import os
    optimapath = os.path.dirname(op.__file__)
    spreadsheetpath = os.path.join(optimapath, '..', 'tests', '') # Empty last part puts a /

    oldprojectfile = spreadsheetpath+'concentrated_v2.1.prj'
    P = op.loadproj(filename=oldprojectfile)
    P.runsim()
    if doplot: op.pygui(P)


    

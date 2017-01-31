"""
Loads an old project version.

Version: 2017jan13
"""

import optima as op
from optima import tic, toc, blank, pd # analysis:ignore

## Options
tests = [
'basicmigration',
'scenario',
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

if 'basicmigration' or 'scenario' in tests:
    
    # Figure out the path 
    import os
    optimapath = os.path.dirname(op.__file__)
    spreadsheetpath = os.path.join(optimapath, '..', 'tests', '') # Empty last part puts a /

    oldprojectfile = spreadsheetpath+'concentrated_v2.1.prj'
    P = op.loadproj(filename=oldprojectfile)
    P.runsim()
    if doplot: op.pygui(P)


    
## Set up project etc.
if 'scenario' in tests:
    t = tic()

    print('Running migration-scenario test...')
    from optima import Budgetscen, dcp
    
    ## Define scenarios
    defaultbudget = P.progset().getdefaultbudget()
    maxbudget = dcp(defaultbudget)
    for key in maxbudget: maxbudget[key] += 1e14
    scenlist = [
        Budgetscen(name='Current conditions', parsetname='default', progsetname='default', t=[2016], budget=defaultbudget),
        Budgetscen(name='Unlimited spending', parsetname='default', progsetname='default', t=[2016], budget=maxbudget),
        ]
    
    # Run the scenarios
    P.addscenlist(scenlist)
    P.runscenarios() 
     
    if doplot:
        from optima import pygui, plotpars
        pygui(P.results[-1], toplot='default')
#        apd = plotpars([scen.scenparset.pars[0] for scen in P.scens.values()])
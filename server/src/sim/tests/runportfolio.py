"""
RUNPORTFOLIO

Procedure to run this file:
1. Go to ui.optimamodel.com and download the .json files to investigate.
2. Place them in the regions folder. This should be a subfolder of the one that stores this script!
3. Press F5 to run (or from the Run menu, select Run).
4. Choose a name for your portfolio and then follow the ensuing instructions.
5. Load as many regions as you want.
5. ...
6. Profit?

For developers:
- Each loaded region has its own individually populated data structure D.
- Any typical processes you wish to apply to individual Ds should be coded as a method of Region class (regionclass.py).
- However, ALL processes should be initiated at the Portfolio class level (portfolioclass.py) and propagate down.
  'Portfolio' should ideally be hooked up as the interface for the front-end.
  For example, want to apply 'optimize' to the nth loaded region within the portfolio?
  Code something like 'def optimize(self,n,parameters)', which should in turn call 'self.regionlist[n-1].optimise(parameters)'.
- Likewise, any processes to apply across multiple Ds should be coded while iterating through a subset of Portfolio's regionlist.
  This includes the geo-prioritisation algorithm but can be extended.

Version: 2015may29
"""

print('WELCOME TO OPTIMA')

# Check that the Optima directory is even linked via system path.
def findoptima():
    """ Find the directory that Optima exists in. """
    from os.path import exists
    optimadirs = [ # List all common directories here.
        '/u/cliffk/unsw/optima/server/src/sim',
        '/Users/robynstuart/Documents/Optima2/server/src/sim',
        'C:/Users/Ireporter/Documents/GitHub/Optima/server/src/sim',
        'D:/Work Projects/Optima/Optima/server/src/sim',
        '/Users/romesha/Desktop/Work/Optima/Optima/server/src/sim'
    ]
    for optimadir in optimadirs:
        if exists(optimadir):
            return optimadir
    raise Exception('Unfortunately the Optima directory cannot be found! Please add its path to the optimadirs list.')

import sys; 
sys.path.append(findoptima())
sys.path.append(findoptima() + '/classes')

from portfolio import Portfolio

portfolioname = raw_input('Please enter a name for your portfolio: ')

currentportfolio = Portfolio(portfolioname)
currentportfolio.run()


#from optimize import optimize, defaultobjectives, defaultconstraints
#from viewresults import viewmultiresults, viewoptimresults
#from utils import *


#origfile = 'regions\Sudan Mar 24.json'
#newfile = 'regions\Sudan Mar 24-temp.json'
#
### Set parameters
#verbose = 10
#ntimepm = 1 # AS: Just use 1 or 2 parameters... using 3 or 4 can cause problems that I'm yet to investigate
#maxiters = 1e3
#maxtime = 100 # Don't run forever :)
#doconstrain = True
#
#from dataio import loaddata, savedata
#D = loaddata(origfile)
#D['opt']['dt'] = 0.2
#D['opt']['parendyear'] = 2030
#D['opt']['simendyear'] = 2030
#
##import versioning
##D = versioning.run_migrations(D)
#
#
### Set default objectives
##objectives = defaultobjectives(D)
##constraints = defaultconstraints(D)
##objectives['outcome']['inci'] = True # "Minimize cumulative incidence"
##objectives['outcome']['death'] = True # "Minimize cumulative AIDS-related deaths"
##
##### Optimization 1
##objectives['outcome']['fixed'] = sum(D['data']['origalloc']) # "With a fixed amount of ['money'] available"
##optimize(D, name='Test optimization May 27', objectives=objectives, constraints=constraints, maxiters=maxiters, timelimit=maxtime, verbose=verbose)
##viewmultiresults(D['plot']['optim'][-1]['multi'])
##viewoptimresults(D['plot']['optim'][-1])
#
#
#
#savedata(newfile, D)


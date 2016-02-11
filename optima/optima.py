# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.] [preferred]
or
import optima as op
or
from optima import *

The __init__.py file imports all functions and classes defined in this file..

Since other functions import optima.py and optima.py imports other functions, 
weird race conditions can happen. Thus, it's designed to silently fail once
it gets up to the latest module that it can successfully import. To make it
fail loudly, do a find-and-replace for "pass #" with blank to re-enable the
print statements.

I'm sorry this file is so ugly. Believe me, it hurts me more than it hurts you.



Now, the legal part:

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Version: 2016jan30 by cliffk
"""

optimalicense = '''
Optima HIV -- HIV optimization and analysis tool
Copyright (C) 2016 by the Optima Consortium
'''
print(optimalicense)




## Specify the version, for the purposes of figuring out which version was used to create a project
__version__ = 2.0



## Housekeeping -- discard errors by default, but enable them if __failsilently is defined (in builtins) and is True
__delbuiltin = False
__delsys = False
if '__builtin__' not in locals().keys(): 
    import __builtin__
    __delbuiltin = True
if 'sys' not in locals().keys(): 
    import sys
    __delsys = True
if '__failsilently' not in __builtin__.__dict__.keys(): __failsilently = True
def __failed(doraise=True):
    ''' Tiny function to optionally allow printing of failed imports (may be useful for debugging) '''
    if not __failsilently: 
        print('Warning: Optima import failed: %s' % sys.exc_info()[1])
        if doraise: raise sys.exc_info()[1], None, sys.exc_info()[2]


__notoptima = locals().keys()


## Load general modules
try: from uuid import uuid4 as uuid
except: __failed()

try: from datetime import datetime; today = datetime.today
except: __failed()

try: from copy import deepcopy as dcp
except: __failed()



## Load non-Optima-specific custom functions
try: 
    import asd as _asd
    from asd import asd
except: __failed()

try: 
    import pchip as _pchip
    from pchip import pchip, plotpchip
except: __failed()

try: 
    import colortools # Load high-level module as well
    from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except: __failed()

try: 
    import utils # Load high-level module as well
    from utils import blank, checkmem, dataindex, defaultrepr, findinds, getdate, gitinfo, isnumber, loadobj, loads, objectid, objatt, objmeth, objrepr, odict, OptimaException, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, scaleratio, setdate, sigfig, smoothinterp, tic, toc, vec2obj # odict class
except: __failed()


## Load Optima functions and classes
try: 
    import settings as _settings # Inter-project definitions, e.g. health states
    from settings import Settings, convertlimits, gettvecdt
except: __failed()

try: 
    import makespreadsheet as _makespreadsheet
    from makespreadsheet import makespreadsheet, makeeconspreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except: __failed()

try: 
    import loadspreadsheet as _loadspreadsheet
    from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except: __failed()

try: 
    import results as _results
    from results import Result, Resultset, Multiresultset, BOC, getresults  # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except: __failed()

try: 
    import parameters as _parameters # Load high-level module as well
    from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, loadpartable, applylimits # Parameter and Parameterset classes
except: __failed()

try: 
    import model as _model
    from model import model, runmodel # The thing that actually runs the model
except: __failed()

try: 
    import programs as _programs # High-level module
    from programs import Program, Programset # Define programs
except: __failed()

try: 
    import economics as _economics
    from economics import loadeconomics, loadeconomicsspreadsheet, makeecontimeseries, getartcosts # Misc economic modules
except: __failed()

try: 
    import calibration as _calibration
    from calibration import sensitivity, autofit # Calibration functions
except: __failed()

try: 
    import scenarios as _scenarios # Load high-level module as well -- WARNING, somewhat like to be overwritten by user
    from scenarios import Parscen, Budgetscen, Coveragescen, Progscen, runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except: __failed()

try: 
    import optimization as _optimization
    from optimization import Optim, defaultobjectives, defaultconstraints, optimize # Scenario functions
except: __failed()

try: 
    import plotting as _plotting # Load high-level module as well
    from plotting import getplotselections, makeplots # Create the plots
except: __failed()


## Want to add more modules to Optima? Do that here (unless they're non-essential plotting functions)



## Load optional plotting functions -- instead of failing, just redefine as an error message so still "available"

try: import gui # All Python GUI functions
except:
    gui = None # If fails, try individual functions as well
    __failed(doraise=False)

try: from gui import plotresults
except:
    def plotresults(*args, **kwargs): print('Note: plotresults() could not be imported, but everything else should work')
    __failed(doraise=False)

try: from gui import pygui # Handle the Python plotting
except:
    def pygui(*args, **kwargs): print('Note: pygui() could not be imported, but everything else should work')
    __failed(doraise=False)

try: from gui import browser # Handle the browser-based plotting
except:
    def browser(*args, **kwargs): print('Note: browser() could not be imported, but everything else should work')
    __failed(doraise=False)

try: from gui import manualfit # Do manual fitting
except:
    def manualfit(*args, **kwargs): print('Note: manualfit() could not be imported, but everything else should work')
    __failed(doraise=False)

try: from gui import plotpeople # Plot all people
except:
    def plotpeople(*args, **kwargs): print('Note: plotpeople() could not be imported, but everything else should work')
    __failed(doraise=False)

try: from gui import plotpars # Plot all people
except:
    def plotpars(*args, **kwargs): print('Note: plotpars() could not be imported, but everything else should work')
    __failed(doraise=False)



## Import the Project class that ties everything together
try: 
    import project as _project
    from project import Project # Project class
except: __failed()

try: 
    import portfolio as _portfolio
    from portfolio import Portfolio # Portfolio class (container of Projects)
except: __failed()

try: 
    import geospatial as _geospatial
    from geospatial import geogui # Import GUI tools for geospatial analysis
except:
    def geogui(*args, **kwargs): print('Note: geogui() could not be imported, but everything else should work')
    __failed(doraise=False)
    

# Finally, load defaults
try: import defaults
except: __failed()



## Tidy up -- delete things we created for housekeeping purposes that we no lnger need
del __failed # This must exist, delete it
if '__failsilently' in __builtin__.__dict__.keys(): del __builtin__.__failsilently # This may or may not exist here
else: del __failsilently
if __delbuiltin: del __builtin__
if __delsys: del sys
del __delbuiltin
del __delsys


# Turn everything into a list to be imported
__all__ = list(set(locals().keys()) - set(__notoptima))
__all__.remove('__notoptima'); del __notoptima
__all__.append('__version__')
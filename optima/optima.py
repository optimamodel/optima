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

Version: 2016jan15 by cliffk
"""

## Specify the version, for the purposes of figuring out which version was used to create a project
__version__ = 2.0 


## Housekeeping
_E = None
if '_printfailed' not in __builtins__(): _printfailed = True # This should be True -- since most of the modules below import from this file, the imports after the module in question are expected to fail
else: _printfailed = __builtins__._printfailed
def _failed(_E, msg):
    ''' Tiny function to optionally allow printing of failed imports (may be useful for debugging) '''
    if _printfailed: print('Optima failed to import "%s": "%s"' % (msg, _E))


## Load general modules
try: from uuid import uuid4 as uuid
except Exception, _E: _failed(_E, 'uuid')

try: from datetime import datetime; today = datetime.today
except Exception, _E: _failed(_E, 'datetime')

try: from copy import deepcopy as dcp
except Exception, _E: _failed(_E, 'copy')



## Load non-Optima-specific custom functions
try: from asd import asd
except Exception, _E: _failed(_E, 'asd')

try: from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except Exception, _E: _failed(_E, 'colortools')

try: from utils import blank, checkmem, dataindex, findinds, getdate, gitinfo, loadobj, loads, objectid, objatt, objmeth, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, setdate, sigfig, smoothinterp, tic, toc # odict class
except Exception, _E: _failed(_E, 'utils')


## Load Optima functions and classes
try: from settings import Settings # Inter-project definitions, e.g. health states
except Exception, _E: _failed(_E, 'settings')

try: from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except Exception, _E: _failed(_E, 'makespreadsheet')

try: from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except Exception, _E: _failed(_E, 'loadspreadsheet')

try: from results import getresults, Result, Resultset  # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except Exception, _E: _failed(_E, 'results')

try: from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, readpars # Parameter and Parameterset classes
except Exception, _E: _failed(_E, 'parameters')

try: from model import model, runmodel # The thing that actually runs the model
except Exception, _E: _failed(_E, 'model')

try: from programs import Program, Programset # Define programs
except Exception, _E: _failed(_E, 'programs')

try: from makeplots import epiplot # Create the plots
except Exception, _E: _failed(_E, 'makeplots')

try: from calibration import sensitivity, autofit # Calibration functions
except Exception, _E: _failed(_E, 'calibration')

try: from scenarios import runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except Exception, _E: _failed(_E, 'scenarios')



## Load optional plotting functions -- instead of failing, just redefine as an error message so still "available"
try: from gui import plotresults
except: 
    def plotresults(**kwargs): print('plotresults could not be imported')
    _failed('plotresults')

try: from gui import pygui # Handle the Python plotting
except: 
    def pygui(**kwargs): print('pygui could not be imported')
    _failed('pygui')

try: from gui import browser # Handle the browser-based plotting
except: 
    def browser(**kwargs): print('browser could not be imported')
    _failed('browser')

try: from manualgui import manualfit # Do manual fitting
except: 
    def manualfit(**kwargs): print('manualfit could not be imported')
    _failed('manualfit')



## Import the Project class that ties everything together
try: from project import Project # Project class
except Exception, _E: _failed(_E, 'project')



## Finally, load certain high-level modules -- those that have multiple sub-modules and no name conflicts
#try: 
#    import defaultprograms, plotpeople # Additional features not included in the main part of Optima
#    import colortools, utils, results, parameters, programs, makeplots, calibration, scenarios, gui, project
#except Exception, _E: _failed(_E, 'high-level modules')

## Tidy up
del _failed, _printfailed, _E
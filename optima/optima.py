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

Version: 2016jan18 by cliffk
"""

## Specify the version, for the purposes of figuring out which version was used to create a project
__version__ = 2.0 




## Housekeeping -- discard errors by default, but enable them if _failsilently is defined (in builtins) and is True
delbuiltin = False
delsys = False
if '__builtin__' not in locals().keys(): 
    import __builtin__
    delbuiltin = True
if 'sys' not in locals().keys(): 
    import sys
    delsys = True
if '_failsilently' not in __builtin__.__dict__.keys(): _failsilently = True
def _failed(doraise=True):
    ''' Tiny function to optionally allow printing of failed imports (may be useful for debugging) '''
    if not _failsilently: 
        print('Warning: Optima import failed: %s' % sys.exc_info()[1])
        if doraise: raise sys.exc_info()[1], None, sys.exc_info()[2]


## Load general modules
try: from uuid import uuid4 as uuid
except: _failed()

try: from datetime import datetime; today = datetime.today
except: _failed()

try: from copy import deepcopy as dcp
except: _failed()



## Load non-Optima-specific custom functions
try: from asd import asd
except: _failed()

try: from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except: _failed()

try: from utils import blank, checkmem, dataindex, findinds, getdate, gitinfo, loadobj, loads, objectid, objatt, objmeth, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, setdate, sigfig, smoothinterp, tic, toc # odict class
except: _failed()


## Load Optima functions and classes
try: from settings import Settings # Inter-project definitions, e.g. health states
except: _failed()

try: from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except: _failed()

try: from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except: _failed()

try: from results import Result, Resultset, getresults  # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except: _failed()

try: from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, readpars # Parameter and Parameterset classes
except: _failed()

try: from model import model, runmodel # The thing that actually runs the model
except: _failed()

try: from programs import Program, Programset # Define programs
except: _failed()

try: from makeplots import epiplot # Create the plots
except: _failed()

try: from calibration import sensitivity, autofit # Calibration functions
except: _failed()

try: from scenarios import runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except: _failed()

try: from optimization import minoutcomes, defaultobjectives # Scenario functions
except: _failed()


## Want to add more modules to Optima? Do that here (unless they're non-essential plotting functions)



## Load optional plotting functions -- instead of failing, just redefine as an error message so still "available"
try: from gui import plotresults
except:
    def plotresults(**kwargs): print('Note: plotresults() could not be imported, but everything else should work')
    _failed(doraise=False)

try: from gui import pygui # Handle the Python plotting
except:
    def pygui(**kwargs): print('Note: pygui() could not be imported, but everything else should work')
    _failed(doraise=False)

try: from gui import browser # Handle the browser-based plotting
except:
    def browser(**kwargs): print('Note: browser() could not be imported, but everything else should work')
    _failed(doraise=False)

try: from manualgui import manualfit # Do manual fitting
except:
    def manualfit(**kwargs): print('Note: manualfit() could not be imported, but everything else should work')
    _failed(doraise=False)



## Import the Project class that ties everything together
try: from project import Project # Project class
except: _failed()



# Finally, load certain high-level modules -- those that have multiple sub-modules and no name conflicts
try: 
    import defaultprograms, plotpeople # Additional features not included in the main part of Optima
    import colortools, utils, results, parameters, programs, makeplots, calibration, scenarios, optimization, gui, project
except: _failed()




## Tidy up -- delete things we created for housekeeping purposes that we no lnger need
del _failed # This must exist, delete it
if '_failsilently' in __builtin__.__dict__.keys(): del __builtin__._failsilently # This may or may not exist here
else: del _failsilently
if delbuiltin: del __builtin__
if delsys: del sys
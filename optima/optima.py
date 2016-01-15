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

## Housekeeping
_silent = False # WARNING: I think this should be True -- since most of the modules below import from this file, shouldn't the imports fail after the module in question?
def _failed(msg):
    ''' Tiny function to optionally allow printing of failed imports (may be useful for debugging) '''
    if not _silent: print('Optima failed to import "%s"' % msg)


## Load general modules
try: from uuid import uuid4 as uuid
except: _failed('uuid')

try: from datetime import datetime; today = datetime.today
except: _failed('datetime')

try: from copy import deepcopy as dcp
except: _failed('copy')



## Load non-Optima-specific custom functions
try: from asd import asd
except: _failed('asd')

try: from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except: _failed('colortools')

try: from utils import blank, checkmem, dataindex, findinds, getdate, gitinfo, loadobj, loads, objectid, objatt, objmeth, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, setdate, sigfig, smoothinterp, tic, toc # odict class
except: _failed('utils')


## Load Optima functions and classes
try: from settings import Settings # Inter-project definitions, e.g. health states
except: _failed('settings')

try: from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except: _failed('makespreadsheet')

try: from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except: _failed('loadspreadsheet')

try: from results import Result, Resultset, getresults # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except: _failed('results')

try: from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars, partable, readpars # Parameter and Parameterset classes
except: _failed('parameters')

try: from model import model, runmodel # The thing that actually runs the model
except: _failed('model')

try: from programs import Program, Programset # Define programs
except: _failed('programs')

try: from makeplots import epiplot # Create the plots
except: _failed('makeplots')

try: from calibration import sensitivity, autofit # Calibration functions
except: _failed('calibration')

try: from scenarios import runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except: _failed('scenarios')



## Load optional plotting functions
try: from gui import plotresults
except: _failed('gui')

try: from gui import pygui # Handle the Python plotting
except: _failed('pygui')

try: from gui import browser # Handle the browser-based plotting
except: _failed('browser')

try: from manualgui import manualfit # Do manual fitting
except: _failed('manualfit')



## Import the Project class that ties everything together
try: from project import Project, version # Project class
except: _failed('project')



## Finally, load certain high-level modules -- those that have multiple sub-modules and no name conflicts
try: 
    import defaultprograms, plotpeople # Additional features not included in the main part of Optima
    import colortools, utils, results, parameters, programs, makeplots, calibration, scenarios, gui, project
except: _failed('high-level modules')
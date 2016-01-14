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

Version: 2016jan14 by cliffk
"""

## Load general modules
try: from uuid import uuid4 as uuid
except: pass # print('Failed at uuid')
try: from datetime import datetime; today = datetime.today
except: pass # print('Failed at datetime')
try: from copy import deepcopy as dcp
except: pass # print('Failed at copy')

## Load non-Optima-specific custom functions
try: from asd import asd
except: pass # print('Failed at asd')
try: from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except: pass # print('Failed at colortools')
try: from utils import blank, checkmem, dataindex, findinds, getdate, loadobj, loads, objectid, objatt, objmeth, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, saveobj, saves, setdate, sigfig, smoothinterp, tic, toc # odict class
except: pass # print('Failed at utils')

## Load Optima functions and classes
try: from settings import Settings # Inter-project definitions, e.g. health states
except: pass # print('Failed at settings')
try: from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except: pass # print('Failed at makespreadsheet')
try: from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except: pass # print('Failed at loadspreadsheet')
try: from results import Result, Resultset, getresults # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except: pass # print('Failed at results')
try: from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars # Parameter and Parameterset classes
except: pass # print('Failed at parameters')
try: from model import model, runmodel # The thing that actually runs the model
except: pass # print('Failed at model')
try: from programs import Program, Programset # Define programs
except: pass # print('Failed at programs')
try: from makeplots import epiplot # Create the plots
except: pass # print('Failed at makeplots')
try: from calibration import sensitivity, autofit # Calibration functions
except: pass # print('Failed at calibration')
try: from scenarios import runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except: pass # print('Failed at scenarios')

## Load optional plotting functions
try: from gui import plotresults
except: pass # print('Failed at gui')
try: from gui import pygui # Handle the Python plotting
except: pass # print('Failed at pygui')
try: from gui import browser # Handle the browser-based plotting
except: pass # print('Failed at browser')
try: from manualgui import manualfit # Do manual fitting
except: pass # print('Failed at manualfit')

## Import the Project class that ties everything together
try: from project import Project, version # Project class
except: pass # print('Failed at project')

## Finally, load certain high-level modules -- those that have multiple sub-modules and no name conflicts
try: import colortools, utils, results, parameters, programs, makeplots, calibration, scenarios, gui, project
except: pass # print('Failed at high-level modules')
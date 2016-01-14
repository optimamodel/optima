# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.] [preferred]
or
import optima as op
or
from optima import *

The __init__.py file imports all functions and classes defined in this file..

Version: 2016jan14 by cliffk
"""

## Load general modules
try: from uuid import uuid4 as uuid
except: pass
try: from datetime import datetime; today = datetime.today
except: pass
try: from copy import deepcopy as dcp
except: pass

## Load non-Optima-specific custom functions
try: from asd import asd
except: pass
try: from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
except: pass
try: from utils import blank, checkmem, dataindex, findinds, getdate, load, loads, objectid, objatt, objmeth, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, save, saves, setdate, sigfig, smoothinterp, tic, toc # odict class
except: pass

## Load Optima functions and classes
try: from settings import Settings # Inter-project definitions, e.g. health states
except: pass
try: from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
except: pass
try: from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
except: pass
try: from results import Result, Resultset, getresults # Result and Results classes -- odd that it comes before parameters, but parameters need getresults()
except: pass
try: from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars # Parameter and Parameterset classes
except: pass
try: from model import model, runmodel # The thing that actually runs the model
except: pass
try: from programs import Program, Programset # Define programs
except: pass
try: from makeplots import epiplot # Create the plots
except: pass
try: from calibration import sensitivity, autofit # Calibration functions
except: pass
try: from scenarios import runscenarios, makescenarios, defaultscenarios, getparvalues # Scenario functions
except: pass

## Load optional plotting functions
try: from gui import plotresults
except: pass
try: from gui import pygui # Handle the Python plotting
except: pass
try: from gui import browser # Handle the browser-based plotting
except: pass
try: from manualgui import manualfit # Do manual fitting
except: pass

## Import the Project class that ties everything together
try: from project import Project, version # Project class
except: pass

## Finally, load high-level modules
try: import asd, colortools, utils, settings, makespreadsheet, loadspreadsheet, results, parameters, model, programs, makeplots, calibration, scenarios, gui, manualgui, project
except: pass
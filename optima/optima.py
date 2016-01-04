# -*- coding: utf-8 -*-
"""
This file performs all necessary imports, so Optima can be used either as

from optima import Project, Parameters [etc.] [preferred]
or
import optima as op
or
from optima import *

The __init__.py file imports all functions and classes defined in this file..

Version: 2016jan04 by cliffk
"""

## Load general modules
from uuid import uuid4 as uuid
from datetime import datetime; today = datetime.today
from copy import deepcopy as dcp

## Load non-Optima-specific custom functions
from ballsd import ballsd
from colortools import alpinecolormap, bicolormap, gridcolormap, vectocolor
from utils import blank, checkmem, dataindex, findinds, getdate, load, loads, objectid, odict, pd, perturb, printarr, printdata, printv, quantile, runcommand, sanitize, save, saves, setdate, sigfig, smoothinterp, tic, toc # odict class

## Load Optima functions and classes
from settings import Settings # Inter-project definitions, e.g. health states
from makespreadsheet import makespreadsheet, default_datastart, default_dataend # For making a blank spreadsheet
from loadspreadsheet import loadspreadsheet # For loading a filled out spreadsheet
from parameters import Par, Timepar, Popsizepar, Constant, Parameterset, makepars, makesimpars # Parameter and Parameterset classes
from results import Result, Resultset # Result and Results classes
from model import model # The thing that actually runs the model
from programs import Program, Programset # Define programs
from makeplots import epiplot # Create the plots
from calibration import sensitivity, autofit # Calibration functions

## Load optional plotting functions
try: from gui import pygui # Handle the Python plotting
except: pygui = 'Import failed'
try: from gui import browser # Handle the browser-based plotting
except: browser = 'Import failed'
try: from manualgui import manualfit # Do manual fitting
except: manualfit = 'Import failed'

## Finally, import the Project class that ties everything together
from project import Project, version # Project class
